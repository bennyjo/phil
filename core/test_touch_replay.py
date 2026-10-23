#!/usr/bin/env python3
"""Offline tests for the touch replay gate (core/touch_replay.py).

PROTECTED CORE - the trading agent must not edit files under core/.

The replay must never see data from after a forecast's time. The trap it
guards against: a windowed /v2/prices-history read of a resolved market ends
with the settlement payout, so "the last price before t" from a window is the
outcome. These tests serve hand-built Gamma, Binance, and price-history
responses from a fake transport that answers a windowed read the way the real
API does, so nothing touches the network. CI runs it on every push.

Usage: python3 core/test_touch_replay.py
"""
import argparse
import contextlib
import datetime as dt
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import touch_replay as tr  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
H = 3600


def ts(s):
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


WSTART = ts("2026-10-19T04:00:00Z")     # midnight ET, October 19
END = ts("2026-10-20T04:00:00Z")
SPIKE = WSTART + 6 * H                  # BTC bar opening 10:00Z touches $110k
MARKETS = [
    {"id": "1", "question": "Will Bitcoin reach $110,000 on October 19?", "version": "v1",
     "endDate": "2026-10-20T04:00:00Z", "startDate": "2026-10-19T04:00:12Z",
     "outcomes": json.dumps(["Yes", "No"]), "outcomePrices": json.dumps(["1", "0"]),
     "clobTokenIds": json.dumps(["btc-yes", "btc-no"])},
    {"id": "2", "question": "Will Ethereum dip to $3,000 on October 19?", "version": "v2",
     "endDate": "2026-10-20T04:00:00Z", "startDate": "2026-10-19T04:00:12Z",
     "outcomes": json.dumps(["Yes", "No"]), "outcomePrices": json.dumps(["0", "1"]),
     "clobTokenIds": None, "positionIds": ["eth-yes", "eth-no"]},
    {"id": "3", "question": "Will Bitcoin be above $100,000 on October 19?", "version": "v1",
     "endDate": "2026-10-20T04:00:00Z", "startDate": "2026-10-19T04:00:12Z",
     "outcomes": json.dumps(["Yes", "No"]), "outcomePrices": json.dumps(["1", "0"]),
     "clobTokenIds": json.dumps(["x", "y"])},
]


