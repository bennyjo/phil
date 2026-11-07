#!/usr/bin/env python3
"""Offline tests for paper fills (core/ledger.py) and void settlement
(core/resolve.py) against Polymarket's documented rules.

PROTECTED CORE - the trading agent must not edit files under core/.

Each test pins one rule to the docs.polymarket.com quote it follows. They
drive `ledger.py place` and resolve.settle_against_market with hand-built
Gamma records and books, so nothing touches the network. CI runs it on
every push.

Usage: python3 core/test_fills.py
"""
import contextlib
import datetime as dt
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ledger  # noqa: E402
import resolve  # noqa: E402

GAMMA = {"question": "Will it happen?", "slug": "q", "endDate": "2026-10-30T00:00:00Z",
         "outcomes": json.dumps(["Yes", "No"]), "clobTokenIds": json.dumps(["111", "222"]),
         "version": "v1", "feesEnabled": True,
         "feeSchedule": {"rate": 0.05, "exponent": 1, "takerOnly": True, "rebateRate": 0.15}}
BOOK = {"bid": 0.39, "ask": 0.40, "asks": [(0.40, 1000.0)], "min_order_size": 5.0}
FREE = dict(GAMMA, feesEnabled=False)


def book(*asks):
    return dict(BOOK, ask=asks[0][0], asks=list(asks))
V2 = json.loads((pathlib.Path(__file__).resolve().parent / "fixtures"
                 / "polymarket_v2.json").read_text())["gamma"]


