#!/usr/bin/env python3
"""Offline tests for the monthly screener log and the journal size tripwire.

PROTECTED CORE - the trading agent must not edit files under core/.

core/screen.py appends screener rows to journal/screener/YYYY-MM.jsonl and
reads them back through log_rows(), which also covers the pre-rotation
journal/screener.jsonl. core/validate.py fails for any journal file over
80 MB. Each test works in a temporary copy, so the real journal is never
touched. CI runs it on every push.

Usage: python3 core/test_screener_log.py
"""
import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent


def load_screen():
    spec = importlib.util.spec_from_file_location("screen", REPO / "core" / "screen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ScreenerLog(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="phil-screener-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.screen = load_screen()
        self.screen.ROOT = self.tmp
        self.screen.LOG_DIR = self.tmp / "journal" / "screener"
        self.screen.LEGACY_LOG_FILE = self.tmp / "journal" / "screener.jsonl"

    def test_append_goes_to_the_rows_month(self):
        rel = self.screen.append_log([{"ts": "2026-10-31T23:59:00Z"}],
                                     "2026-10-31T23:59:00Z")
        self.assertEqual(str(rel), "journal/screener/2026-10.jsonl")
        self.screen.append_log([{"ts": "2026-11-01T00:01:00Z"}],
                               "2026-11-01T00:01:00Z")
        self.assertEqual([p.name for p in self.screen.log_files()],
                         ["2026-10.jsonl", "2026-11.jsonl"])

    def test_reads_both_layouts_legacy_first(self):
        self.screen.LEGACY_LOG_FILE.parent.mkdir(parents=True)
        self.screen.LEGACY_LOG_FILE.write_text('{"ts": "legacy"}\n\n')
        self.screen.append_log([{"ts": "2026-10-14T00:00:00Z"}],
                               "2026-10-14T00:00:00Z")
        self.assertEqual([r["ts"] for r in self.screen.log_rows()],
                         ["legacy", "2026-10-14T00:00:00Z"])

    def test_no_log_yields_nothing(self):
        self.assertEqual(list(self.screen.log_rows()), [])


class JournalSizeTripwire(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="phil-validate-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        for d in ("core", "config", "strategy"):
            shutil.copytree(REPO / d, self.tmp / d,
                            ignore=shutil.ignore_patterns("__pycache__"))
        (self.tmp / "journal" / "screener").mkdir(parents=True)

    def validate(self):
        return subprocess.run([sys.executable, str(self.tmp / "core" / "validate.py")],
                              capture_output=True, text=True)

    def sparse(self, rel, mb):
        with open(self.tmp / rel, "wb") as fh:
            fh.truncate(mb * 1024 * 1024)

    def test_file_under_limit_passes(self):
        self.sparse("journal/cycles.log", 79)
        res = self.validate()
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_file_over_limit_fails(self):
        self.sparse("journal/cycles.log", 81)
        res = self.validate()
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("journal/cycles.log: 81.0 MB is over the 80 MB", res.stdout)


if __name__ == "__main__":
    unittest.main()
