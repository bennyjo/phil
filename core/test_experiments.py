#!/usr/bin/env python3
"""Tests for core/experiments.py (offline, temporary git repos).

PROTECTED CORE - the trading agent must not edit files under core/.

Covers propose (the computed baseline), grade (COLLECTING, KEEP, DOUBLE DOWN,
ROLL BACK, INCONCLUSIVE, BLOCKED; n and days windows; the as-of cutoff;
secondary-metric clauses), status, the check_ledger rules core/validate.py
enforces, and core/score.py --since.

Usage: python3 core/test_experiments.py [-v]
"""
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import experiments as E  # noqa: E402
import score  # noqa: E402

T0 = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
COMMIT_AT = T0 + dt.timedelta(days=1)          # 2026-11-02T00:00:00Z
H = dt.timedelta(hours=1)
RISK = {"default_stake_usd": 5.0, "min_edge": 0.04, "max_spread": 0.06}


def iso(t):
    return E.iso(t)


class Repo:
    """A throwaway repo with Phil's layout and a controllable clock."""

    def __init__(self, tmp):
        self.root = pathlib.Path(tmp)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "test")
        self.fulls, self.forecasts, self.ledger = [], [], []
        self.commit({"strategy/playbook.md": "# playbook\n" + "line\n" * 9,
                     "strategy/risk.json": json.dumps(RISK),
                     "strategy/policy.py": "def decide(row, state=None):\n"
                                           "    return {'side': 'yes', 'stake_usd': 1}\n",
                     "core/placeholder.py": "",
                     "journal/.keep": ""},
                    "operator: init", T0 - 10 * H)

    def git(self, *args, when=None):
        env = dict(os.environ)
        if when is not None:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = iso(when)
        return subprocess.run(["git", "-C", str(self.root), *args], env=env,
                              check=True, capture_output=True, text=True).stdout.strip()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, files, msg, when):
        for rel, text in files.items():
            self.write(rel, text)
        self.git("add", "--", *files)
        self.git("commit", "-q", "-m", msg, when=when)
        return self.git("rev-parse", "HEAD")

    def full(self, when, n_rows, category="cat"):
        self.fulls.append({"cycle": iso(when), "tick_type": "FULL",
                           "researched": [{"forecast_id": f"f{when:%d%H}{i}",
                                           "category": category}
                                          for i in range(n_rows)]})
        self.write("strategy/funnel.jsonl",
                   "".join(json.dumps(r) + "\n" for r in self.fulls))

    def forecast(self, rid, when, settled_at, won, est=0.6, mid=0.5,
                 category="cat", rule=None, spread=0.02):
        row = {"id": rid, "ts": iso(when), "market_id": rid, "question": "q?",
               "outcome": "Yes", "token_id": "t", "est_prob": est,
               "market_prob_at_record": mid,
               "best_bid_at_record": round(mid - spread / 2, 4),
               "best_ask_at_record": round(mid + spread / 2, 4),
               "liquidity_at_record": 100000.0, "category": category,
               "skip_reason": "no-edge", "end_date": iso(settled_at),
               "status": "won" if won else "lost", "settled_ts": iso(settled_at)}
        if rule:
            row.update(rule=rule, raw_prob=mid, rule_prob=est)
        self.forecasts.append(row)
        self.write("journal/forecasts.jsonl",
                   "".join(json.dumps(r) + "\n" for r in self.forecasts))

    def ledger_rows(self, rows):
        self.write(E.LEDGER_REL, "".join(json.dumps(r) + "\n" for r in rows))


def open_row(rid, sha, baseline, metric="rows_per_full", window=None,
             keep_if=">= 6.5", rollback_if="< 3", lever=None, prior=None,
             asof=COMMIT_AT + 2 * H, ts=COMMIT_AT + 2 * H):
    return {"event": "open", "id": rid, "ts": iso(ts),
            "hypothesis": "more rows per FULL", "commit": sha,
            "lever": lever or ["strategy/playbook.md#floor"],
            "metric": metric, "window": window or {"n": 4},
            "baseline": baseline, "baseline_asof": iso(asof),
            "keep_if": keep_if, "rollback_if": rollback_if,
            "prior": prior or [], "blocked_by_core": None}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.r = Repo(self._tmp.name)
        # Baseline: four FULLs before the commit with 4, 6, 4, 6 rows (mean 5).
        for i, n in enumerate((4, 6, 4, 6)):
            self.r.full(COMMIT_AT - (8 - 2 * i) * H, n)
        self.r.commit({"strategy/funnel.jsonl":
                       (self.r.root / "strategy/funnel.jsonl").read_text()},
                      "cycle: baseline", COMMIT_AT - H)
        self.sha = self.r.commit({"strategy/playbook.md": "# playbook\nnew rule\n"},
                                 "experiment: E-1 more rows", COMMIT_AT)

    def tearDown(self):
        self._tmp.cleanup()

    def forward(self, counts, start=1):
        for i, n in enumerate(counts):
            self.r.full(COMMIT_AT + (start + 2 * i) * H, n)

    def grade(self, row, asof=COMMIT_AT + 3 * E.DAY):
        return E.grade_one(self.r.root, row, asof)