class Place(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = pathlib.Path(self.tmp.name) / "ledger.jsonl"
        self.skips = pathlib.Path(self.tmp.name) / "v2-bet-skips.jsonl"
        for p in (mock.patch.object(ledger, "LEDGER", self.path),
                  mock.patch.object(ledger, "V2_BET_SKIPS", self.skips)):
            p.start()
            self.addCleanup(p.stop)

    def place(self, stake, book=BOOK, market=GAMMA, market_id="1"):
        argv = ["ledger.py", "place", "--market-id", market_id, "--outcome", "Yes",
                "--est-prob", "0.6", "--stake", str(stake), "--category", "test",
                "--edge-class", "other", "--rationale", "test"]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(ledger.pmapi, "gamma_market", lambda _id: market), \
                mock.patch.object(ledger.pmapi, "book_quote", lambda _t: book), \
                contextlib.redirect_stdout(io.StringIO()):
            ledger.main()
        return json.loads(self.path.read_text().splitlines()[-1])

    def test_taker_fee_comes_out_of_the_stake(self):
        # docs.polymarket.com/trading/fees: "fee = C x feeRate x p x (1 - p)";
        # its Sports table charges $1.20 on 100 shares at $0.40, so $0.012 a share.
        row = self.place(5)
        self.assertEqual(row["shares"], round(5 / 0.412, 4))
        self.assertAlmostEqual(row["fee_usd"], row["shares"] * 0.012, places=4)
        self.assertEqual(self.place(5, market=FREE, market_id="2")["shares"], 12.5)

    def test_top_level_that_covers_the_stake_fills_at_the_top_ask(self):
        row = self.place(5, book=book((0.40, 12.5), (0.70, 100.0)), market=FREE)
        self.assertEqual((row["entry_price"], row["shares"], row["edge"]), (0.40, 12.5, 0.2))

    def test_stake_past_the_top_level_walks_to_the_next(self):
        # A taker order takes each level in turn: $2 buys 5 shares at $0.40,
        # the other $3 buys 6 at $0.50. The edge is on the average price, and
        # the market's price stays the top ask.
        row = self.place(5, book=book((0.40, 5.0), (0.50, 100.0)), market=FREE)
        self.assertEqual((row["shares"], row["fee_usd"]), (11.0, 0.0))
        self.assertEqual(row["entry_price"], round(5 / 11, 6))
        self.assertEqual(row["edge"], round(0.6 - 5 / 11, 4))
        self.assertEqual(row["market_prob_at_entry"], 0.40)

    def test_stake_that_exactly_empties_the_book_fills(self):
        # $0.70 + $0.20 + $0.10: the remainder is float dust, not an unfilled stake.
        row = self.place(1, book=book((0.1, 7.0), (0.2, 1.0), (0.5, 0.2)), market=FREE)
        self.assertEqual(row["shares"], 8.2)

    def test_each_level_pays_the_fee_at_its_own_price(self):
        # docs.polymarket.com/trading/fees: "fee = C x feeRate x p x (1 - p)".
        # 5 shares at $0.40 cost $0.412 each ($2.06); $2.94 is left at $0.5125.
        row = self.place(5, book=book((0.40, 5.0), (0.50, 100.0)))
        shares = 5 + 2.94 / 0.5125
        self.assertEqual(row["shares"], round(shares, 4))
        self.assertAlmostEqual(row["fee_usd"], 5 * 0.012 + (shares - 5) * 0.0125, places=5)
        self.assertEqual(row["entry_price"], round((5 - row["fee_usd"]) / shares, 6))

    def test_book_that_cannot_fill_the_stake_is_rejected(self):
        # 2.73 shares at $0.88 hold $2.40, recorded on a live V2 book, 2026-11-07.
        with self.assertRaises(SystemExit) as cm:
            self.place(5, book=book((0.88, 2.73)), market=FREE)
        self.assertIn("fill only $2.40 of the $5 stake", str(cm.exception.code))
        self.assertFalse(self.path.exists())

    def test_walk_stops_at_the_protected_price_bound(self):
        # The level past max_entry_price (0.95) could fill the stake, but no
        # fill may print there.
        with self.assertRaises(SystemExit) as cm:
            self.place(5, book=book((0.90, 2.0), (0.97, 1000.0)), market=FREE)
        self.assertIn("fill only $1.80", str(cm.exception.code))
        self.assertFalse(self.path.exists())

    def test_book_quote_orders_ask_levels_cheapest_first(self):
        # The CLOB does not list the best ask first.
        raw = {"bids": [{"price": "0.38", "size": "9"}, {"price": "0.39", "size": "7"}],
               "asks": [{"price": "0.50", "size": "100"}, {"price": "0.40", "size": "5"}],
               "min_order_size": "5"}
        with mock.patch.object(ledger.pmapi, "clob_book", lambda _t: raw):
            q = ledger.pmapi.book_quote("111")
        self.assertEqual(q, {"bid": 0.39, "ask": 0.40, "asks": [(0.40, 5.0), (0.50, 100.0)],
                             "min_order_size": 5.0})

    def test_binary_v2_bet_fills_on_its_position_id(self):
        v2 = dict(V2["binary_open"], outcomes=json.dumps(["Yes", "No"]))
        row = self.place(5, market=v2, market_id="7")
        self.assertEqual(row["token_id"], v2["positionIds"][0])
        # feeSchedule rate 0.05 at $0.40, as for V1.
        self.assertEqual(row["shares"], round(5 / 0.412, 4))
        self.assertFalse(self.skips.exists())

    def test_neg_risk_v2_bet_is_refused_logged_and_counted(self):
        # Read-only: Phil forecasts neg-risk V2 markets but does not bet them.
        v2 = dict(V2["neg_risk_open"], outcomes=json.dumps(["Yes", "No"]))
        with self.assertRaises(SystemExit) as cm:
            self.place(5, market=v2, market_id="7")
        self.assertIn("REJECTED", str(cm.exception.code))
        self.assertIn("read-only", str(cm.exception.code))
        self.assertFalse(self.path.exists())
        skip = json.loads(self.skips.read_text())
        self.assertEqual((skip["market_id"], skip["outcome"], skip["version"]), ("7", "Yes", "v2"))
        self.assertIn("read-only", skip["reason"])
        self.assertEqual(self.status()["v2_bets_skipped"], 1)

    def test_v2_bet_without_a_binary_position_id_is_refused(self):
        v2 = dict(GAMMA, version="v2", positionIds=["9", "8"])
        with self.assertRaises(SystemExit) as cm:
            self.place(5, market=v2, market_id="7")
        self.assertIn("read-only", str(cm.exception.code))
        self.assertFalse(self.path.exists())

    def test_v1_bet_logs_no_v2_skip(self):
        row = self.place(5)
        self.assertEqual(row["token_id"], "111")
        self.assertFalse(self.skips.exists())
        self.assertEqual(self.status()["v2_bets_skipped"], 0)

    def status(self):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["ledger.py", "status"]), \
                contextlib.redirect_stdout(out):
            ledger.main()
        return json.loads(out.getvalue())

    def test_fees_without_a_rate_are_rejected(self):
        # A market with feesEnabled must carry its fee parameters
        # (docs.polymarket.com/market-data/market-details#trading-fees); a fill
        # never assumes a zero fee.
        with self.assertRaises(SystemExit) as cm:
            self.place(5, market=dict(GAMMA, feeSchedule=None))
        self.assertIn("cannot price the taker fee", str(cm.exception.code))
        self.assertFalse(self.path.exists())

    def test_order_below_min_order_size_is_rejected(self):
        # docs.polymarket.com/market-data/market-details: "Orders smaller than
        # the minimum order size are rejected." $1.80 at $0.40 is about 4.4 shares.
        with self.assertRaises(SystemExit) as cm:
            self.place(1.8)
        self.assertIn("min_order_size", str(cm.exception.code))
        self.assertFalse(self.path.exists())