def bar(open_ts, symbol):
    base = 100_000.0 if symbol == "BTCUSDT" else 4_000.0
    close = base * (1.01 if (open_ts // 86400) % 2 else 1.0)
    high = 120_000.0 if symbol == "BTCUSDT" and open_ts == SPIKE else close * 1.001
    return [open_ts * 1000, str(close), str(high), str(close * 0.999), str(close)]


class FakeAPI:
    """Serves the three endpoints; a windowed price read gets the payout."""

    def __init__(self):
        self.hist_calls = []

    def __call__(self, url, params=None):
        if url == tr.KEYSET:
            return {"markets": MARKETS, "next_cursor": None}
        if url == tr.KLINES:
            t0 = params["startTime"] // 1000
            return [bar(t, params["symbol"]) for t in range(t0, min(END, t0 + 1000 * H), H)]
        if url == tr.HIST:
            self.hist_calls.append(dict(params))
            if "as_of" not in params:            # what the real API does to a window
                return {"data": [{"timestamp": params["end"] - 60, "price": 1.0,
                                  "resolution_seconds": 0}]}
            t = params["as_of"]
            return {"data": [
                {"timestamp": t - 300, "price": 0.30, "resolution_seconds": 300},
                {"timestamp": t - 60, "price": 0.99, "resolution_seconds": 300},  # ends after t
            ]}
        raise AssertionError(f"unexpected url {url}")


class Offline(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()
        self.saved = tr.http, tr.HIST_INTERVAL_S, tr.CACHE
        self.tmp = tempfile.TemporaryDirectory()
        tr.http, tr.HIST_INTERVAL_S = self.api, 0.0
        tr.CACHE = pathlib.Path(self.tmp.name) / "touch-prices.jsonl"

    def tearDown(self):
        tr.http, tr.HIST_INTERVAL_S, tr.CACHE = self.saved
        self.tmp.cleanup()


class LeakGuard(Offline):
    def test_windowed_read_is_refused(self):
        for params in ({"token_id": "a", "start": 1, "end": 2},
                       {"token_id": "a", "as_of": 2, "end": 2},
                       {"token_id": "a", "interval": "max"}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                tr.price_at(params)
        self.assertEqual(self.api.hist_calls, [])

    def test_every_price_read_is_as_of_the_forecast_time(self):
        rows, _ = tr.build_rows(WSTART - 86400, END, 600)
        self.assertTrue(self.api.hist_calls)
        for p in self.api.hist_calls:
            self.assertEqual(set(p), {"token_id", "as_of"})
        self.assertEqual({(p["token_id"], p["as_of"]) for p in self.api.hist_calls},
                         {("btc-yes" if r["asset"] == "Bitcoin" else "eth-yes", r["t"])
                          for r in rows})

    def test_rows_see_nothing_after_t(self):
        rows, funnel = tr.build_rows(WSTART - 86400, END, 600)
        self.assertEqual(funnel["parsed"], 2)       # the "above" market is not a touch
        btc = [r for r in rows if r["asset"] == "Bitcoin"]
        # Only 10:00Z is live: the spike bar opens at t and closes after it,
        # so it neither touches the barrier nor sets the spot. Later times
        # see the touch and are dropped.
        self.assertEqual([r["t"] for r in btc], [SPIKE])
        self.assertEqual(btc[0]["spot"], float(bar(SPIKE - H, "BTCUSDT")[4]))
        # The 0.99 point's bucket ends after t, so the mid is the 0.30 one.
        self.assertEqual({r["mid"] for r in rows}, {0.30})
        self.assertTrue(all(r["mid_age_s"] >= 0 for r in rows))
        # Protocol V2 ids come from positionIds.
        self.assertEqual(len([r for r in rows if r["asset"] == "Ethereum"]), 3)

    def test_rule_never_sees_the_outcome(self):
        rows, _ = tr.build_rows(WSTART - 86400, END, 600)
        seen = []
        tr.evaluate(rows, (lambda *a: 0.5, lambda raw, mid, row: seen.append(row) or raw))
        self.assertTrue(seen)
        for row in seen:
            self.assertEqual(set(row), set(tr.RULE_ROW_KEYS))

    def test_cached_lookahead_point_is_rechecked(self):
        t = 1000
        self.assertIsNone(tr.usable_point({"timestamp": 900, "price": 1.0,
                                           "resolution_seconds": 300}, t))
        self.assertIsNotNone(tr.usable_point({"timestamp": 700, "price": 0.4,
                                              "resolution_seconds": 300}, t))


def fixture(n_paths, y=0.0, mid=0.3):
    """One row per price path, end dates a day apart."""
    return [{"asset": "Bitcoin", "window": "daily", "end": 1_790_000_000 + i * 86400,
             "mid": mid, "y": y} for i in range(n_paths)]


class Scoring(unittest.TestCase):
    def test_paired_means_on_fixed_rows(self):
        rows = fixture(25)
        base, cand = [(0.6, 0.5)] * 25, [(0.6, 0.4)] * 25
        res = tr.score(rows, base, cand)
        whole = res["slices"][0]
        # Brier vs mid: raw 0.36-0.09, current 0.25-0.09, candidate 0.16-0.09.
        self.assertEqual(whole["raw"]["mean"], 0.27)
        self.assertEqual(whole["cur"]["mean"], 0.16)
        self.assertEqual(whole["cand"]["mean"], 0.07)
        self.assertEqual(whole["paired"], {"mean": -0.09, "lo": -0.09, "hi": -0.09})
        self.assertEqual((whole["rows"], whole["paths"]), (25, 25))
        self.assertEqual(res["verdict"], "PASS")

    def test_interval_resamples_paths_not_rows(self):
        # Path A: 3 rows at -0.01 each; path B: 1 row at +0.03. Ratio of sums: 0.
        rows = [{"asset": "Bitcoin", "window": "daily", "end": e} for e in (1, 1, 1, 2)]
        m = tr.boot(rows, [-0.01, -0.01, -0.01, 0.03])
        self.assertAlmostEqual(m["mean"], 0.0)
        self.assertEqual((m["lo"], m["hi"]), (-0.01, 0.03))

    def test_unchanged_rule_is_no_change(self):
        rows = fixture(25)
        res = tr.score(rows, [(0.6, 0.5)] * 25, [(0.6, 0.5)] * 25)
        self.assertEqual(res["verdict"], "NO CHANGE")

    def test_too_few_paths_fails(self):
        rows = fixture(10)
        res = tr.score(rows, [(0.6, 0.5)] * 10, [(0.6, 0.4)] * 10)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("differs on 10 paths, under 20", res["reasons"])

    def test_worse_rule_fails(self):
        rows = fixture(25)
        res = tr.score(rows, [(0.6, 0.4)] * 25, [(0.6, 0.5)] * 25)
        self.assertEqual(res["verdict"], "FAIL")


class CycleStillRuns(Offline):
    def test_touch_tool_cli_with_and_without_mid(self):
        args = [sys.executable, str(ROOT / "strategy" / "tools" / "touch.py"), "--spot", "100",
                "--barrier", "102", "--days", "1", "--ann-vol", "0.5",
                "--vol-source", "Binance 30d close vol, test"]
        plain = json.loads(subprocess.run(args, check=True, capture_output=True, text=True).stdout)
        self.assertNotIn("p_rule", plain)
        ruled = json.loads(subprocess.run(args + ["--mid", "0.05"], check=True,
                                          capture_output=True, text=True).stdout)
        self.assertEqual(ruled["p_touch"], plain["p_touch"])
        self.assertTrue(0.05 <= ruled["p_rule"] <= ruled["p_touch"])

    def test_replay_command_runs_offline(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            tr.main(["--start", "2026-10-18T00:00:00Z", "--end", "2026-10-20T04:00:00Z"])
        text = out.getvalue()
        self.assertIn("funnel: listed 3, parsed 2", text)
        self.assertRegex(text.splitlines()[-1], r"^touch-replay (PASS|FAIL|NO CHANGE): ")
        self.assertTrue(tr.CACHE.exists())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    unittest.main(argv=[sys.argv[0]], verbosity=2 if a.v else 1)