class ProposeTest(Base):
    def test_baseline_is_the_window_before_the_commit(self):
        self.forward([100])  # after the commit: never in the baseline
        out = E.propose(self.r.root, "rows_per_full", {"n": 4}, self.sha,
                        COMMIT_AT + 5 * H)
        self.assertEqual(out["baseline"], 5.0)
        self.assertEqual(out["baseline_n"], 4)
        self.assertEqual(out["commit"], self.sha)
        self.assertEqual(out["baseline_asof"], iso(COMMIT_AT + 5 * H))

    def test_n_window_takes_the_last_k_units(self):
        out = E.propose(self.r.root, "rows_per_full", {"n": 2}, self.sha,
                        COMMIT_AT)
        self.assertEqual(out["baseline"], 5.0)  # 4 and 6
        out = E.propose(self.r.root, "min_rows_per_full", {"n": 4}, self.sha,
                        COMMIT_AT)
        self.assertEqual(out["baseline"], 4.0)

    def test_days_window_rate(self):
        out = E.propose(self.r.root, "fulls_per_day", {"days": 1}, self.sha,
                        COMMIT_AT)
        self.assertEqual(out["baseline"], 4.0)

    def test_asof_hides_rows_not_yet_known(self):
        out = E.propose(self.r.root, "rows_per_full", {"n": 4}, self.sha,
                        COMMIT_AT - 5 * H)  # only the first two FULLs exist
        self.assertEqual(out["baseline"], 5.0)
        self.assertEqual(out["baseline_n"], 2)

    def test_refusals(self):
        with self.assertRaisesRegex(ValueError, "not in the catalog"):
            E.propose(self.r.root, "vibes", {"n": 4}, self.sha, COMMIT_AT)
        with self.assertRaisesRegex(ValueError, "does not resolve"):
            E.propose(self.r.root, "rows_per_full", {"n": 4}, "deadbeef", COMMIT_AT)
        with self.assertRaisesRegex(ValueError, "days window only"):
            E.propose(self.r.root, "fulls_per_day", {"n": 4}, self.sha, COMMIT_AT)
        with self.assertRaisesRegex(ValueError, "no baseline"):
            E.propose(self.r.root, "tight_dbrier", {"days": 1}, self.sha, COMMIT_AT)

    def test_null_baseline_for_a_new_paired_metric(self):
        # A rule slug never tagged before the commit: no data, baseline null.
        out = E.propose(self.r.root, "rule_verdict:new-rule", {"n": 20},
                        self.sha, COMMIT_AT + 5 * H)
        self.assertIsNone(out["baseline"])
        self.assertEqual(out["baseline_n"], 0)
        # A slug with rows before the commit still gets its number.
        self.r.forecast("old", COMMIT_AT - 3 * H, COMMIT_AT - 2 * H, won=True,
                        rule="old-rule")
        out = E.propose(self.r.root, "rule_verdict:old-rule", {"n": 20},
                        self.sha, COMMIT_AT + 5 * H)
        self.assertAlmostEqual(out["baseline"], -0.09)