class V2Settlement(unittest.TestCase):
    def test_resolved_v2_market_settles_a_paper_bet(self):
        # Recorded: a closed V2 market's prices are "1" and "0".
        market = V2["binary_closed"]
        won, lost = json.loads(market["outcomes"])
        now = dt.datetime(2026, 11, 3, tzinfo=dt.timezone.utc)
        for outcome, status in ((won, "won"), (lost, "lost")):
            e = {"status": "open", "outcome": outcome, "end_date": market["endDate"],
                 "stake_usd": 5.0, "shares": 12.5}
            self.assertTrue(resolve.settle_against_market(e, market, now))
            self.assertEqual(e["status"], status)


class Void(unittest.TestCase):
    NOW = dt.datetime(2026, 10, 5, tzinfo=dt.timezone.utc)

    def settle(self, prices):
        e = {"status": "open", "outcome": "Yes", "end_date": "2026-10-01T00:00:00Z",
             "stake_usd": 5.0, "shares": 12.5}
        m = {"closed": True, "outcomes": json.dumps(["Yes", "No"]), "outcomePrices": prices}
        return resolve.settle_against_market(e, m, self.NOW), e

    def test_void_bet_redeems_half_a_dollar_a_share(self):
        # docs.polymarket.com/concepts/resolution: "Market resolves 50/50 -
        # each token redeems for $0.50"
        settled, e = self.settle(json.dumps(["0.5", "0.5"]))
        self.assertTrue(settled)
        self.assertEqual((e["status"], e["pnl_usd"]), ("void", 1.25))
        start = ledger.PROTECTED["sim_bankroll_usd"]
        self.assertEqual(ledger.bankroll([e]), start + 1.25)

    def test_void_without_resolution_prices_returns_the_stake(self):
        for prices in (None, json.dumps([])):
            with self.subTest(prices=prices):
                settled, e = self.settle(prices)
                self.assertTrue(settled)
                self.assertEqual((e["status"], e["pnl_usd"]), ("void", 0.0))

    def test_undecided_prices_stay_open(self):
        settled, e = self.settle(json.dumps(["0.6", "0.4"]))
        self.assertFalse(settled)
        self.assertEqual(e["status"], "open")


if __name__ == "__main__":
    unittest.main()
