#!/usr/bin/env python3
"""Offline tests for the variant and edge board.

PROTECTED CORE - the trading agent must not edit files under core/.

core/edge_board.py replays settled forecasts every cycle. These tests pin its
maths on hand-computed examples and prove its two guards: the reserved rows
reach nothing but a variant's verdict, and agent variants stay inside the rule
budget. Nothing touches the network or the real journal. CI runs it on every
push.

Usage: python3 core/test_edge_board.py
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
import edge_board  # noqa: E402
import pmapi  # noqa: E402
import score  # noqa: E402
import screen  # noqa: E402

START = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
NOW = START + dt.timedelta(days=30)  # sample() ends here, 14 of its 30 days reserved


def stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def row(i=0, est=0.6, mid=0.5, status="won", category="soccer", **over):
    """A forecast recorded i hours after START, settled an hour later."""
    t = START + dt.timedelta(hours=i)
    r = {"id": f"r{i}", "ts": stamp(t), "market_id": str(i), "question": "Q?",
         "outcome": "Yes", "end_date": stamp(t + dt.timedelta(hours=12)),
         "est_prob": est, "market_prob_at_record": mid,
         "best_bid_at_record": mid - 0.01, "best_ask_at_record": mid + 0.01,
         "liquidity_at_record": 5000.0, "category": category, "skip_reason": "no-edge",
         "status": status, "settled_ts": stamp(t + dt.timedelta(hours=1))}
    r.update(over)
    return r


def sample(n=120):
    """Gaps right about half the time, a row every 6 hours, one event a row."""
    rows = []
    for i in range(n):
        r = row(i * 6, est=0.6 if i % 2 else 0.4, status="won" if i % 4 in (0, 1) else "lost")
        r["end_date"] = stamp(START + dt.timedelta(days=i))
        rows.append(r)
    return rows


class Maths(unittest.TestCase):
    def test_cluster_ratio_matches_the_paired_test(self):
        # paired_rule_test is the same estimator at another critical value.
        rows = [{
            "status": "won" if i % 3 else "lost", "category": str(i), "end_date": "",
            "raw_prob": 0.5, "rule_prob": 0.5 + 0.01 * (i % 5)} for i in range(30)]
        paired = score.paired_rule_test(rows)
        y = [1.0 if r["status"] == "won" else 0.0 for r in rows]
        ratio = edge_board.cluster_ratio([
            (str(i), (r["rule_prob"] - y[i]) ** 2 - (r["raw_prob"] - y[i]) ** 2, 1.0)
            for i, r in enumerate(rows)])
        self.assertAlmostEqual(ratio["est"], paired["mean_delta"], places=4)
        ratio_width = ratio["hi"] - ratio["lo"]
        paired_width = paired["ci"][1] - paired["ci"][0]
        self.assertAlmostEqual(ratio_width / edge_board._t95(29),
                               paired_width / score._t_crit(29), places=3)

    def test_cluster_ratio_holds_back_an_interval_on_few_events(self):
        out = edge_board.cluster_ratio([(i, 1.0, 1.0) for i in range(9)])
        self.assertEqual(out["est"], 1.0)
        self.assertIsNone(out["lo"])

    def test_benjamini_hochberg(self):
        # Sorted 0.01, 0.04, 0.03 -> 0.01*3/1, 0.03*3/2, 0.04*3/3, monotone.
        self.assertEqual([round(q, 4) for q in
                          edge_board.benjamini_hochberg([0.01, 0.04, 0.03])],
                         [0.03, 0.04, 0.04])
        self.assertEqual(edge_board.benjamini_hochberg([None, 0.5]), [None, 0.5])

    def test_fit_shrink_is_least_squares_and_clipped(self):
        history = [{"est_prob": 0.6, "market_prob_at_record": 0.5, "won": True},
                   {"est_prob": 0.6, "market_prob_at_record": 0.5, "won": False}]
        # (0.1*0.5 + 0.1*-0.5) / 0.02 = 0: the gap carries nothing.
        self.assertEqual(edge_board.fit_shrink(history), 0.0)
        self.assertEqual(edge_board.fit_shrink(history[:1]), 1.0)  # 5.0 clipped
        self.assertEqual(edge_board.fit_shrink([]), 1.0)

    def test_fit_stack_moves_weight_to_the_informative_input(self):
        history = [{"est_prob": 0.8 if i % 2 else 0.2, "market_prob_at_record": 0.5,
                    "won": bool((i % 2) if i % 10 else not i % 2)} for i in range(200)]
        a, b = edge_board.fit_stack(history)
        self.assertGreater(b, 0.5)
        self.assertGreater(edge_board.predict_stack(
            {"est_prob": 0.8, "market_prob_at_record": 0.5}, (a, b)), 0.7)

    def test_taker_pnl_pays_the_fee_and_needs_the_edge(self):
        # Yes at 0.51 in a 5% family: fee 0.05*0.51*0.49 = 0.012495 a share.
        r = row(est=0.6)
        shares = 1 / (0.51 + 0.012495)
        self.assertAlmostEqual(edge_board.taker_pnl(r, 0.6), shares - 1, places=6)
        self.assertEqual(edge_board.taker_pnl({**r, "status": "lost"}, 0.6), -1.0)
        self.assertIsNone(edge_board.taker_pnl(r, 0.54))  # 3 cents over the ask

    def test_taker_pnl_buys_the_complement_at_one_minus_bid(self):
        # Bid 0.49, so No costs 0.51; the row lost, so No won.
        r = row(est=0.4, status="lost")
        self.assertGreater(edge_board.taker_pnl(r, 0.4), 0)
        self.assertEqual(edge_board.taker_pnl({**r, "status": "won"}, 0.4), -1.0)

    def test_taker_pnl_respects_the_protected_price_band(self):
        self.assertIsNone(edge_board.taker_pnl(
            row(mid=0.005, best_bid_at_record=0.001, best_ask_at_record=0.009), 0.5))

    def test_families_first_match_wins(self):
        for category, family in [("trump-mention", "say-the-word"),
                                 ("soccer", "sports-moneyline"),
                                 ("nfl-moneyline", "sports-moneyline"),
                                 ("mlb-totals", "sports-line"),
                                 ("soccer-transfer", "other"),
                                 ("econ-cpi", "econ-print"),
                                 ("Crypto-Touch", "crypto"),
                                 ("geopolitics-military", "politics/geopolitics")]:
            self.assertEqual(edge_board.family_of({"category": category}), family, category)

    def test_verdicts_follow_the_definitions(self):
        def stat(lo, hi, est=None):
            return {"est": est if est is not None else (lo + hi) / 2, "lo": lo, "hi": hi}
        none = {"est": None, "lo": None, "hi": None}
        flat = stat(-0.1, 0.1)
        v = edge_board.cell_verdict
        self.assertEqual(v(stat(0.1, 0.9), 0.5, 0.5, 0.05, flat, flat), "Real")
        self.assertEqual(v(stat(0.1, 0.9), 0.5, 0.5, 0.5, flat, flat), "Plausible")
        self.assertEqual(v(stat(-0.1, 0.9), 0.5, 0.5, 0.5, flat, stat(-0.2, -0.1)), "Plausible")
        self.assertEqual(v(stat(0.1, 0.9), -0.5, 0.5, 0.05, flat, flat), "Noise")
        self.assertEqual(v(stat(-0.9, -0.1), -0.5, -0.5, 0.05, flat, flat), "Negative")
        self.assertEqual(v(stat(-0.5, 0.6, 0.05), 0.1, -0.1, 0.9, stat(0.1, 0.2), flat), "Negative")
        self.assertEqual(v(none, 0.5, 0.5, None, none, none), "Noise")

    def test_allocation_never_prefers_a_thin_cell(self):
        cells = {"spread": [{"cell": ">10c", "verdict": "Real"},
                            {"cell": "<=1c", "verdict": "Plausible"},
                            {"cell": "5-10c", "verdict": "Negative"},
                            {"cell": "1-2c", "verdict": "Noise"}]}
        self.assertEqual(edge_board.allocation(cells),
                         {"prefer": ["spread=<=1c"], "skip": ["spread=5-10c"]})


class Moves(unittest.TestCase):
    def test_reads_the_mid_nearest_a_day_earlier(self):
        r = row(100, mid=0.5)
        t = START + dt.timedelta(hours=100)

        def seen(hours, mid):
            return {"ts": stamp(t - dt.timedelta(hours=hours)), "market_id": "100",
                    "mids": {"Yes": mid}}
        moves = edge_board.load_moves([r], [seen(19, 0.9), seen(25, 0.35), seen(12, 0.0)])
        self.assertAlmostEqual(moves["r100"], 0.15)

    def test_an_exact_ten_cent_move_counts_as_moved(self):
        rows = sample()
        moves = {r["id"]: abs(0.6 - 0.5) for r in rows}  # 0.09999999999999998
        cells = edge_board.edge_map(rows, moves, NOW)["move24h"]
        self.assertEqual([c["cell"] for c in cells], ["moved>=10c"])

    def test_no_sighting_in_the_window_is_no_move(self):
        r = row(100)
        t = START + dt.timedelta(hours=100)
        far = {"ts": stamp(t - dt.timedelta(hours=40)), "market_id": "100", "mids": {"Yes": 0.1}}
        other = {"ts": stamp(t - dt.timedelta(hours=24)), "market_id": "100", "mids": {"No": 0.1}}
        self.assertEqual(edge_board.load_moves([r], [far, other]), {})


class ReservedRows(unittest.TestCase):
    def test_the_split_is_by_record_time_and_never_moves_back(self):
        rows = sample()
        fold0, dev, reserved = edge_board.split_folds(rows, NOW)
        self.assertEqual(len(fold0) + len(dev) + len(reserved), len(rows))
        self.assertEqual(len(reserved), 56)
        self.assertLess(dev[-1]["ts"], edge_board.reserved_from(NOW))
        self.assertGreaterEqual(reserved[0]["ts"], edge_board.reserved_from(NOW))
        # An old row settling late adds to the older rows and reserves nothing old.
        extra = row(-1)
        _f, _d, after = edge_board.split_folds([extra] + rows, NOW)
        self.assertEqual(after, reserved)

    def test_a_fit_sees_only_rows_settled_before_its_fold(self):
        rows = sample()
        # This row is recorded early but settles after every fold has started.
        rows[0]["settled_ts"] = stamp(START + dt.timedelta(days=90))
        seen = {"trains": [], "tests": []}

        def fit(history):
            seen["trains"].append([h["id"] for h in history])
            self.assertTrue(all("won" in h and "status" not in h for h in history))
            seen["tests"].append([])
            return None

        def predict(row_, _state):
            for field in ("status", "outcome_won", "settled_ts", "won"):
                self.assertNotIn(field, row_)
            seen["tests"][-1].append(row_["id"])
            return None
        edge_board.walk_forward((fit, predict), rows, NOW)
        self.assertEqual(len(seen["trains"]), 5)
        self.assertFalse(any("r0" in t for t in seen["trains"]))
        by_id = {r["id"]: i for i, r in enumerate(rows)}
        for train, test in zip(seen["trains"], seen["tests"]):
            self.assertLess(max(by_id[i] for i in train), min(by_id[i] for i in test))

    def test_changing_reserved_outcomes_moves_only_the_verdict(self):
        rows = sample()
        before = edge_board.build(rows, [], {}, {}, [], NOW)
        flipped = [dict(r) for r in rows]
        _f0, _dev, reserved = edge_board.split_folds(flipped, NOW)
        for r in reserved:  # every gap now points the wrong way
            r["status"] = "lost" if r["est_prob"] > 0.5 else "won"
        after = edge_board.build(flipped, [], {}, {}, [], NOW)
        self.assertEqual(before["edge_map"], after["edge_map"])
        self.assertEqual(before["allocation"], after["allocation"])
        for b, a in zip(before["variants"], after["variants"]):
            self.assertEqual({k: v for k, v in b.items() if k != "reserved"},
                             {k: v for k, v in a.items() if k != "reserved"})
        verdict = {v["variant"]: v["reserved"] for v in before["variants"]}["shrink"]
        changed = {v["variant"]: v["reserved"] for v in after["variants"]}["shrink"]
        self.assertEqual(verdict["verdict"], "shadow")
        self.assertEqual(changed["verdict"], "pass")
        self.assertEqual(set(changed), {"rows", "n", "events", "verdict"})

    def test_reserved_outcomes_never_reach_the_change_flag(self):
        # The reserved rows settle after the as-of point and old long-dated rows
        # settle in the last day, which is what moved a positional boundary.
        rows = sample()
        for r in rows[:30]:
            r["settled_ts"] = stamp(NOW - dt.timedelta(hours=2))
        def flags(rs):
            cells = edge_board.edge_map(rs, {}, NOW)
            edge_board.flag_changes(cells, rs, {}, NOW)
            return [c.get("was") for table in cells.values() for c in table]
        flipped = [dict(r) for r in rows]
        _f0, _dev, reserved = edge_board.split_folds(flipped, NOW)
        for r in reserved:
            r["status"] = "lost" if r["est_prob"] > 0.5 else "won"
        self.assertEqual(flags(rows), flags(flipped))

    def test_the_verdict_counts_revised_rows_but_nothing_else_does(self):
        rows = sample()
        revised = [row(i * 6, est=0.7, status="won", id=f"rev{i}", superseded_by="x")
                   for i in range(100, 110)]
        with_rev = edge_board.variant_row("half", (None, lambda r, _s: (r["est_prob"] + 0.5) / 2),
                                          rows, NOW, revised)
        plain = edge_board.variant_row("half", (None, lambda r, _s: (r["est_prob"] + 0.5) / 2),
                                       rows, NOW)
        self.assertEqual(with_rev["reserved"]["n"], plain["reserved"]["n"] + 10)
        self.assertEqual(with_rev["vs_market"], plain["vs_market"])

    def test_the_paired_verdict_counts_only_reserved_rows_it_moved(self):
        rows = sample()
        out = edge_board.variant_row("half", (None, lambda r, _s: (r["est_prob"] + 0.5) / 2), rows, NOW)
        self.assertEqual(out["reserved"]["rows"], 56)
        self.assertEqual(out["reserved"]["n"], 56)
        same = edge_board.variant_row("same", (None, lambda r, _s: None), rows, NOW)
        self.assertEqual(same["reserved"]["n"], 0)

    def test_no_opinion_keeps_an_extreme_estimate_unmoved(self):
        rows = sample()
        rows[-1]["est_prob"] = 0.0005
        same = edge_board.variant_row("same", (None, lambda r, _s: None), rows, NOW)
        self.assertEqual(same["reserved"]["n"], 0)


class Budget(unittest.TestCase):
    def tagged(self, *names, last=NOW):
        return [row(i, rule=name, raw_prob=0.6, rule_prob=0.55, ts=stamp(last))
                for i, name in enumerate(names)]

    def test_rules_in_play_uses_the_idle_cutoff(self):
        idle = NOW - dt.timedelta(days=15)
        frows = self.tagged("fresh") + [row(9, rule="idle", raw_prob=0.6, rule_prob=0.55,
                                            ts=stamp(idle))]
        self.assertEqual(edge_board.rules_in_play(frows, NOW), ["fresh"])

    def test_variants_past_the_budget_are_refused(self):
        frows = self.tagged("r-a", "r-b", "r-c", "r-d", "r-e")
        variants = {"new-one": (None, lambda r, s: None), "new-two": (None, lambda r, s: None)}
        report = edge_board.build(sample(), frows, {}, variants, [], NOW)
        self.assertEqual(report["budget"]["agent_variants"], ["new-one"])
        self.assertEqual(report["budget"]["refused"], ["new-two"])
        self.assertEqual(report["budget"]["used"], 6)
        names = [v["variant"] for v in report["variants"]]
        self.assertEqual(names, ["raw", "shrink", "stack", "new-one"])

    def test_a_variant_named_after_a_tagged_rule_shares_its_slot(self):
        kept, refused, slots = edge_board.apply_budget(
            {"r-a": (None, None)}, ["r-a", "r-b", "r-c", "r-d", "r-e", "r-f"])
        self.assertEqual((list(kept), refused, len(slots)), (["r-a"], [], 6))


class AgentFile(unittest.TestCase):
    def load(self, source):
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "variants.py"
            path.write_text(source)
            return edge_board.load_agent_variants(path)

    def test_missing_file_is_no_variants(self):
        self.assertEqual(edge_board.load_agent_variants("/nonexistent/variants.py"), ({}, []))

    def test_loads_a_variant_and_skips_a_builtin_name(self):
        variants, notes = self.load(
            "VARIANTS = {'half-gap': (None, lambda r, s: None), 'shrink': (None, None)}\n")
        self.assertEqual(list(variants), ["half-gap"])
        self.assertIn("shrink", notes[0])

    def test_a_broken_file_never_stops_the_board(self):
        for source in ("this is not python", "import sys; sys.exit(3)", "X = 1\n",
                       "VARIANTS = {'a-b': 1}\n", "VARIANTS = 3\n"):
            variants, notes = self.load(source)
            self.assertEqual(variants, {}, source)
            self.assertIn("unusable", notes[0], source)

    def test_a_non_string_name_is_skipped(self):
        variants, notes = self.load("VARIANTS = {12: (None, None), 'ab': (None, None)}\n")
        self.assertEqual(list(variants), ["ab"])
        self.assertIn("12", notes[0])

    def test_a_slow_or_noisy_variant_is_contained(self):
        def spin(_history):
            while True:
                pass

        def noisy(row_, _state):
            print("debug")
            return None
        out = io.StringIO()
        with mock.patch.object(edge_board, "VARIANT_TIMEOUT_S", 1), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            report = edge_board.build(sample(), [], {},
                                      {"spin": (spin, None), "noisy": (None, noisy)}, [], NOW)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("noisy", [v["variant"] for v in report["variants"]])
        self.assertTrue(any("spin" in n and "TimeoutError" in n for n in report["notes"]))

    def test_a_failing_variant_costs_only_itself(self):
        def boom(_history):
            raise SystemExit(1)
        bad_prob = (None, lambda r, s: 7.0)
        report = edge_board.build(sample(), [], {}, {"boom": (boom, None), "bad-prob": bad_prob},
                                  [], NOW)
        self.assertEqual([v["variant"] for v in report["variants"]], ["raw", "shrink", "stack"])
        self.assertEqual(len(report["notes"]), 2)
        self.assertTrue(report["edge_map"])


class Board(unittest.TestCase):
    def test_settled_rows_split_live_from_revised(self):
        frows = [row(3), row(2), row(4, status="open"), row(5, status="void"),
                 row(6, superseded_by="x"), row(7, best_bid_at_record=None),
                 row(8, liquidity_at_record=1.0)]
        live, revised = edge_board.settled_rows(frows)
        self.assertEqual([r["id"] for r in live], ["r2", "r3"])
        self.assertEqual([r["id"] for r in revised], ["r6"])

    def test_too_few_rows_says_so(self):
        report = edge_board.build(sample(10), [], {}, {}, [], NOW)
        self.assertEqual(report["variants"], [])
        self.assertIn("only 10", report["notes"][0])

    def test_shrink_beats_raw_on_an_overconfident_ledger(self):
        # Gaps that are right 55% of the time on a 40-cent claim: a shrink helps.
        rows = [row(i, est=0.9 if i % 2 else 0.1,
                    status=("won" if i % 2 else "lost") if i % 20 < 11
                    else ("lost" if i % 2 else "won"))
                for i in range(240)]
        # Keeps 144 of the 240 hourly rows older than the reserved window.
        now = START + dt.timedelta(hours=144 + 14 * 24)
        report = edge_board.build(rows, [], {}, {}, [], now)
        shrink = next(v for v in report["variants"] if v["variant"] == "shrink")
        self.assertLess(shrink["vs_raw"]["est"], 0)

    def test_a_verdict_change_in_the_last_day_is_flagged(self):
        # Sports gaps start right, then old rows settling in the last day flip
        # the cell. This now is far past every record, so nothing here is reserved.
        now = START + dt.timedelta(days=200)
        old = [row(i, est=0.7, status="won") if i % 3 else row(i, est=0.3, status="lost")
               for i in range(180)]
        for i, r in enumerate(old):
            r["end_date"] = stamp(START + dt.timedelta(days=i))
            r["settled_ts"] = stamp(now - dt.timedelta(days=30))
        self.assertEqual(edge_board.edge_map(old, {}, now)["family"][0]["verdict"], "Real")
        recent = [row(i, est=0.7, status="lost") if i % 3 else row(i, est=0.3, status="won")
                  for i in range(180, 900)]
        for i, r in enumerate(recent, 180):
            r["end_date"] = stamp(START + dt.timedelta(days=i))
            r["settled_ts"] = stamp(now - dt.timedelta(hours=1))
        rows = old + recent
        cells = edge_board.edge_map(rows, {}, now)
        self.assertNotEqual(cells["family"][0]["verdict"], "Real")
        edge_board.flag_changes(cells, rows, {}, now)
        self.assertEqual(cells["family"][0]["was"], "Real")

    def test_main_stays_offline_and_writes_the_allocation_line(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            forecasts = root / "forecasts.jsonl"
            forecasts.write_text("\n".join(json.dumps(r) for r in sample()) + "\n")
            allocation = root / "reports" / "line.txt"
            out = io.StringIO()
            with mock.patch.object(edge_board.forecast, "FORECASTS", forecasts), \
                    mock.patch.object(edge_board, "ALLOCATION_FILE", allocation), \
                    mock.patch.object(edge_board, "VARIANTS_FILE", root / "absent.py"), \
                    mock.patch.object(screen, "log_rows", lambda: iter(())), \
                    mock.patch.object(pmapi.urllib.request, "urlopen",
                                      side_effect=AssertionError("network")), \
                    contextlib.redirect_stdout(out):
                self.assertEqual(edge_board.main([], NOW), 0)
            text = out.getvalue()
            self.assertIn("edge board: 120 settled rows", text)
            self.assertIn("reserved verdict", text)
            self.assertTrue(allocation.read_text().startswith("allocation: prefer "))

    def test_a_failed_run_leaves_no_allocation_line(self):
        with tempfile.TemporaryDirectory() as d:
            allocation = pathlib.Path(d) / "line.txt"
            allocation.write_text("allocation: prefer stale; skip none\n")
            with mock.patch.object(edge_board, "ALLOCATION_FILE", allocation), \
                    mock.patch.object(edge_board.forecast, "read_forecasts",
                                      side_effect=ValueError("bad row")):
                with self.assertRaises(ValueError):
                    edge_board.main([], NOW)
            self.assertFalse(allocation.exists())

    def test_screen_repeats_the_line_and_tolerates_its_absence(self):
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "line.txt"
            with mock.patch.object(screen, "EDGE_BOARD_ALLOCATION", path):
                self.assertIsNone(screen.edge_board_allocation())
                path.write_text("allocation: prefer none; skip none\n")
                self.assertEqual(screen.edge_board_allocation(),
                                 "allocation: prefer none; skip none")


if __name__ == "__main__":
    unittest.main()
