#!/usr/bin/env python3
"""Offline tests for the core-opened funnel row (proposal P10).

PROTECTED CORE - the trading agent must not edit files under core/.

A FULL cycle runs core/screen.py prepare, the screener subagents, collect,
and then the agent's core/funnel.py merge. Each test drives that path through
the real CLIs in a temporary copy of the files they read, and checks that it
leaves exactly one strategy/funnel.jsonl row for the cycle. The ForecastRow
tests drive core/forecast.py record in-process with a stubbed market, on FULL
and TRIGGERED ticks, and check that strategy/tools/reconcile.py then passes
with no hand-written funnel row. The real journal and funnel are never
touched. CI runs it on every push.

Usage: python3 core/test_funnel.py
"""
import contextlib
import datetime as dt
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import forecast  # noqa: E402
import funnel  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
COPIED = ("core/screen.py", "core/funnel.py", "config/protected.json",
          "strategy/screener-prompt.md", "strategy/screener-strata.json",
          "strategy/screener-filters.json", "strategy/tools/reconcile.py")

GAMMA = {"question": "Will it happen?", "slug": "q", "endDate": "2026-12-30T00:00:00Z",
         "outcomes": json.dumps(["Yes", "No"]), "clobTokenIds": json.dumps(["111", "222"]),
         "version": "v1", "liquidityNum": "900", "volume24hr": "100"}
BOOK = {"bid": 0.49, "ask": 0.51, "min_order_size": 5.0}


def stamp(when):
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def candidate(i, query):
    end = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=24 + i)
    return {"market_id": str(1000 + i), "question": f"Will event {i} happen?",
            "end_date": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "outcomes": ["Yes", "No"], "outcome_prices": [0.3, 0.7],
            "volume_24h": 1000.0 * i, "liquidity": 500.0 * i,
            "description": "test market", "query": query}


class FunnelRow(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="phil-funnel-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        for rel in COPIED:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(REPO / rel, self.root / rel)
        self.funnel = self.root / "strategy" / "funnel.jsonl"
        self.funnel.write_text('{"cycle": "2026-10-24T22:12:00Z", "tick_type": "FULL"}\n')
        cands = [candidate(i, "by-liquidity" if i % 2 else "active-today")
                 for i in range(1, 6)]
        self.cands = self.root / "candidates.jsonl"
        self.cands.write_text("".join(json.dumps(c) + "\n" for c in cands))
        self.env = dict(os.environ, PHIL_RUNNER="test")
        self.env.pop("PHIL_PUSH_BY_LOOP", None)

    def run_core(self, *args, ok=True):
        proc = subprocess.run([sys.executable, *args], cwd=self.root, env=self.env,
                              capture_output=True, text=True, timeout=60)
        if ok:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def prepare(self):
        proc = self.run_core("core/screen.py", "prepare", "--file", str(self.cands),
                             "--batch-size", "2")
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    def rows(self):
        return [json.loads(line) for line in self.funnel.read_text().splitlines()]

    def answer_batches(self, header):
        work = self.root / header["work_dir"]
        for b in header["batches"]:
            batch = json.loads((work / b["batch_file"]).read_text())
            out = [{"market_id": m["market_id"], "prob": {"Yes": 0.6, "No": 0.4},
                    "confidence": "low", "reason": "test"} for m in batch["markets"]]
            (work / b["out_file"]).write_text(json.dumps(out))
        return work

    def test_full_cycle_leaves_exactly_one_row(self):
        header = self.prepare()
        cycle = header["funnel_cycle"]
        work = self.answer_batches(header)
        self.run_core("core/screen.py", "collect", "--dir", str(work))
        self.run_core("core/funnel.py", "merge", "--cycle", cycle, "--json",
                      json.dumps({"researched": [{"market_id": "1001",
                                                  "skip_reason": "no-edge",
                                                  "forecast_id": "abc"}],
                                  "placed": 0, "mode": "paper"}))
        rows = self.rows()
        self.assertEqual(len(rows), 2, "one pre-existing row plus this cycle's")
        self.assertEqual(sum(r.get("cycle") == cycle for r in rows), 1)
        row = rows[-1]
        self.assertEqual(row["tick_type"], "FULL")
        self.assertEqual(row["runner"], "test")
        self.assertEqual(row["pool_total"], 5)
        self.assertEqual(row["pool_by_query"], {"by-liquidity": 3, "active-today": 2})
        self.assertEqual(row["screener_batches"], 3)
        self.assertEqual(row["screened"], 5)
        self.assertEqual(row["escalated"], 5)
        self.assertEqual(row["researched"][0]["forecast_id"], "abc")
        self.assertEqual(row["mode"], "paper")

    def test_quota_exhausted_full_still_opens_one_row(self):
        quota = self.root / "journal" / "screener-quota" / "test.json"
        quota.parent.mkdir(parents=True)
        today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        quota.write_text(json.dumps({"day": today, "batches": 10_000}))
        self.assertIsNone(self.prepare(), "exhausted quota keeps stdout empty")
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["screened"], 0)
        self.assertEqual(rows[-1]["pool_total"], 5)
        self.assertIn("quota exhausted", rows[-1]["screener"])

    def test_rerun_prepare_reuses_the_open_row(self):
        first = self.prepare()["funnel_cycle"]
        second = self.prepare()["funnel_cycle"]
        self.assertEqual(first, second)
        self.assertEqual(len(self.rows()), 2)

    def test_merge_refuses_core_fields_and_unknown_cycles(self):
        cycle = self.prepare()["funnel_cycle"]
        before = self.funnel.read_text()
        refused = self.run_core("core/funnel.py", "merge", "--cycle", cycle,
                                "--json", '{"screened": 999}', ok=False)
        self.assertEqual(refused.returncode, 1)
        missing = self.run_core("core/funnel.py", "merge", "--cycle",
                                "2026-01-01T00:00:00Z", "--json", '{"placed": 0}',
                                ok=False)
        self.assertEqual(missing.returncode, 1)
        self.assertEqual(self.funnel.read_text(), before)

    def test_dry_run_writes_no_row(self):
        self.run_core("core/screen.py", "prepare", "--file", str(self.cands),
                      "--dry-run")
        self.assertEqual(len(self.rows()), 1)