class GradeTest(Base):
    def test_collecting_before_the_window_fills(self):
        self.forward([7])
        g = self.grade(open_row("E-1", self.sha, 5.0))
        self.assertEqual(g["verdict"], "COLLECTING")
        self.assertIn("COLLECTING n=1/4", g["line"])

    def test_collecting_with_no_data(self):
        g = self.grade(open_row("E-1", self.sha, 5.0))
        self.assertEqual(g["verdict"], "COLLECTING")
        self.assertIn("n=0/4", g["line"])

    def test_keep(self):
        self.forward([6, 8, 6, 8])  # mean 7: past 6.5, effect 2 < twice the bar 3
        g = self.grade(open_row("E-1", self.sha, 5.0))
        self.assertEqual(g["verdict"], "KEEP")
        self.assertEqual(g["value"], 7.0)

    def test_double_down_on_effect(self):
        self.forward([10, 9, 11, 10])  # effect 5 >= twice the bar 1.5
        g = self.grade(open_row("E-1", self.sha, 5.0))
        self.assertEqual(g["verdict"], "DOUBLE DOWN")

    def test_double_down_on_interval(self):
        self.forward([7, 7, 7, 7])  # effect 2 < 3, but the interval sits at 7
        g = self.grade(open_row("E-1", self.sha, 5.0))
        self.assertEqual(g["verdict"], "DOUBLE DOWN")

    def test_roll_back_after_half_the_window(self):
        self.forward([1])
        self.assertEqual(self.grade(open_row("E-1", self.sha, 5.0))["verdict"],
                         "COLLECTING")  # under half: no early verdict
        self.forward([1], start=3)
        self.assertEqual(self.grade(open_row("E-1", self.sha, 5.0))["verdict"],
                         "ROLL BACK")

    def test_roll_back_wins_over_keep(self):
        self.forward([7, 7, 7, 7])
        row = open_row("E-1", self.sha, 5.0, rollback_if="> 6")
        self.assertEqual(self.grade(row)["verdict"], "ROLL BACK")

    def test_inconclusive(self):
        self.forward([5, 6, 5, 6])
        g = self.grade(open_row("E-1", self.sha, 5.0))
        self.assertEqual(g["verdict"], "INCONCLUSIVE")

    def test_window_ignores_units_past_n(self):
        self.forward([6, 8, 6, 8, 100])
        g = self.grade(open_row("E-1", self.sha, 5.0))
        self.assertEqual((g["verdict"], g["value"], g["n"]), ("KEEP", 7.0, 4))
        self.assertEqual(g["window_end"], iso(COMMIT_AT + 7 * H))

    def test_asof_cutoff(self):
        self.forward([6, 8, 6, 8])
        g = self.grade(open_row("E-1", self.sha, 5.0), asof=COMMIT_AT + 4 * H)
        self.assertEqual((g["verdict"], g["n"]), ("COLLECTING", 2))

    def test_days_window(self):
        self.forward([5, 5, 5, 5, 5, 5])  # FULLs at +1h .. +11h
        row = open_row("E-1", self.sha, 4.0, metric="fulls_per_day",
                       window={"days": 1}, keep_if=">= 5.5", rollback_if="< 2")
        g = self.grade(row, asof=COMMIT_AT + 12 * H)
        self.assertEqual(g["verdict"], "COLLECTING")  # half the day, rate 12/day
        self.assertIn("n=0.5/1 days", g["line"])
        g = self.grade(row, asof=COMMIT_AT + 30 * H)
        self.assertEqual((g["verdict"], g["value"]), ("KEEP", 6.0))

    def test_secondary_metric_clause(self):
        self.forward([12, 1, 12, 12])  # mean 9.25 but one FULL with 1 row
        row = open_row("E-1", self.sha, 5.0,
                       rollback_if="< 3 or min_rows_per_full < 2")
        self.assertEqual(self.grade(row)["verdict"], "ROLL BACK")
        row = open_row("E-1", self.sha, 5.0, keep_if=">= 6.5 and min_rows_per_full >= 2")
        self.assertEqual(self.grade(row)["verdict"], "INCONCLUSIVE")

    def test_blocked_row(self):
        row = {"event": "open", "id": "B-1", "ts": iso(COMMIT_AT),
               "hypothesis": "freshness filter", "lever": ["core/screen.py"],
               "commit": None, "blocked_by_core": "core/screen.py collect freshness"}
        g = self.grade(row)
        self.assertEqual(g["verdict"], "BLOCKED")

    def test_tight_dbrier_respects_settlement_time(self):
        # Recorded after the commit; one settles in the window, one after asof.
        self.r.forecast("a", COMMIT_AT + H, COMMIT_AT + 5 * H, won=True)
        self.r.forecast("b", COMMIT_AT + H, COMMIT_AT + 50 * H, won=False)
        self.r.forecast("w", COMMIT_AT + H, COMMIT_AT + 5 * H, won=True,
                        spread=0.2)  # wide book: not tight
        row = open_row("E-1", self.sha, 0.0, metric="tight_dbrier",
                       window={"n": 2}, keep_if="< 0", rollback_if="> 0.05")
        g = self.grade(row, asof=COMMIT_AT + 10 * H)
        self.assertEqual((g["verdict"], g["n"]), ("COLLECTING", 1))
        g = self.grade(row, asof=COMMIT_AT + 60 * H)
        self.assertEqual(g["n"], 2)
        # a: (0.6-1)^2-(0.5-1)^2 = -0.09; b: 0.36-0.25 = +0.11; mean +0.01
        self.assertAlmostEqual(g["value"], 0.01)
        self.assertEqual(g["verdict"], "INCONCLUSIVE")

    def test_rule_verdict_and_replay(self):
        for i in range(3):
            self.r.forecast(f"r{i}", COMMIT_AT + H, COMMIT_AT + (2 + i) * H,
                            won=True, rule="knife")
        rule = open_row("E-1", self.sha, 0.0, metric="rule_verdict:knife",
                        window={"n": 3}, keep_if="< 0", rollback_if="> 0")
        g = self.grade(rule)
        self.assertEqual(g["verdict"], "KEEP")  # rule 0.6 beats raw 0.5 on wins
        self.assertAlmostEqual(g["value"], -0.09)
        pol = open_row("E-2", self.sha, 0.0,
                       metric="replay_cw_return:strategy/policy.py",
                       window={"n": 3}, keep_if="> 0", rollback_if="< -0.5")
        g = self.grade(pol)  # a zero bar: no effect test, no interval
        self.assertEqual((g["verdict"], g["n"]), ("KEEP", 3))
        self.assertGreater(g["value"], 0)

    def test_null_baseline_grades_against_zero(self):
        row = open_row("E-1", self.sha, None, metric="rule_verdict:knife",
                       window={"n": 3}, keep_if="< -0.01", rollback_if="> 0")
        g = self.grade(row)
        self.assertEqual(g["verdict"], "COLLECTING")
        self.assertIn("COLLECTING n=0/3", g["line"])
        self.assertIn("baseline=null", g["line"])
        for i in range(3):
            self.r.forecast(f"r{i}", COMMIT_AT + H, COMMIT_AT + (2 + i) * H,
                            won=True, rule="knife")
        # -0.09 against a bar of -0.01 from zero: past twice the bar.
        self.assertEqual(self.grade(row)["verdict"], "DOUBLE DOWN")
        row["keep_if"] = "< -0.05"  # -0.09 is short of twice -0.05
        self.assertEqual(self.grade(row)["verdict"], "KEEP")


