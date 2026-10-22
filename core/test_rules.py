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


def row(raw, rule, status, category="rally", end="2026-10-20", **over):
    r = {"id": "x", "ts": "2026-10-20T00:00:00Z", "market_id": "1",
         "outcome": "Yes", "category": category, "end_date": end + "T00:00:00Z",
         "est_prob": raw, "raw_prob": raw, "rule_prob": rule, "rule": "r1",
         "market_prob_at_record": 0.5, "best_bid_at_record": 0.49,
         "best_ask_at_record": 0.51, "liquidity_at_record": 500.0,
         "skip_reason": "no-edge", "status": status}
    r.update(over)
    return r


class PairedTest(unittest.TestCase):
    def test_fixed_example(self):
        # Event A (two rows) nets 0.07 - 0.07 = 0; B is -0.28; C is +0.05.
        # mean = -0.23 / 4 = -0.0575; event residuals s - mean * k are
        # 0.115, -0.2225, 0.1075, so se = sqrt(3/2 * 0.0742875) / 4 = 0.08345
        # and the interval is -0.0575 +/- 3.8519 * 0.08345.
        rows = [row(0.7, 0.6, "won", end="2026-10-01"),
                row(0.4, 0.3, "lost", end="2026-10-01"),
                row(0.8, 0.6, "lost", end="2026-10-02"),
                row(0.2, 0.3, "lost", end="2026-10-03")]
        self.assertEqual(score.paired_rule_test(rows),
                         {"n": 4, "events": 3, "mean_delta": -0.0575,
                          "ci95": [-0.379, 0.264], "verdict": "shadow"})

    def test_t95_matches_table_where_verdicts_start(self):
        self.assertAlmostEqual(score._t95(19), 2.093, places=3)

    def test_verdict_needs_min_events(self):
        helps = [row(0.7, 0.6, "lost", end=f"2026-10-{d:02d}") for d in range(1, 21)]
        self.assertEqual(score.paired_rule_test(helps[:19])["verdict"], "shadow")
        self.assertEqual(score.paired_rule_test(helps)["verdict"], "pass")
        hurts = [row(0.6, 0.7, "lost", end=f"2026-10-{d:02d}") for d in range(1, 21)]
        self.assertEqual(score.paired_rule_test(hurts)["verdict"], "fail")

    def test_one_event_counts_once(self):
        same_event = [row(0.7, 0.6, "lost") for _ in range(25)]
        v = score.paired_rule_test(same_event)
        self.assertEqual((v["events"], v["verdict"]), (1, "shadow"))


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
        rep = score.forecast_report([dict(r, rule=None) for r in rows])
        self.assertEqual(rep["overall"], score.fstats([real]))
        self.assertEqual(rep["placeholder"]["n"], 4)


GAMMA = {"question": "Will it happen?", "slug": "q", "endDate": "2026-10-30T00:00:00Z",
         "outcomes": json.dumps(["Yes", "No"]), "clobTokenIds": json.dumps(["111", "222"]),
         "version": "v1", "liquidityNum": "900", "volume24hr": "100"}


class Record(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp.name) / "forecasts.jsonl"
        for p in (mock.patch.object(forecast, "FORECASTS", self.path),
                  mock.patch.object(forecast.pmapi, "gamma_market", lambda _id: GAMMA),
                  mock.patch.object(forecast.pmapi, "best_prices", lambda _t: (0.49, 0.51))):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def record(self, market_id, est, rule=None, raw=None):
        argv = ["forecast.py", "record", "--market-id", market_id, "--outcome", "Yes",
                "--est-prob", str(est), "--category", "rally", "--skip-reason", "no-edge"]
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

    def seed(self, rule, raw, value, n=20):
        settled = [dict(row(raw, value, "lost", end=f"2026-10-{d:02d}"), rule=rule,
                        market_id=f"s{rule}{d}")
                   for d in range(1, n + 1)]
        with self.path.open("a") as f:
            f.writelines(json.dumps(r) + "\n" for r in settled)

    def test_plain_record_is_unchanged(self):
        out = self.record("1", 0.62)
        self.assertEqual(out["est_prob"], 0.62)
        self.assertNotIn("rule", self.rows()[0])

    def test_shadow_rule_records_raw(self):
        out = self.record("1", 0.55, rule="half-gap", raw=0.62)
        r = self.rows()[0]
        self.assertEqual((r["est_prob"], r["raw_prob"], r["rule_prob"], r["rule_state"]),
                         (0.62, 0.62, 0.55, "shadow"))
        self.assertEqual(out["rule"]["state"], "shadow")
        self.assertIn("half-gap", score.forecast_report(self.rows())["rules"])

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

    def test_budget_refuses_a_new_rule_when_full(self):
        for i in range(forecast.RULE_BUDGET):
            self.record(str(10 + i), 0.55, rule=f"rule-{i}", raw=0.62)
        self.record("20", 0.55, rule="rule-0", raw=0.62)
        with self.assertRaises(SystemExit) as cm:
            self.record("21", 0.55, rule="rule-new", raw=0.62)
        self.assertIn("budget full", str(cm.exception.code))


if __name__ == "__main__":
    unittest.main()