class ForecastRow(FunnelRow):
    """core/forecast.py record writes its forecast into the cycle's funnel row."""

    def setUp(self):
        super().setUp()
        self.forecasts = self.root / "journal" / "forecasts.jsonl"
        self.triggers = self.root / "journal" / "watch-triggers.jsonl"
        self.forecasts.parent.mkdir(parents=True, exist_ok=True)
        later = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
        (self.root / "strategy" / "schedule.json").write_text(
            json.dumps({"next_full_cycle_after": stamp(later)}))
        for p in (mock.patch.object(forecast, "FORECASTS", self.forecasts),
                  mock.patch.object(funnel, "FUNNEL", self.funnel),
                  mock.patch.object(funnel, "WATCH_TRIGGERS", self.triggers, create=True),
                  mock.patch.object(forecast.pmapi, "gamma_market", lambda _id: GAMMA),
                  mock.patch.object(forecast.pmapi, "book_quote", lambda _t: BOOK),
                  mock.patch.dict(os.environ, {"PHIL_RUNNER": "test"})):
            p.start()
            self.addCleanup(p.stop)

    def fire(self, *keys, minutes_ago=3):
        utc = stamp(dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=minutes_ago))
        with self.triggers.open("a") as fh:
            for key in keys:
                fh.write(json.dumps({"utc": utc, "kind": "new_market", "key": key,
                                     "market_id": key.split(":")[-1]}) + "\n")

    def record(self, market_id, skip="no-edge"):
        argv = ["forecast.py", "record", "--market-id", market_id, "--outcome", "Yes",
                "--est-prob", "0.55", "--category", "test", "--skip-reason", skip]
        out = io.StringIO()
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out):
            forecast.main()
        return json.loads(out.getvalue())

    def reconcile(self):
        return subprocess.run([sys.executable, "strategy/tools/reconcile.py"],
                              cwd=self.root, capture_output=True, text=True, timeout=60)

    def assert_reconciles(self):
        proc = self.reconcile()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_triggered_tick_forecast_opens_its_own_row(self):
        self.fire("newmarket:6440125")
        out = self.record("6440125")
        rows = self.rows()
        self.assertEqual(len(rows), 2, "one pre-existing row plus this tick's")
        row = rows[-1]
        self.assertEqual(row["tick_type"], "TRIGGERED")
        self.assertEqual(row["trigger"], "newmarket:6440125")
        self.assertEqual(row["runner"], "test")
        self.assertEqual(row["opened_by"], "core/forecast.py")
        self.assertEqual(out["funnel_cycle"], row["cycle"])
        self.assertEqual([(e["market_id"], e["skip_reason"], e["forecast_id"])
                          for e in row["researched"]],
                         [("6440125", "no-edge", out["recorded"])])
        self.assert_reconciles()

    def test_second_forecast_in_a_triggered_tick_joins_the_same_row(self):
        self.fire("newmarket:6435746", "newmarket:6435745")
        first = self.record("6435746")
        second = self.record("6435745", skip="market-agrees")
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["trigger"], "newmarket:6435746,newmarket:6435745")
        self.assertEqual([e["forecast_id"] for e in rows[-1]["researched"]],
                         [first["recorded"], second["recorded"]])
        self.assertEqual(first["funnel_cycle"], second["funnel_cycle"])
        self.assert_reconciles()

    def test_full_cycle_forecast_lands_in_the_prepare_row(self):
        cycle = self.prepare()["funnel_cycle"]
        out = self.record("1001")
        self.assertEqual(out["funnel_cycle"], cycle)
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["tick_type"], "FULL")
        self.assertEqual(rows[-1]["researched"][0]["forecast_id"], out["recorded"])
        self.assert_reconciles()

    def test_triggered_tick_after_a_full_opens_a_new_row(self):
        self.prepare()
        rows = self.rows()
        full = stamp(dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=25))
        rows[-1]["cycle"] = full  # the FULL ran 25 min ago, inside REOPEN_WINDOW
        self.funnel.write_text("".join(json.dumps(r) + "\n" for r in rows))
        self.fire("newmarket:7")
        out = self.record("7")
        self.assertNotEqual(out["funnel_cycle"], full)
        self.assertEqual(self.rows()[-1]["tick_type"], "TRIGGERED")
        self.assertEqual(self.rows()[-2]["researched"], [])

    def test_agent_merge_keeps_core_recorded_forecasts(self):
        cycle = self.prepare()["funnel_cycle"]
        kept = self.record("1001")
        self.run_core("core/funnel.py", "merge", "--cycle", cycle, "--json",
                      json.dumps({"researched": [{"market_id": "1003",
                                                  "skip_reason": "benchmark-unreachable"}],
                                  "placed": 0}))
        ids = [e.get("forecast_id") for e in self.rows()[-1]["researched"]]
        self.assertEqual(ids, [None, kept["recorded"]])
        self.assert_reconciles()

    def test_merge_refuses_a_non_list_researched(self):
        cycle = self.prepare()["funnel_cycle"]
        before = self.funnel.read_text()
        refused = self.run_core("core/funnel.py", "merge", "--cycle", cycle,
                                "--json", '{"researched": 3}', ok=False)
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(self.funnel.read_text(), before)


if __name__ == "__main__":
    unittest.main()