class StatusTest(Base):
    def test_fold_and_lever_filter(self):
        self.r.ledger_rows([
            open_row("E-1", self.sha, 5.0),
            {"event": "open", "id": "B-1", "ts": iso(COMMIT_AT + 3 * H),
             "hypothesis": "h", "lever": ["core/screen.py"], "commit": None,
             "blocked_by_core": "freshness"},
            {"event": "verdict", "id": "E-1", "ts": iso(COMMIT_AT + 9 * H),
             "verdict": "KEEP", "value": 7.0, "n": 4,
             "source": "core/experiments.py grade"},
            {"event": "close", "id": "E-1", "ts": iso(COMMIT_AT + 9 * H),
             "outcome": "kept", "lesson": "the floor works"}])
        rows = {r["id"]: r for r in E.status(self.r.root)}
        self.assertEqual(rows["E-1"]["state"], "closed:kept")
        self.assertEqual(rows["E-1"]["last_verdict"], "KEEP")
        self.assertEqual(rows["B-1"]["state"], "blocked")
        only = E.status(self.r.root, "strategy/playbook.md")
        self.assertEqual([r["id"] for r in only], ["E-1"])


class CheckLedgerTest(Base):
    def errors(self, rows):
        self.r.ledger_rows(rows)
        return E.check_ledger(self.r.root)

    def assertError(self, rows, pattern):
        errs = self.errors(rows)
        self.assertTrue(any(pattern in e for e in errs),
                        f"no error matching {pattern!r} in {errs}")

    def test_absent_ledger_is_fine(self):
        self.assertEqual(E.check_ledger(self.r.root), [])

    def test_valid_ledger(self):
        self.assertEqual(self.errors([open_row("E-1", self.sha, 5.0)]), [])

    def test_parse_and_schema(self):
        self.r.write(E.LEDGER_REL, "{not json\n")
        self.assertTrue(E.check_ledger(self.r.root))
        self.assertError([{"event": "opened", "id": "x", "ts": iso(T0)}],
                         "unknown event")
        self.assertError([open_row("E-1", self.sha, 5.0, metric="vibes")],
                         "not in the catalog")
        self.assertError([open_row("E-1", self.sha, 5.0, keep_if="better")],
                         "cannot parse clause")
        row = open_row("E-1", self.sha, 5.0)
        del row["baseline_asof"]
        self.assertError([row], "baseline_asof missing")
        self.assertError([open_row("E-1", self.sha, 5.0),
                          open_row("E-1", self.sha, 5.0)], "opened twice")

    def test_baseline_must_be_computed(self):
        self.assertError([open_row("E-1", self.sha, 6.0)],
                         "is not what propose computes")
        closed = {"event": "close", "id": "E-1", "ts": iso(COMMIT_AT + 9 * H),
                  "outcome": "withdrawn", "lesson": "wrong baseline"}
        self.assertEqual(self.errors([open_row("E-1", self.sha, 6.0), closed]), [])

    def test_null_baseline(self):
        rule = dict(metric="rule_verdict:knife", window={"n": 20},
                    keep_if="< -0.01", rollback_if="> 0")
        self.assertEqual(self.errors([open_row("E-1", self.sha, None, **rule)]),
                         [])
        self.assertError([open_row("E-1", self.sha, None)],
                         "baseline null is allowed only for")
        row = open_row("E-1", self.sha, 5.0)
        del row["baseline"]
        self.assertError([row], "baseline missing or not a number")
        # Null is refused once the window before the commit has data.
        self.r.forecast("old", COMMIT_AT - 3 * H, COMMIT_AT - 2 * H, won=True,
                        rule="knife")
        self.assertError([open_row("E-1", self.sha, None, **rule)],
                         "baseline null, but propose computes -0.09")

    def test_commit_rules(self):
        self.assertError([open_row("E-1", "0" * 40, 5.0)], "does not resolve")
        core = self.r.commit({"core/placeholder.py": "x = 1\n"}, "sneaky",
                             COMMIT_AT + H)
        self.assertError([open_row("E-1", core, 5.0)], "touches ['core/placeholder.py']")
        three = self.r.commit({"strategy/a.md": "a", "strategy/b.md": "b",
                               "strategy/c.md": "c"}, "big", COMMIT_AT + H)
        self.assertError([open_row("E-1", three, 5.0)], "touches 3 files")
        led = self.r.commit({"strategy/a.md": "a2", E.LEDGER_REL: "\n"}, "ledger",
                            COMMIT_AT + H)
        self.assertError([open_row("E-1", led, 5.0)], "never the ledger itself")

    def test_commit_must_be_an_ancestor(self):
        self.r.git("checkout", "-q", "-b", "side")
        side = self.r.commit({"strategy/x.md": "x"}, "side", COMMIT_AT + H)
        self.r.git("checkout", "-q", "main")
        self.assertError([open_row("E-1", side, 5.0)], "not an ancestor of HEAD")

    def test_risk_loosening_is_refused(self):
        loose = self.r.commit({"strategy/risk.json":
                               json.dumps(dict(RISK, min_edge=0.03))},
                              "loosen", COMMIT_AT + H)
        self.assertError([open_row("E-1", loose, 5.0, lever=["strategy/risk.json"])],
                         "loosens strategy/risk.json (min_edge 0.04 -> 0.03)")
        tight = self.r.commit({"strategy/risk.json":
                               json.dumps(dict(RISK, min_edge=0.05, max_spread=0.05))},
                              "tighten", COMMIT_AT + 2 * H)
        errs = self.errors([open_row("E-1", tight, 5.0, lever=["strategy/risk.json"])])
        self.assertFalse([e for e in errs if "loosens" in e], errs)

    def test_protected_lever(self):
        self.assertError([open_row("E-1", self.sha, 5.0, lever=["CYCLE.md#step-3"])],
                         "is not an agent-owned strategy/ file")

    def test_lever_held_by_an_open_experiment(self):
        self.assertError([open_row("E-1", self.sha, 5.0),
                          open_row("E-2", self.sha, 5.0)],
                         "already held by open experiment E-1")

    def test_open_cap(self):
        rows = [open_row(f"E-{i}", self.sha, 5.0, lever=[f"strategy/playbook.md#s{i}"])
                for i in range(4)]
        self.assertError(rows, "4 experiments open, the cap is 3")
        blocked = {"event": "open", "id": "B-1", "ts": iso(COMMIT_AT),
                   "hypothesis": "h", "lever": ["core/screen.py"], "commit": None,
                   "blocked_by_core": "freshness"}
        self.assertEqual(self.errors(rows[:3] + [blocked]), [])

    def test_failed_lever_needs_prior(self):
        closed = [open_row("E-1", self.sha, 5.0),
                  {"event": "close", "id": "E-1", "ts": iso(COMMIT_AT + 9 * H),
                   "outcome": "rolled_back", "lesson": "did not help"}]
        retry = open_row("E-2", self.sha, 5.0, ts=COMMIT_AT + 10 * H)
        self.assertError(closed + [retry], "was rolled back in E-1")
        retry["prior"] = ["E-1"]
        self.assertEqual(self.errors(closed + [retry]), [])
        late = open_row("E-3", self.sha, 5.0, ts=COMMIT_AT + 40 * E.DAY)
        self.assertEqual(self.errors(closed + [late]), [])

    def test_verdict_and_close_rules(self):
        self.assertError([{"event": "verdict", "id": "E-9", "ts": iso(T0),
                           "verdict": "KEEP"}], "which is not open")
        self.assertError([open_row("E-1", self.sha, 5.0),
                          {"event": "verdict", "id": "E-1", "ts": iso(T0),
                           "verdict": "GREAT"}], "verdict 'GREAT'")
        self.assertError([open_row("E-1", self.sha, 5.0),
                          {"event": "close", "id": "E-1", "ts": iso(T0),
                           "outcome": "kept", "lesson": ""}], "one-line lesson")
        close = {"event": "close", "id": "E-1", "ts": iso(T0), "outcome": "kept",
                 "lesson": "x"}
        self.assertError([open_row("E-1", self.sha, 5.0), close, close],
                         "close for E-1, which is not open")

    def test_blocked_row_needs_a_reason(self):
        self.assertError([{"event": "open", "id": "B-1", "ts": iso(T0),
                           "hypothesis": "h", "lever": ["core/screen.py"],
                           "commit": None}], "no commit and no blocked_by_core")


