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
import math
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


def market(id_, question, start="2026-10-19T04:00:12Z"):
    return {"id": id_, "question": question, "version": "v1",
            "endDate": "2026-10-20T04:00:00Z", "startDate": start,
            "outcomes": json.dumps(["Yes", "No"]), "outcomePrices": json.dumps(["0", "1"]),
            "clobTokenIds": json.dumps([f"{id_}-yes", f"{id_}-no"])}


class FakeAPI:
    """Serves the three endpoints; a windowed price read gets the payout.
    The as_of answer's mid is `price`, `age` seconds old at t."""

    def __init__(self, markets=MARKETS):
        self.hist_calls, self.markets = [], markets
        self.price, self.age, self.fail = 0.30, 0, False

    def __call__(self, url, params=None):
        if url == tr.KEYSET:
            return {"markets": self.markets, "next_cursor": None}
        if url == tr.KLINES:
            t0 = params["startTime"] // 1000
            return [bar(t, params["symbol"]) for t in range(t0, min(END, t0 + 1000 * H), H)]
        if url == tr.HIST:
            self.hist_calls.append(dict(params))
            if self.fail:
                raise RuntimeError("GET prices-history failed after 3 tries")
            if "as_of" not in params:            # what the real API does to a window
                return {"data": [{"timestamp": params["end"] - 60, "price": 1.0,
                                  "resolution_seconds": 0}]}
            t = params["as_of"]
            return {"data": [
                {"timestamp": t - 300 - self.age, "price": self.price, "resolution_seconds": 300},
                {"timestamp": t - 60, "price": 0.99, "resolution_seconds": 300},  # ends after t
            ]}
        raise AssertionError(f"unexpected url {url}")


