#!/usr/bin/env python3
"""Offline tests for core/real.py settle reconciliation.

PROTECTED CORE - the trading agent must not edit files under core/.

The connect skill scripts and the signer healthcheck are stubbed, and the
real ledger points at a temporary file, so nothing touches funds or the
network. CI runs it on every push.

Usage: python3 core/test_real.py
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parent.parent


def load_real():
    spec = importlib.util.spec_from_file_location("real", REPO / "core" / "real.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Place(unittest.TestCase):
    """Real orders stay on V1: a V2 twin is refused before any money moves."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="phil-real-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.real = load_real()
        self.real.REAL_LEDGER = self.tmp / "real-ledger.jsonl"
        self.real.PAPER_LEDGER = self.tmp / "ledger.jsonl"
        self.real.PAPER_LEDGER.write_text(json.dumps(
            {"id": "p1", "market_id": "7", "token_id": "9", "edge_class": "info-race"}) + "\n")

    def place(self, gamma_market):
        scripts = []

        def run_script(store, name, *args, timeout=180):
            scripts.append(name)
            return 0, {"ok": True}, ""

        args = mock.Mock(paper_id="p1", usd=None)
        real_caps = {"max_stake_usd": 1, "allowed_edge_classes": ["info-race"],
                     "max_open_positions": 5, "daily_stake_cap_usd": 5}
        out = io.StringIO()
        with mock.patch.object(self.real, "load_protected", return_value=({}, real_caps)), \
             mock.patch.object(self.real, "store_path", return_value=self.tmp), \
             mock.patch.object(self.real, "healthy", return_value=True), \
             mock.patch.object(self.real, "run_script", side_effect=run_script), \
             mock.patch.object(self.real.pmapi, "gamma_market", gamma_market), \
             contextlib.redirect_stdout(out):
            try:
                self.real.cmd_place(args)
                code = 0
            except SystemExit as e:
                code = e.code
        return code, scripts, out.getvalue()

    def assert_refused(self, code, scripts):
        self.assertNotEqual(code, 0)
        self.assertEqual(scripts, [])
        self.assertFalse(self.real.REAL_LEDGER.exists())

    def test_v2_market_is_refused_before_any_money_moves(self):
        code, scripts, out = self.place(lambda _id: {"version": "v2"})
        self.assert_refused(code, scripts)
        self.assertIn("read-only", out)

    def test_untagged_market_is_refused(self):
        code, scripts, _out = self.place(lambda _id: {})
        self.assert_refused(code, scripts)

    def test_unreadable_version_fails_closed(self):
        def down(_id):
            raise RuntimeError("gamma down")
        code, scripts, out = self.place(down)
        self.assert_refused(code, scripts)
        self.assertIn("gamma down", out)

    def test_v1_market_still_places(self):
        code, scripts, _out = self.place(lambda _id: {"version": "v1"})
        self.assertEqual(code, 0)
        self.assertEqual(scripts, ["funds.py", "trade.py"])


class Settle(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="phil-real-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.real = load_real()
        self.real.REAL_LEDGER = self.tmp / "real-ledger.jsonl"
        self.real.append_real({"id": "r-pending", "token_id": "111",
                               "status": "pending"})
        self.real.append_real({"id": "r-placed", "token_id": "222",
                               "status": "placed"})

    def settle(self, positions_result):
        def run_script(store, name, *args, timeout=180):
            if name == "positions.py":
                return positions_result
            return 0, {"ok": True}, ""
        with mock.patch.object(self.real, "load_protected", return_value=({}, {})), \
             mock.patch.object(self.real, "store_path", return_value=self.tmp), \
             mock.patch.object(self.real, "healthy", return_value=True), \
             mock.patch.object(self.real, "run_script", side_effect=run_script), \
             contextlib.redirect_stdout(io.StringIO()):
            try:
                self.real.cmd_settle(None)
                code = 0
            except SystemExit as e:
                code = e.code
        return code, {r["id"]: r for r in self.real.real_rows()}

    def assert_untouched(self, code, rows):
        self.assertNotEqual(code, 0)
        self.assertEqual(rows["r-pending"]["status"], "pending")
        self.assertNotIn("settled", rows["r-placed"])
        settles = [r for r in rows.values() if r.get("type") == "settle"]
        self.assertEqual(len(settles), 1, "the sweep/redeem result is still logged")
        self.assertIn("reconcile_skipped", settles[0])

    def test_positions_script_fails_closed(self):
        self.assert_untouched(*self.settle((1, None, "data-api 410 Gone")))

    def test_positions_timeout_fails_closed(self):
        self.assert_untouched(*self.settle((None, None, "positions.py timed out")))

    def test_unrecognised_positions_shape_fails_closed(self):
        self.assert_untouched(*self.settle((0, {"raw": "not json"}, "")))

    def test_live_positions_reconcile(self):
        code, rows = self.settle((0, [{"token_id": "111"}], ""))
        self.assertEqual(code, 0)
        self.assertEqual(rows["r-pending"]["status"], "placed")
        self.assertTrue(rows["r-placed"]["settled"])

    def test_empty_positions_list_reconciles(self):
        code, rows = self.settle((0, {"positions": []}, ""))
        self.assertEqual(code, 0)
        self.assertEqual(rows["r-pending"]["status"], "failed")
        self.assertTrue(rows["r-placed"]["settled"])


if __name__ == "__main__":
    unittest.main()
