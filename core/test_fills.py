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
BOOK = {"bid": 0.39, "ask": 0.40, "min_order_size": 5.0}


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
        free = dict(GAMMA, feesEnabled=False)
        self.assertEqual(self.place(5, market=free, market_id="2")["shares"], 12.5)

    def test_v2_bet_is_refused_logged_and_counted(self):
        # Read-only V2: Phil forecasts V2 markets but does not bet them.
        v2 = dict(GAMMA, version="v2", positionIds=["9", "8"])
        with self.assertRaises(SystemExit) as cm:
            self.place(5, market=v2, market_id="7")
        self.assertIn("REJECTED", str(cm.exception.code))
        self.assertIn("read-only", str(cm.exception.code))
        self.assertFalse(self.path.exists())
        skip = json.loads(self.skips.read_text())
        self.assertEqual((skip["market_id"], skip["outcome"], skip["version"]), ("7", "Yes", "v2"))
        self.assertIn("read-only", skip["reason"])
        self.assertEqual(self.status()["v2_bets_skipped"], 1)

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
