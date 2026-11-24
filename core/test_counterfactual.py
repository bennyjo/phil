#!/usr/bin/env python3
"""Offline tests for where `core/counterfactual.py reconcile` finds the
frozen outside-view-veto hand table.

PROTECTED CORE - the trading agent must not edit files under core/.

Playbook compaction moves text from strategy/playbook.md to
strategy/archive/*.md. The frozen hand table must parse the same wherever
it lands, and a table left in two places (or lost) must stop reconcile
rather than double-count or report zero rows. Each test works in a
temporary directory, and the last one checks the real strategy docs still
hold exactly one table. CI runs it on every push.

Usage: python3 core/test_counterfactual.py
"""
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import counterfactual  # noqa: E402

SECTION = "## Outside-view veto: settled counterfactual ledger (DEEP-2026-08-15)"
TABLE = """### Frozen hand table (all rows, original order)

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| SC Nordone (57f222efb516) | 0.33 / 0.595 | No | +0.260 | Yes | −1.00 |
| WTI above $90 Sep 30 (`853c6998ca45`, WSV) | 0.88 / 0.925 | No | -0.010 | Yes | -5.00 |
| ISM PMI 55.0-55.9 Sep (`4b0493d215d6`, WSV) | 0.283 / 0.395 | No | +0.077 | No | +2.81 |
| AI Arena 1530 by Sep 30 (`a93c997dbdf5`) | 0.93 / 0.891 | Yes | -0.022 | Yes | refused (entry 0.952) |
| prose-only row (9618a7d0872d) | see archive | No | +0.06 | No | **+0.22** |
"""
LIVE_RULES = f"""{SECTION}

The hand table is FROZEN; settlement retros cite the mechanical totals.

### Live rules carried over from the archived narrative

**Append discipline:** a settled veto batch appends only its table rows.
"""
NEXT = "## 2026-10-05 05:27Z: one distribution per event\n\nUnrelated rule.\n"
# The archive already holds a verbatim copy of the old section under the
# same section heading; it has table rows but no frozen-table heading.
OLD_NARRATIVE = f"""# Archived: OVV counterfactual-ledger narrative (verbatim)

{SECTION}

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| SC Nordone (57f222efb516) | 0.33 / 0.595 | No | +0.260 | Yes | −1.00 |
"""


class FrozenTableLocation(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        self.playbook = self.root / "strategy" / "playbook.md"
        self.archive = self.root / "strategy" / "archive"
        self.archive.mkdir(parents=True)
        (self.archive / "ovv-ledger-narrative-2026-08-15-to-2026-10-07.md").write_text(OLD_NARRATIVE)
        for name, value in (("ROOT", self.root), ("PLAYBOOK", self.playbook),
                            ("ARCHIVE_DIR", self.archive)):
            patcher = mock.patch.object(counterfactual, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def rows(entries):
        return [{k: v for k, v in e.items() if k != "line"} for e in entries]

    def test_table_in_playbook(self):
        self.playbook.write_text(f"# Playbook\n\n{LIVE_RULES}\n{TABLE}\n{NEXT}")
        entries, stated, meta = counterfactual.parse_playbook()
        self.assertEqual(meta["source"], "strategy/playbook.md")
        self.assertEqual([e["id"] for e in entries], ["57f222efb516", "853c6998ca45",
                                                       "4b0493d215d6", "a93c997dbdf5",
                                                       "9618a7d0872d"])
        self.assertEqual(entries[0]["pnl"], -1.0)
        self.assertIsNone(entries[3]["pnl"])  # a refused row is a non-trade
        self.assertEqual(entries[4]["pnl"], 0.22)
        self.assertEqual(self.playbook.read_text().splitlines()[entries[0]["line"] - 1][:12],
                         "| SC Nordone")
        self.assertIsNone(stated)

    def test_table_moved_to_archive_parses_the_same(self):
        self.playbook.write_text(f"# Playbook\n\n{LIVE_RULES}\n{TABLE}\n{NEXT}")
        before, _, _ = counterfactual.parse_playbook()
        moved = self.archive / "playbook-narrative-ovv-frozen-table.md"
        moved.write_text(f"# Archived: frozen OVV hand table\n\n{TABLE}")
        self.playbook.write_text(f"# Playbook\n\n{LIVE_RULES}\n{NEXT}")
        after, _, meta = counterfactual.parse_playbook()
        self.assertEqual(meta["source"], "strategy/archive/playbook-narrative-ovv-frozen-table.md")
        self.assertEqual(self.rows(after), self.rows(before))
        self.assertEqual(moved.read_text().splitlines()[after[0]["line"] - 1][:12], "| SC Nordone")
        self.assertIn(moved, counterfactual.strategy_docs())

    def test_table_in_two_places_stops(self):
        self.playbook.write_text(f"# Playbook\n\n{LIVE_RULES}\n{TABLE}\n{NEXT}")
        (self.archive / "copy.md").write_text(TABLE)
        with self.assertRaises(SystemExit) as cm:
            counterfactual.parse_playbook()
        self.assertIn("found 2", str(cm.exception.code))
        self.assertIn("strategy/archive/copy.md:1", str(cm.exception.code))

    def test_no_table_stops(self):
        self.playbook.write_text(f"# Playbook\n\n{LIVE_RULES}\n{NEXT}")
        with self.assertRaises(SystemExit) as cm:
            counterfactual.parse_playbook()
        self.assertIn("found 0", str(cm.exception.code))


class RealStrategyDocs(unittest.TestCase):
    def test_exactly_one_frozen_table(self):
        entries, _, meta = counterfactual.parse_playbook()
        self.assertTrue(meta["source"].startswith("strategy/"))
        self.assertGreater(len(entries), 0)


if __name__ == "__main__":
    unittest.main()