class ParseTest(unittest.TestCase):
    def test_conditions(self):
        self.assertEqual(E.parse_condition("< 6.0 or min_rows_per_full < 8"),
                         [[(None, "<", 6.0)], [("min_rows_per_full", "<", 8.0)]])
        self.assertEqual(E.parse_condition(">= 9 and tight_dbrier:soccer <= 0"),
                         [[(None, ">=", 9.0), ("tight_dbrier:soccer", "<=", 0.0)]])
        for bad in ("", "about 9", "nope < 3", "== 3"):
            with self.assertRaises(ValueError):
                E.parse_condition(bad)

    def test_windows(self):
        m = E.CATALOG["rows_per_full"]
        self.assertEqual(E.parse_window({"n": 14}, m), (None, 14))
        self.assertEqual(E.parse_window({"days": 30, "n": 15}, m), (30, 15))
        for bad in ({}, {"fulls": 14}, {"n": 0}, {"n": 1.5}, {"days": -1}, None):
            with self.assertRaises(ValueError):
                E.parse_window(bad, m)
        self.assertEqual(E.parse_window_spec("days=30,n=15"), {"days": 30, "n": 15})

    def test_metric_arguments(self):
        with self.assertRaisesRegex(ValueError, "needs an argument"):
            E.parse_metric("rule_verdict")
        with self.assertRaisesRegex(ValueError, "takes no argument"):
            E.parse_metric("rows_per_full:x")
        with self.assertRaisesRegex(ValueError, "policy path under strategy/"):
            E.parse_metric("replay_cw_return:core/replay.py")


class ScoreSinceTest(unittest.TestCase):
    def test_cutoffs(self):
        now = dt.datetime(2026, 11, 17, 6, tzinfo=dt.timezone.utc)
        self.assertEqual(score.since_cutoff("7d", now), "2026-11-10T06:00:00Z")
        self.assertEqual(score.since_cutoff("36h", now), "2026-11-15T18:00:00Z")
        self.assertEqual(score.since_cutoff("2026-11-16", now), "2026-11-16T00:00:00Z")
        self.assertEqual(score.since_cutoff("2026-11-16T05:40:00Z", now),
                         "2026-11-16T05:40:00Z")
        with self.assertRaises(SystemExit):
            score.since_cutoff("last week", now)

    def test_settled_since_keeps_open_rows(self):
        rows = [{"status": "open"},
                {"status": "won", "settled_ts": "2026-11-15T00:00:00Z"},
                {"status": "lost", "settled_ts": "2026-11-17T00:00:00Z"}]
        kept = score.settled_since(rows, "2026-11-16T00:00:00Z")
        self.assertEqual([r["status"] for r in kept], ["open", "lost"])


if __name__ == "__main__":
    unittest.main()