class Offline(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()
        self.saved = tr.http, tr.HIST_INTERVAL_S, tr.CACHE, tr.RUNS
        self.tmp = tempfile.TemporaryDirectory()
        tr.http, tr.HIST_INTERVAL_S = self.api, 0.0
        tr.CACHE = pathlib.Path(self.tmp.name) / "touch-prices.jsonl"
        tr.RUNS = pathlib.Path(self.tmp.name) / "runs.jsonl"

    def tearDown(self):
        tr.http, tr.HIST_INTERVAL_S, tr.CACHE, tr.RUNS = self.saved
        self.tmp.cleanup()

    def rule(self, source):
        path = pathlib.Path(self.tmp.name) / "rule.py"
        path.write_text(source)
        return path


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

    def test_cached_lookahead_point_is_dropped(self):
        tr.CACHE.write_text(
            json.dumps({"token": "btc-yes", "as_of": SPIKE,
                        "point": {"timestamp": SPIKE - 60, "price": 0.5,
                                  "resolution_seconds": 300}}) + "\n"
            + json.dumps({"token": "btc-yes", "as_of": SPIKE,      # a later line can't override
                          "point": {"timestamp": SPIKE - 600, "price": 0.4,
                                    "resolution_seconds": 300}}) + "\n")
        rows, funnel = tr.build_rows(WSTART - 86400, END, 600)
        self.assertEqual([r for r in rows if r["asset"] == "Bitcoin"], [])
        self.assertEqual(funnel["unpriced"], 1)
        self.assertNotIn({"token_id": "btc-yes", "as_of": SPIKE}, self.api.hist_calls)

    def test_stale_and_out_of_band_mids_are_dropped(self):
        for age, price, kept, dropped in ((600, 0.30, 4, None), (601, 0.30, 0, "stale"),
                                          (0, 0.97, 0, "outside_band"),
                                          (0, 0.04, 0, "outside_band")):
            with self.subTest(age=age, price=price):
                tr.CACHE.unlink(missing_ok=True)
                self.api.age, self.api.price = age, price
                rows, funnel = tr.build_rows(WSTART - 86400, END, 600)
                self.assertEqual(len(rows), kept)
                if dropped:
                    self.assertEqual(funnel[dropped], 4)

    def test_touched_dip_and_times_before_creation_are_dropped(self):
        self.api.markets = [market("a", "Will Ethereum dip to $4,036 on October 19?"),
                            market("b", "Will Ethereum dip to $4,000 on October 19?",
                                   start="2026-10-19T16:30:00Z")]
        rows, _ = tr.build_rows(WSTART - 86400, END, 600)
        # a: every bar's low (4035.96) is at or under the barrier, so it was
        # touched before any forecast time. b: 6 h and 12 h precede creation.
        self.assertEqual([(r["market_id"], r["t"]) for r in rows], [("b", WSTART + 18 * H)])

    def test_forecast_times_are_offsets_from_the_window_start(self):
        day = {"window": "daily", "wstart": WSTART, "end": WSTART + 20 * H}
        self.assertEqual(tr.forecast_times(day), [WSTART + h * H for h in (6, 12, 18)])
        month = {"window": "monthly", "wstart": WSTART, "end": WSTART + 31 * 86400}
        self.assertEqual(tr.forecast_times(month), [WSTART + d * 86400 for d in (3, 10, 17, 24)])
        month["end"] = WSTART + 12 * 86400            # resolved early: later times are gone
        self.assertEqual(tr.forecast_times(month), [WSTART + d * 86400 for d in (3, 10)])

    def test_vol_reads_only_closes_by_t(self):
        day0 = ts("2026-10-19T00:00:00Z")
        k = {o: (0, 0, 100.0 * (1.02 if (o // 86400) % 2 else 1.0)) for o in
             range(day0 - 40 * 86400, day0 + 3 * H, H)}
        k[day0] = (0, 0, 1e6)                        # bar 00:00-01:00Z, open at t
        t = day0 + 30 * 60
        closed = {o: b for o, b in k.items() if o + H <= t}
        self.assertEqual(tr.vol30(k, t), tr.vol30(closed, t))
        # 30 daily returns alternating +-ln 1.02: mean 0, sample sd ln 1.02 * sqrt(30/29).
        self.assertAlmostEqual(tr.vol30(k, t), math.log(1.02) * math.sqrt(30 / 29 * 365))

    def test_parse_market_outcome_and_window(self):
        parse = tr.parse_market
        yes = market("1", "Will Bitcoin reach $110,000 on October 19?")
        yes["outcomePrices"] = json.dumps(["1", "0"])
        self.assertEqual(parse(yes)["y"], 1.0)
        self.assertEqual(parse(market("1", "Will Bitcoin reach $110,000 on October 19?"))["y"], 0.0)
        half = dict(yes, outcomePrices=json.dumps(["0.5", "0.5"]))
        self.assertIsNone(parse(half))
        monthly = dict(yes, question="Will XRP dip to $1.20 in October?",
                       endDate="2026-11-01T04:00:00Z")
        got = parse(monthly)
        self.assertEqual((got["window"], got["wstart"], got["barrier"], got["kind"]),
                         ("monthly", ts("2026-10-01T04:00:00Z"), 1.2, "dip to"))
        for q in ("Will Bitcoin reach $110,000 on October?",
                  "Will Bitcoin reach $110,000 in October 19?"):
            self.assertIsNone(parse(dict(yes, question=q)))


class RuleIsolation(Offline):
    ROWS = [{"t": t, "spot": 100.0, "barrier": 102.0, "days": 1.0, "ann_vol": 0.5, "mid": 0.3,
             "y": 1.0, "market_id": "1"} for t in (30, 20, 10)]

    def test_rule_cannot_find_the_outcome_in_its_process(self):
        rule = self.rule(
            "import sys\n"
            "def estimate(raw, mid, row):\n"
            "    f = sys._getframe(1)\n"
            "    while f:\n"
            "        for v in list(f.f_locals.values()) + list(f.f_globals.values()):\n"
            "            for x in v if isinstance(v, list) else [v]:\n"
            "                if isinstance(x, dict) and 'y' in x:\n"
            "                    return 0.9 * x['y'] + 0.05\n"
            "        f = f.f_back\n"
            "    return raw\n")
        out = tr.evaluate(self.ROWS, (ROOT / tr.TOOL, rule))   # skip check_rule on purpose
        self.assertEqual([p for _, p in out], [raw for raw, _ in out])

    def test_rows_are_priced_in_forecast_time_order(self):
        rule = self.rule("n = 0\ndef estimate(raw, mid, row):\n    global n\n    n += 1\n"
                         "    return n / 10\n")
        out = tr.evaluate(self.ROWS, tr.load_side(ROOT / tr.TOOL, rule))
        self.assertEqual([p for _, p in out], [0.3, 0.2, 0.1])   # rows given latest first

    def test_rule_may_use_only_its_arguments_and_math(self):
        tr.check_rule(ROOT / tr.RULE)
        tr.check_rule(self.rule("import math\nfrom math import erf\n"
                                "def estimate(raw, mid, row):\n"
                                "    return min(1.0, max(0.0, erf(math.exp(raw) - 1)\n"
                                "                        + 0 * row['days']))\n"))
        for body in ("import sys", "import os.path", "from os import path", "import math as m",
                     "from . import touch", "x = (1).__class__", "x = raw.real", "f = open",
                     "x = __builtins__", "x = getattr(1, 'real')", "math = 1",
                     "def g(math): pass", "match raw:\n    case float(real=r): pass"):
            with self.subTest(body=body), self.assertRaises(ValueError):
                tr.check_rule(self.rule("import math\ndef estimate(raw, mid, row):\n"
                                        f"    return raw\n{body}\n"))
        with self.assertRaises(ValueError):                     # the replay loads sides checked
            tr.load_side(ROOT / tr.TOOL, self.rule("import os\ndef estimate(raw, mid, row):\n"
                                                   "    return raw\n"))

    def test_rule_errors_stop_the_replay(self):
        for body in ("return 1.5", "return None", "raise KeyError('x')"):
            with self.subTest(body=body), self.assertRaises(ValueError):
                rule = self.rule(f"def estimate(raw, mid, row):\n    {body}\n")
                tr.evaluate(self.ROWS, (ROOT / tr.TOOL, rule))


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

    def gate(self, cands, **kw):
        """Score 100 paths a day apart; current records 0.5, candidate cands[i]."""
        rows = fixture(len(cands))
        return tr.score(rows, [(0.6, 0.5)] * len(rows), [(0.6, c) for c in cands], **kw)

    # With y = 0 and current 0.5, candidate 0.4 is -0.09 paired, 0.6 is +0.11.
    # Folds hold rows 0-24, 25-49, 50-74, 75-99; the 14-day holdout rows 86-99.

    def test_worse_rule_fails(self):
        res = self.gate([0.6] * 100)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertEqual(len(res["reasons"]), 3)

    def test_losing_holdout_fails(self):
        res = self.gate([0.4] * 86 + [0.6] * 14)
        self.assertLess(res["slices"][0]["paired"]["hi"], 0)
        self.assertEqual(res["reasons"], ["holdout mean +0.1100 is above zero"])

    def test_two_losing_folds_fail(self):
        res = self.gate([0.55] * 50 + [0.0] * 50)
        self.assertLess(res["slices"][0]["paired"]["hi"], 0)
        self.assertEqual(res["reasons"], ["only 2 of 4 folds at or below zero"])

    def test_three_winning_folds_pass(self):
        res = self.gate([0.55] * 25 + [0.0] * 75)
        self.assertEqual((res["verdict"], res["folds_ok"]), ("PASS", 3))

    def test_interval_spanning_zero_fails(self):
        res = self.gate([0.4 if i % 2 == 0 else math.sqrt(0.33) for i in range(100)])
        whole = res["slices"][0]["paired"]
        self.assertLess(whole["mean"], 0)
        self.assertEqual(res["reasons"], [f"whole-window interval upper bound "
                                          f"{whole['hi']:+.4f} is not below zero"])

    def test_failed_price_reads_fail(self):
        self.assertEqual(self.gate([0.4] * 100, fetch_errors=2)["reasons"],
                         ["2 price reads failed; rerun"])
        self.assertEqual(self.gate([0.5] * 100, fetch_errors=2)["verdict"], "FAIL")


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

    def run_replay(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            tr.main(["--start", "2026-10-18T00:00:00Z", "--end", "2026-10-20T04:00:00Z"])
        return out.getvalue()

    def test_replay_command_runs_offline_and_logs_the_run(self):
        text = self.run_replay()
        self.assertIn("funnel: listed 3, parsed 2", text)
        line = text.splitlines()[-1]
        self.assertTrue(line.startswith("touch-replay NO CHANGE: "), line)
        head, tool, rule = (tr.git_out("rev-parse", "HEAD"), tr.git_out("hash-object", tr.TOOL),
                            tr.git_out("hash-object", tr.RULE))
        self.assertTrue(line.endswith(f"baseline {head[:12]}, candidate touch.py {tool[:12]} "
                                      f"touch_rule.py {rule[:12]}"), line)
        self.assertTrue(tr.CACHE.exists())
        self.run_replay()
        runs = [json.loads(x) for x in tr.RUNS.read_text().splitlines()]
        self.assertEqual(len(runs), 2)
        self.assertEqual((runs[0]["gate"], runs[0]["baseline"], runs[0]["touch_rule.py"]),
                         (line, head, rule))

    def test_failed_price_reads_fail_the_run(self):
        self.api.fail = True
        line = self.run_replay().splitlines()[-1]
        self.assertTrue(line.startswith("touch-replay FAIL: "), line)
        self.assertIn("4 price reads failed; rerun", line)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    unittest.main(argv=[sys.argv[0]], verbosity=2 if a.v else 1)
