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
