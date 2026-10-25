#!/usr/bin/env python3
"""Offline tests for the paired rule test, the placeholder-book exclusion,
and rule-tagged forecast records.

PROTECTED CORE - the trading agent must not edit files under core/.

core/score.py grades each estimation rule by the paired Brier difference of
its raw and rule estimates, clustered by event; core/forecast.py records a
rule's value in shadow until that verdict passes. These tests pin the
maths on a hand-computed example and drive `forecast.py record` with a
stubbed market, so nothing touches the network. CI runs it on every push.

Usage: python3 core/test_rules.py
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
import forecast  # noqa: E402
import score  # noqa: E402


# Seeded rows are recorded "now", so the 14-day idle cutoff never ages them.
NOW = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def row(raw, rule, status, category="rally", end="2026-10-20", **over):
    r = {"id": "x", "ts": NOW, "market_id": "1",
         "outcome": "Yes", "category": category, "end_date": end + "T00:00:00Z",
         "est_prob": raw, "raw_prob": raw, "rule_prob": rule, "rule": "r1",
         "market_prob_at_record": 0.5, "best_bid_at_record": 0.49,
         "best_ask_at_record": 0.51, "liquidity_at_record": 500.0,
         "skip_reason": "no-edge", "status": status}
    r.update(over)
    return r


class PairedTest(unittest.TestCase):
    def test_fixed_example(self):
        # Event A (two rows) nets 0.07 - 0.07 = 0; B is -0.28; C is +0.05;
        # seven one-row events are -0.13 each. n = 11, 10 events,
        # mean = -1.14 / 11 = -0.10364. Event residuals s - mean * k are
        # 0.20727, -0.17636, 0.15364 and 7 x -0.02636 (squares sum 0.10254),
        # so se = sqrt(10/9 * 0.10254) / 11 = 0.030685, and the 99.5%
        # interval is -0.10364 +/- 3.6580 * 0.030685.
        rows = [row(0.7, 0.6, "won", end="2026-10-01"),
                row(0.4, 0.3, "lost", end="2026-10-01"),
                row(0.8, 0.6, "lost", end="2026-10-02"),
                row(0.2, 0.3, "lost", end="2026-10-03")]
        rows += [row(0.7, 0.6, "lost", end=f"2026-10-{d:02d}") for d in range(4, 11)]
        self.assertEqual(score.paired_rule_test(rows),
                         {"n": 11, "events": 10, "mean_delta": -0.1036,
                          "ci": [-0.2159, 0.0086], "verdict": "shadow"})
        # under 10 events the t approximation reads narrow: no interval shown
        self.assertNotIn("ci", score.paired_rule_test(rows[:4]))

    def test_t_crit_matches_table_where_verdicts_start(self):
        self.assertAlmostEqual(score._t_crit(19), 3.174, places=2)

    def test_noisy_rule_at_the_bar_stays_shadow(self):
        # 20 events whose interval straddles zero: the sign of the mean alone
        # must not pass or retire the rule.
        for raw, rule in ((0.7, 0.6), (0.6, 0.7)):
            rows = [row(raw, rule, "lost" if d % 2 else "won", end=f"2026-10-{d:02d}")
                    for d in range(1, 21)]
            v = score.paired_rule_test(rows)
            self.assertLess(v["ci"][0], 0)
            self.assertGreater(v["ci"][1], 0)
            self.assertEqual(v["verdict"], "shadow")

    def test_verdict_needs_min_events(self):
        helps = [row(0.7, 0.6, "lost", end=f"2026-10-{d:02d}") for d in range(1, 21)]
        self.assertEqual(score.paired_rule_test(helps[:19])["verdict"], "shadow")
        self.assertEqual(score.paired_rule_test(helps)["verdict"], "pass")
        hurts = [row(0.6, 0.7, "lost", end=f"2026-10-{d:02d}") for d in range(1, 21)]
        self.assertEqual(score.paired_rule_test(hurts)["verdict"], "fail")

    def test_events_are_category_and_end_date(self):
        same_event = [row(0.7, 0.6, "lost") for _ in range(25)]
        v = score.paired_rule_test(same_event)
        self.assertEqual((v["events"], v["verdict"]), (1, "shadow"))
        two = [row(0.7, 0.6, "lost"), row(0.7, 0.6, "lost", category="sports")]
        self.assertEqual(score.paired_rule_test(two)["events"], 2)

    def test_verdicts_grade_settled_and_superseded_rows(self):
        rows = [row(0.7, 0.6, "lost", end=f"2026-10-{d:02d}",
                    superseded_by="y" if d % 2 else None) for d in range(1, 21)]
        rows += [row(0.7, 0.6, "open", end="2026-10-25") for _ in range(30)]
        v = score.rule_verdicts(rows)["r1"]
        self.assertEqual((v["n"], v["open"], v["verdict"]), (20, 30, "pass"))


class Placeholder(unittest.TestCase):
    def test_placeholder_rows_leave_the_headline(self):
        real = row(0.6, 0.6, "won")
        rows = [real,
                row(0.97, 0.97, "won", best_bid_at_record=0.005,
                    best_ask_at_record=0.999, liquidity_at_record=17.0),
                row(0.9, 0.9, "won", best_ask_at_record=None),
                row(0.9, 0.9, "won", liquidity_at_record=20.0),
                row(0.9, 0.9, "won", best_bid_at_record=0.05,
                    best_ask_at_record=0.95, liquidity_at_record=None)]
        self.assertEqual([score.placeholder_book(r) for r in rows],
                         [False, True, True, True, True])
        revised = row(0.9, 0.9, "won", best_ask_at_record=None, superseded_by="y")
        rep = score.forecast_report([dict(r, rule=None) for r in rows + [revised]])
        self.assertEqual(rep["overall"], score.fstats([real]))
        self.assertEqual(rep["placeholder"]["n"], 4)
        self.assertEqual(rep["revised_away"]["settled"], 0)


GAMMA = {"question": "Will it happen?", "slug": "q", "endDate": "2026-10-30T00:00:00Z",
         "outcomes": json.dumps(["Yes", "No"]), "clobTokenIds": json.dumps(["111", "222"]),
         "version": "v1", "liquidityNum": "900", "volume24hr": "100"}


BOOK = {"bid": 0.49, "ask": 0.51, "min_order_size": 5.0}
LAST_TRADE_PRICE = forecast.pmapi.last_trade_price


class Record(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp.name) / "forecasts.jsonl"
        for p in (mock.patch.object(forecast, "FORECASTS", self.path),
                  mock.patch.object(forecast.pmapi, "gamma_market", lambda _id: GAMMA),
                  mock.patch.object(forecast.pmapi, "book_quote", lambda _t: BOOK),
                  mock.patch.object(forecast.pmapi, "last_trade_price", lambda _t: 0.55)):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def record(self, market_id, est, rule=None, raw=None, *extra):
        argv = ["forecast.py", "record", "--market-id", market_id, "--outcome", "Yes",
                "--est-prob", str(est), "--category", "rally", "--skip-reason", "no-edge",
                *extra]
        if rule:
            argv += ["--rule", rule]
        if raw is not None:
            argv += ["--raw-prob", str(raw)]
        out = io.StringIO()
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out):
            forecast.main()
        return json.loads(out.getvalue())

    def rows(self):
        return [json.loads(line) for line in self.path.read_text().splitlines()]

    def seed(self, rule, raw, value, n=20, **over):
        settled = [dict(row(raw, value, "lost", end=f"2026-10-{d:02d}"), rule=rule,
                        market_id=f"s{rule}{d}", **over)
                   for d in range(1, n + 1)]
        with self.path.open("a") as f:
            f.writelines(json.dumps(r) + "\n" for r in settled)

    def test_plain_record_is_unchanged(self):
        out = self.record("1", 0.62)
        self.assertEqual(out["est_prob"], 0.62)
        self.assertNotIn("rule", self.rows()[0])

    def test_wide_spread_benchmarks_last_trade(self):
        # docs.polymarket.com/concepts/prices-orderbook: "If the spread is
        # wider than $0.10, the last traded price is shown instead."
        wide = dict(BOOK, bid=0.30, ask=0.60)
        with mock.patch.object(forecast.pmapi, "book_quote", lambda _t: wide):
            out = self.record("1", 0.62)
        self.assertEqual((out["market_price"], out["price_source"]), (0.55, "last_trade"))
        self.assertEqual(self.rows()[0]["market_prob_at_record"], 0.55)
        out = self.record("2", 0.62)  # a tight book shows its mid
        self.assertEqual((out["market_price"], out["price_source"]), (0.5, "mid"))

    def test_never_traded_placeholder_is_not_a_trade(self):
        # docs.polymarket.com/market-data/prices-order-books: "When a token has
        # never traded and its order book is empty, the API returns the "0.5"
        # placeholder and an empty side string"
        wide = dict(BOOK, bid=0.30, ask=0.60)
        with mock.patch.object(forecast.pmapi, "book_quote", lambda _t: wide), \
                mock.patch.object(forecast.pmapi, "last_trade_price", LAST_TRADE_PRICE), \
                mock.patch.object(forecast.pmapi, "get_json",
                                  lambda *_a, **_k: {"price": "0.5", "side": ""}):
            out = self.record("1", 0.62)
        self.assertEqual((out["market_price"], out["price_source"]), (0.45, "book"))

    def test_shadow_rule_records_raw(self):
        out = self.record("1", 0.55, rule="half-gap", raw=0.62)
        r = self.rows()[0]
        self.assertEqual((r["est_prob"], r["raw_prob"], r["rule_prob"], r["rule_state"]),
                         (0.62, 0.62, 0.55, "shadow"))
        self.assertEqual(out["rule"]["state"], "shadow")
        self.assertIn("half-gap", score.forecast_report(self.rows())["rules"])

    def test_shadow_rule_with_history_still_records_raw(self):
        self.seed("half-gap", 0.7, 0.6, n=5)
        out = self.record("1", 0.55, rule="half-gap", raw=0.62)
        self.assertEqual((out["est_prob"], out["rule"]["state"]), (0.62, "shadow"))

    def test_gates_use_recorded_and_both_values(self):
        # Supersede: the recorded raw moves 0.02, the rule value 0.10 - not material.
        self.record("1", 0.55, rule="half-gap", raw=0.62)
        with self.assertRaises(SystemExit) as cm:
            self.record("1", 0.45, "half-gap", 0.64, "--supersede")
        self.assertIn("material change", str(cm.exception.code))
        # Extreme disagreement (mid 0.50): on the recorded raw, then on the rule value.
        for est, raw, name in ((0.80, 0.95, "raw-prob 0.95"), (0.95, 0.80, "est-prob 0.95")):
            with self.subTest(name=name), self.assertRaises(SystemExit) as cm:
                self.record("2", est, "half-gap", raw)
            self.assertIn(name, str(cm.exception.code))

    def test_text_report_prints_rule_line(self):
        # score.main() prints text only with settled bets, so it reads the
        # real journal/ledger.jsonl next to this temporary forecast file.
        self.seed("half-gap", 0.7, 0.6, n=3)
        out = io.StringIO()
        with mock.patch.object(score, "FORECASTS", self.path), \
                mock.patch.object(sys, "argv", ["score.py", "--skip-mtm"]), \
                contextlib.redirect_stdout(out):
            score.main()
        self.assertIn("rule half-gap: SHADOW settled=3 events=3 open=0", out.getvalue())

    def test_passed_rule_binds(self):
        self.seed("half-gap", 0.7, 0.6)
        out = self.record("1", 0.55, rule="half-gap", raw=0.62)
        self.assertEqual((out["est_prob"], out["rule"]["state"]), (0.55, "bound"))

    def test_refusals(self):
        self.seed("bad-rule", 0.6, 0.7)
        for rule, raw in (("half-gap", None), (None, 0.62), ("bad-rule", 0.62),
                          ("Half Gap", 0.62), ("half-gap", 0.55)):
            with self.subTest(rule=rule, raw=raw), self.assertRaises(SystemExit) as cm, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.record("1", 0.55, rule=rule, raw=raw)
            self.assertIn("REJECTED", str(cm.exception.code))

    def test_budget(self):
        # An idle rule and a retired rule hold no slot ...
        self.seed("old-rule", 0.7, 0.6, n=1, ts="2026-01-01T00:00:00Z")
        self.seed("bad-rule", 0.6, 0.7)
        for i in range(forecast.RULE_BUDGET):
            self.record(str(10 + i), 0.55, rule=f"rule-{i}", raw=0.62)
        # ... a rule in play may keep recording ...
        self.record("20", 0.55, rule="rule-0", raw=0.62)
        # ... and a full budget refuses both a new rule and an idle one coming back.
        for rule in ("rule-new", "old-rule"):
            with self.subTest(rule=rule), self.assertRaises(SystemExit) as cm:
                self.record("21", 0.55, rule=rule, raw=0.62)
            self.assertIn("budget full", str(cm.exception.code))


if __name__ == "__main__":
    unittest.main()
