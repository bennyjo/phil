#!/usr/bin/env python3
"""Offline tests for the Gamma token-id guard in core/pmapi.py and core/scan.py.

PROTECTED CORE - the trading agent must not edit files under core/.

Polymarket Protocol V2 markets (from 2026-11-02) set clobTokenIds to null.
Before this guard, json.loads(None) raised TypeError and the first such
market killed the whole scan. These tests feed hand-built Gamma records, so
nothing touches the network. CI runs it on every push.

Usage: python3 core/test_token_ids.py
"""
import argparse
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402
import scan  # noqa: E402


def gamma(**over):
    m = {"id": "1", "question": "Will it happen?", "version": "v1",
         "outcomes": json.dumps(["Yes", "No"]),
         "outcomePrices": json.dumps(["0.4", "0.6"]),
         "clobTokenIds": json.dumps(["111", "222"]),
         "volume24hr": 1000}
    m.update(over)
    return m


V2 = {"version": "v2", "clobTokenIds": None, "positionIds": json.dumps(["9", "8"])}


class TokenIds(unittest.TestCase):
    def test_v1_reads_clob_token_ids(self):
        self.assertEqual(pmapi.token_ids(gamma()), ["111", "222"])
        self.assertEqual(pmapi.market_tokens(gamma()), {"Yes": "111", "No": "222"})

    def test_untagged_market_is_v1(self):
        m = gamma()
        del m["version"]
        self.assertEqual(pmapi.token_ids(m), ["111", "222"])

    def test_v2_is_unsupported(self):
        self.assertIsNone(pmapi.token_ids(gamma(**V2)))
        self.assertIsNone(pmapi.market_tokens(gamma(**V2)))

    def test_unusable_ids_are_unsupported(self):
        for ids in (None, "", "not json", json.dumps([]), json.dumps(["111"]),
                    json.dumps({"Yes": "111"})):
            with self.subTest(ids=ids):
                self.assertIsNone(pmapi.token_ids(gamma(clobTokenIds=ids)))


class ScanKeep(unittest.TestCase):
    def setUp(self):
        scan.UNSUPPORTED.clear()
        self.args = argparse.Namespace(min_volume_24h=0)

    def test_v2_market_is_skipped_not_fatal(self):
        seen = set()
        self.assertIsNone(scan.keep(gamma(id="2", **V2), seen, [], self.args))
        rec = scan.keep(gamma(id="3"), seen, [], self.args)
        self.assertEqual(rec["clob_token_ids"], ["111", "222"])
        self.assertEqual(dict(scan.UNSUPPORTED), {"v2": 1})


if __name__ == "__main__":
    unittest.main()
