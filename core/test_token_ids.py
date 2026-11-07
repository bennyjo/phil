#!/usr/bin/env python3
"""Offline tests for the Gamma token-id guard in core/pmapi.py and core/scan.py.

PROTECTED CORE - the trading agent must not edit files under core/.

The market's Gamma version alone selects its outcome ids: clobTokenIds for
v1, positionIds for v2. A market with no supported version or unusable ids
is skipped, so one bad record cannot kill the whole scan. Scan lists and tags
V2 markets. Phil bets binary V2 markets; core/ledger.py and core/real.py refuse
every other V2 market. These tests feed Gamma records and books, hand-built or
recorded, so nothing touches the network. CI runs it on every push.

Usage: python3 core/test_token_ids.py
"""
import argparse
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

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


# The shape Gamma returns live: positionIds is an array, and clobTokenIds may
# be populated too, so only the version may select between them.
V2 = {"version": "v2", "clobTokenIds": json.dumps(["777", "666"]), "positionIds": ["9", "8"]}


class TokenIds(unittest.TestCase):
    def test_v1_reads_clob_token_ids(self):
        self.assertEqual(pmapi.token_ids(gamma()), ["111", "222"])
        self.assertEqual(pmapi.market_tokens(gamma()), {"Yes": "111", "No": "222"})

    def test_untagged_market_is_rejected(self):
        # docs.polymarket.com/migrate/polymarket-v2/api-integrations:
        # "Reject missing or unsupported versions"
        m = gamma()
        del m["version"]
        self.assertIsNone(pmapi.token_ids(m))
        self.assertIsNone(pmapi.market_tokens(m))

    def test_unknown_version_is_rejected(self):
        self.assertIsNone(pmapi.token_ids(gamma(version="v3")))

    def test_v2_reads_position_ids(self):
        # docs.polymarket.com/migrate/polymarket-v2/api-integrations: "Choose
        # the ID field by `version`, even when both fields are present".
        self.assertEqual(pmapi.token_ids(gamma(**V2)), ["9", "8"])
        self.assertEqual(pmapi.market_tokens(gamma(**V2)), {"Yes": "9", "No": "8"})

    def test_unusable_ids_are_unsupported(self):
        for ids in (None, "", "not json", json.dumps([]), json.dumps(["111"]),
                    json.dumps({"Yes": "111"})):
            with self.subTest(ids=ids):
                self.assertIsNone(pmapi.token_ids(gamma(clobTokenIds=ids)))
        for ids in (None, [], ["9"]):
            with self.subTest(position_ids=ids):
                self.assertIsNone(pmapi.token_ids(gamma(**dict(V2, positionIds=ids))))


class Tradable(unittest.TestCase):
    RECORDED = json.loads((pathlib.Path(__file__).resolve().parent / "fixtures"
                           / "polymarket_v2.json").read_text())["gamma"]

    def test_position_module_is_the_first_byte_of_the_id(self):
        # docs.polymarket.com/trading/positions/how-positions-work: 1 BinaryModule,
        # 2 NegRiskModule, 3 CombinatorialModule.
        binary, neg_risk = self.RECORDED["binary_open"], self.RECORDED["neg_risk_open"]
        self.assertEqual(pmapi.position_module(binary["positionIds"][0]), 1)
        self.assertEqual(pmapi.position_module(neg_risk["positionIds"][0]), 2)
        self.assertEqual(pmapi.position_module(str(3 << 248)), 3)

    def test_non_decimal_position_id_has_no_module(self):
        for bad in ("0x01", "", "1e5", None, "١"):
            with self.subTest(bad=bad):
                self.assertIsNone(pmapi.position_module(bad))

    def test_recorded_binary_v2_markets_are_tradable(self):
        for name in ("binary_open", "binary_closed"):
            with self.subTest(market=name):
                self.assertTrue(pmapi.tradable(self.RECORDED[name]))

    def test_recorded_neg_risk_v2_market_is_not(self):
        self.assertFalse(pmapi.tradable(self.RECORDED["neg_risk_open"]))

    def test_neg_risk_flag_alone_refuses_a_v2_market(self):
        self.assertFalse(pmapi.tradable(dict(self.RECORDED["binary_open"], negRisk=True)))

    def test_v2_market_with_unusable_ids_is_not(self):
        binary = self.RECORDED["binary_open"]
        for ids in (None, [], ["9", "8"], [binary["positionIds"][0], "0x01"]):
            with self.subTest(ids=ids):
                self.assertFalse(pmapi.tradable(dict(binary, positionIds=ids)))

    def test_v1_stays_tradable_whatever_its_neg_risk_flag(self):
        self.assertTrue(pmapi.tradable(gamma()))
        self.assertTrue(pmapi.tradable(gamma(negRisk=True)))

    def test_unknown_or_missing_version_is_not(self):
        self.assertFalse(pmapi.tradable(gamma(version="v3")))
        self.assertFalse(pmapi.tradable(gamma(version=None)))


class Listing(unittest.TestCase):
    def listed_url(self, **params):
        urls = []

        class Reply(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *_exc):
                return False

        def urlopen(req, timeout):
            urls.append(req.full_url)
            return Reply(b"[]")

        with mock.patch.object(pmapi.urllib.request, "urlopen", urlopen):
            pmapi.gamma_markets(**params)
        return urls[0]

    def test_listing_asks_for_both_versions(self):
        # docs.polymarket.com/market-data/discover-markets: "Repeat the
        # parameter as `version=v1&version=v2` to include both. [...] Omission
        # uses the current server default of CTF events (v1)."
        self.assertIn("version=v1&version=v2", self.listed_url(limit=100))

    def test_caller_can_ask_for_one_version(self):
        url = self.listed_url(version="v2")
        self.assertIn("version=v2", url)
        self.assertNotIn("version=v1", url)


def book(token, bids=(), asks=()):
    return {"asset_id": token, "bids": list(bids), "asks": list(asks)}


class ScanKeep(unittest.TestCase):
    def setUp(self):
        scan.UNSUPPORTED.clear()
        self.args = argparse.Namespace(min_volume_24h=0)

    def test_records_are_tagged_with_their_version(self):
        seen = set()
        v1 = scan.keep(gamma(id="1"), seen, [], self.args)
        v2 = scan.keep(gamma(id="2", **V2), seen, [], self.args)
        self.assertEqual((v1["version"], v1["clob_token_ids"]), ("v1", ["111", "222"]))
        self.assertEqual((v2["version"], v2["clob_token_ids"]), ("v2", ["9", "8"]))
        self.assertFalse(scan.UNSUPPORTED)

    def test_unsupported_version_is_skipped_not_fatal(self):
        seen = set()
        self.assertIsNone(scan.keep(gamma(id="2", version="v3"), seen, [], self.args))
        rec = scan.keep(gamma(id="3"), seen, [], self.args)
        self.assertEqual(rec["clob_token_ids"], ["111", "222"])
        self.assertEqual(dict(scan.UNSUPPORTED), {"v3": 1})


class ScanMain(unittest.TestCase):
    """scan.py end to end, with Gamma and the CLOB stubbed."""

    def setUp(self):
        scan.UNSUPPORTED.clear()
        scan.LISTED.clear()
        scan.V2_BOOKS.clear()
        scan.BOOKS.clear()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.books_dir = pathlib.Path(tmp.name)

    def scan(self, books, rows_for=None):
        self.calls = []

        def gamma_markets(**params):
            self.calls.append(params)
            if params["offset"]:
                return []
            if rows_for:
                return rows_for(params)
            if params.get("version") == "v2":
                return [gamma(id="20", **V2)]
            return [gamma(id="10"), gamma(id="20", **V2)]

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["scan.py"]), \
                mock.patch.object(scan, "discovery_queries",
                                  lambda *_a: [{"_label": "q", "closed": "false"}]), \
                mock.patch.object(pmapi, "gamma_markets", gamma_markets), \
                mock.patch.object(pmapi, "clob_books", books), \
                mock.patch.object(scan.archive, "BOOKS_DIR", self.books_dir), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            scan.main()
        return [json.loads(line) for line in out.getvalue().splitlines()], err.getvalue()

    def test_scan_archives_the_book_fields_it_read(self):
        recs, _ = self.scan(lambda tokens: [book("9", bids=[{"price": "0.4", "size": "100"}]),
                                            book("8")])
        (path,) = self.books_dir.iterdir()
        (row,) = [json.loads(x) for x in path.read_text().splitlines()]
        self.assertEqual(set(row["books"]), {r["market_id"] for r in recs})

    def test_failed_book_archive_leaves_the_scan_output_alone(self):
        good, _ = self.scan(lambda tokens: [book("9", bids=[{"price": "0.4", "size": "100"}]),
                                            book("8")])
        self.setUp()
        self.books_dir = self.books_dir / "blocked"
        self.books_dir.write_text("")
        got, err = self.scan(lambda tokens: [book("9", bids=[{"price": "0.4", "size": "100"}]),
                                             book("8")])
        self.assertEqual(got, good)
        self.assertIn("archive: books not saved", err)

    def test_v2_market_with_orders_flows_through_tagged(self):
        recs, err = self.scan(lambda tokens: [book("9", bids=[{"price": "0.4", "size": "100"}]),
                                              book("8")])
        self.assertEqual({r["market_id"]: r["version"] for r in recs},
                         {"10": "v1", "20": "v2"})
        self.assertIn("v2 markets kept: 1,", err)

    def test_empty_v2_book_is_dropped_and_counted(self):
        # Empty V2 books carry placeholder 0.5/0.5 prices, which pass keep()
        # and would spend screener slots that V1 markets get today.
        recs, err = self.scan(lambda tokens: [book(t) for t in tokens])
        self.assertEqual([r["market_id"] for r in recs], ["10"])
        self.assertIn("dropped for an empty book: 1", err)

    def thin_books(self, yes_bids, no_bids):
        return lambda tokens: [
            book("9", bids=[{"price": p, "size": s} for p, s in yes_bids]),
            book("8", bids=[{"price": p, "size": s} for p, s in no_bids])]

    def test_placeholder_book_with_orders_is_dropped_as_thin(self):
        # Spurs vs. Suns, live on 2026-11-07: orders on both sides, 0.5/0.5 prices,
        # and $0.48 of bids against Gamma's liquidityNum 0.4788.
        recs, err = self.scan(self.thin_books([("0.12", "1.26")], [("0.12", "2.73")]))
        self.assertEqual([r["market_id"] for r in recs], ["10"])
        self.assertIn("v2 markets kept: 0, dropped for a thin book (under $25): 1", err)
        self.assertIn("dropped for an empty book: 0", err)

    def test_depth_sums_the_bids_of_every_token_against_the_placeholder_line(self):
        # Each side alone is under $25. Heat vs. Kings held 12.16 + 11.76 = $23.92.
        heat = self.thin_books([("0.76", "16")], [("0.21", "56")])
        self.assertEqual([r["market_id"] for r in self.scan(heat)[0]], ["10"])
        self.setUp()
        at_line = self.thin_books([("0.5", "25")], [("0.25", "50")])
        self.assertEqual([r["market_id"] for r in self.scan(at_line)[0]], ["10", "20"])

    def test_malformed_book_drops_v2_and_leaves_v1_alone(self):
        recs, err = self.scan(lambda tokens: [book("9", bids=[{"price": "0.4"}]), book("8")])
        self.assertEqual([r["market_id"] for r in recs], ["10"])
        self.assertIn("v2 books unreadable", err)

    def test_unreadable_books_drop_v2_and_leave_v1_alone(self):
        def down(_tokens):
            raise RuntimeError("clob down")
        recs, err = self.scan(down)
        self.assertEqual([r["market_id"] for r in recs], ["10"])
        self.assertIn("clob down", err)

    def test_v1_only_listing_never_reads_books(self):
        def fail(_tokens):
            raise AssertionError("books read for a V1 market")
        recs, _err = self.scan(fail, rows_for=lambda _p: [gamma(id="10")])
        self.assertEqual([r["market_id"] for r in recs], ["10"])

    def test_v2_sweep_runs_without_floors(self):
        # Gamma leaves liquidityNum and volume24hr null on V2 markets that have
        # traded, so queries with those floors or orderings can miss them.
        self.scan(lambda tokens: [book(t) for t in tokens])
        sweeps = [c for c in self.calls if c.get("version") == "v2"]
        self.assertTrue(sweeps)
        self.assertEqual(sweeps[0]["order"], "volumeNum")
        self.assertFalse({"volume_num_min", "liquidity_num_min"} & set(sweeps[0]))

    def test_listing_counts_by_version_show_a_v2_gap(self):
        _recs, err = self.scan(lambda tokens: [book(t) for t in tokens])
        self.assertIn("Gamma listed by version: {'v1': 1, 'v2': 1}", err)


if __name__ == "__main__":
    unittest.main()
