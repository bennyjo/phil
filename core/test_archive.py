#!/usr/bin/env python3
"""Offline tests for the price and book archive (core/archive.py).

PROTECTED CORE - the trading agent must not edit files under core/.

The fake price endpoint answers a windowed read the way the real API does: it
ends with exact-tick points priced at or next to the payout, stamped inside the
window. Nothing touches the network, and each test works in a temporary
directory. CI runs it on every push.

Usage: python3 core/test_archive.py
"""
import argparse
import contextlib
import gzip
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import archive  # noqa: E402

DAY = 86400
NOW = archive.parse_ts("2026-11-03T12:00:00Z")
END = "2026-11-01T04:00:00Z"
CLOSE = archive.parse_ts("2026-11-01T04:10:00Z")
NEWEST = archive.parse_ts("2026-11-01T00:00:00Z")


def gamma(id_="1", question="Will it rain in Paris?", tags=("weather",), **over):
    return {"id": id_, "question": question, "version": "v1", "endDate": END,
            "closedTime": "2026-11-01 04:10:00.5+00", "startDate": "2026-10-30T04:00:00Z",
            "outcomes": json.dumps(["Yes", "No"]), "outcomePrices": json.dumps(["1", "0"]),
            "clobTokenIds": json.dumps([f"{id_}-yes", f"{id_}-no"]),
            "tags": [{"slug": t} for t in tags], **over}


class FakeAPI:
    def __init__(self, markets=()):
        self.markets, self.lists, self.reads, self.fail = list(markets), [], [], set()

    def __call__(self, url, params=None):
        if url == archive.KEYSET:
            self.lists.append(dict(params))
            return {"markets": self.markets if params["end_date_min"].startswith("2026-11-01") else [],
                    "next_cursor": None}
        if url == archive.HIST:
            self.reads.append(dict(params))
            if params["token_id"] in self.fail:
                raise RuntimeError("GET prices-history failed after 3 tries")
            end = params["end"]
            return {"data": [
                {"timestamp": end - 1200, "price": 0.40, "resolution_seconds": 300},
                {"timestamp": end - 600, "price": 0.42, "resolution_seconds": 300},
                {"timestamp": end - 900, "price": 0.9995, "resolution_seconds": 0},  # next to the payout
                {"timestamp": end - 700, "price": 1.0, "resolution_seconds": 0},     # the payout
                {"timestamp": end - 60, "price": 0.99, "resolution_seconds": 300},  # ends after the close
                {"timestamp": end - 120, "price": 0.50, "resolution_seconds": 1800},  # another grain
            ]}
        raise AssertionError(f"unexpected url {url}")


class Offline(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = pathlib.Path(tmp.name)
        self.api = FakeAPI([gamma()])
        for name, value in (("http", self.api), ("HIST_INTERVAL_S", 0.0),
                            ("PRICES_DIR", self.dir / "prices")):
            patcher = mock.patch.object(archive, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *argv):
        """(summary, stderr, exit code) with the clock at NOW."""
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(archive.time, "time", lambda: NOW), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = archive.main(list(argv))
        return json.loads(out.getvalue()), err.getvalue(), code

    def newest(self):
        """The file of the one date the fake lists markets for."""
        return self.dir / "prices" / "2026-11-01-cloud.jsonl.gz"

    def rows(self):
        return [json.loads(x) for x in gzip.decompress(self.newest().read_bytes()).decode().splitlines()]


class Hindsight(Offline):
    def test_nothing_past_the_close_or_at_the_payout_is_stored(self):
        self.run_main()
        (row,) = self.rows()
        self.assertEqual(row["p"], [0.40, 0.42])    # the exact ticks and the later bucket are gone
        self.assertEqual(row["t0"], CLOSE - 1200)
        self.assertEqual(row["dt"], [600])
        self.assertEqual(row["bucket"], 300)
        self.assertLessEqual(row["t0"] + sum(row["dt"]) + row["bucket"], CLOSE)

    def test_read_ends_at_the_close_within_the_span_limit(self):
        self.run_main()
        p = self.api.reads[0]
        self.assertEqual((p["end"], p["bucket_seconds"]), (CLOSE, 300))
        self.assertEqual(p["start"], archive.parse_ts("2026-10-30T04:00:00Z"))
        self.api.reads.clear()
        self.api.markets = [gamma(startDate="2026-01-01T00:00:00Z")]
        self.newest().unlink()
        self.run_main()
        self.assertEqual(CLOSE - self.api.reads[0]["start"], 14 * DAY)

    def test_no_row_carries_the_outcome(self):
        self.run_main()
        (row,) = self.rows()
        self.assertEqual(set(row), {"market_id", "version", "question", "token", "end", "closed",
                                    "bucket", "t0", "dt", "p"})


class Selection(Offline):
    def test_excludes_sports_banned_and_non_binary(self):
        self.api.markets = [
            gamma("1"),
            gamma("2", tags=("sports", "soccer")),
            gamma("3", question="Bitcoin Up or Down - November 1, 4PM ET"),
            gamma("4", outcomes=json.dumps(["A", "B", "C"]),
                  clobTokenIds=json.dumps(["a", "b", "c"])),
        ]
        self.run_main()
        self.assertEqual([r["market_id"] for r in self.rows()], ["1"])

    def test_v2_market_reads_its_position_id(self):
        self.api.markets = [gamma("9", version="v2", clobTokenIds=None, positionIds=["p-yes", "p-no"])]
        self.run_main()
        (row,) = self.rows()
        self.assertEqual((row["version"], row["token"]), ("v2", "p-yes"))

    def test_listing_asks_for_both_versions_and_tags(self):
        self.run_main()
        p = self.api.lists[0]
        self.assertEqual(p["version"], ["v1", "v2"])
        self.assertEqual((p["include_tag"], p["volume_num_min"], p["closed"]), ("true", 1000, "true"))

    def test_market_without_points_gets_no_row(self):
        api = self.api
        with mock.patch.object(archive, "http", lambda url, params=None:
                               {"data": []} if url == archive.HIST else api(url, params)):
            summary, _, _ = self.run_main()
        self.assertEqual(self.rows(), [])       # the empty file still marks the date done
        self.assertEqual(summary["still_missing"], 0)


class Schedule(Offline):
    def test_first_run_covers_oldest_to_two_days_ago(self):
        days = archive.missing_days(NOW, self.dir)
        self.assertEqual((archive.iso(days[0])[:10], archive.iso(days[-1])[:10]),
                         ("2026-09-09", "2026-11-01"))
        self.assertEqual(len(days), 54)

    def test_second_run_the_same_day_reads_nothing(self):
        first, _, _ = self.run_main()
        self.assertEqual(len(first["archived"]), 54)
        self.assertEqual(first["still_missing"], 0)
        self.api.lists.clear()
        self.api.reads.clear()
        second, _, _ = self.run_main()
        self.assertEqual(second, {"archived": [], "still_missing": 0})
        self.assertEqual((self.api.lists, self.api.reads), ([], []))

    def test_another_runners_file_counts_as_done(self):
        (self.dir / "prices").mkdir()
        name = "2026-11-01-operator.jsonl.gz"
        (self.dir / "prices" / name).write_bytes(gzip.compress(b""))
        self.assertNotIn(NEWEST, archive.missing_days(NOW, self.dir / "prices"))

    def test_budget_stops_before_the_next_date_and_oldest_goes_first(self):
        clock, seen = [0.0], []

        def slow_day(day, banned, directory):
            seen.append(archive.iso(day)[:10])
            clock[0] += 100.0
            return {"date": seen[-1]}
        with mock.patch.object(archive, "archive_day", slow_day), \
                mock.patch.object(archive.time, "monotonic", lambda: clock[0]):
            summary, _, code = self.run_main("--budget-s", "150")
        self.assertEqual(code, 0)
        self.assertEqual(seen, ["2026-09-09", "2026-09-10"])
        self.assertEqual(summary["still_missing"], 52)

    def test_runner_name_is_in_the_file(self):
        with mock.patch.dict(archive.os.environ, {"PHIL_PUSH_BY_LOOP": "1"}, clear=True):
            self.run_main()
        self.assertTrue((self.dir / "prices" / "2026-11-01-operator.jsonl.gz").exists())


class NeverBlocks(Offline):
    def test_api_down_exits_zero_and_writes_nothing(self):
        def down(url, params=None):
            raise RuntimeError("GET failed after 3 tries")
        with mock.patch.object(archive, "http", down):
            summary, err, code = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("error", summary)
        self.assertIn("a later run retries", err)
        self.assertEqual(list((self.dir / "prices").glob("*.gz")), [])

    def test_unexpected_error_exits_zero(self):
        self.api.markets = [gamma(endDate=None, closedTime=None)]
        _, _, code = self.run_main()
        self.assertEqual(code, 0)

    def test_many_failed_reads_leave_the_date_missing(self):
        self.api.markets = [gamma(str(i)) for i in range(10)]
        self.api.fail = {"0-yes", "1-yes"}
        summary, _, code = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("2 of 10 price reads failed", summary["error"])
        self.assertFalse(self.newest().exists())
        self.api.fail = set()               # the next run retries it
        self.run_main()
        self.assertTrue(self.newest().exists())

    def test_one_failed_read_keeps_the_date(self):
        self.api.markets = [gamma(str(i)) for i in range(10)]
        self.api.fail = {"0-yes"}
        summary, _, _ = self.run_main()
        self.assertEqual(summary["archived"][-1]["failed"], 1)
        self.assertEqual(summary["archived"][-1]["rows"], 9)

    def test_stale_temp_file_is_removed(self):
        (self.dir / "prices").mkdir()
        stale = self.dir / "prices" / ".2026-11-01-cloud.jsonl.gz.tmp"
        stale.write_bytes(b"partial")
        self.run_main()
        self.assertFalse(stale.exists())

    def test_books_failure_is_swallowed(self):
        blocker = self.dir / "not-a-dir"
        blocker.write_text("")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            archive.append_books({"1": [0.1, 0.2, 0.1, 5.0]}, NOW, blocker)
        self.assertIn("books not saved", err.getvalue())


class Books(Offline):
    def test_row_shape_and_monthly_file(self):
        market = {"bestBid": 0.02, "bestAsk": 0.021, "spread": 0.001, "liquidityNum": 294604.2}
        archive.append_books({"7": archive.book_row(market)}, NOW, self.dir)
        archive.append_books({"8": archive.book_row({})}, NOW + 40 * DAY, self.dir)
        rows = [json.loads(x) for x in (self.dir / "2026-11.jsonl").read_text().splitlines()]
        self.assertEqual(rows, [{"at": "2026-11-03T12:00:00Z",
                                 "books": {"7": [0.02, 0.021, 0.001, 294604.2]}}])
        self.assertTrue((self.dir / "2026-12.jsonl").exists())

    def test_empty_scan_writes_nothing(self):
        archive.append_books({}, NOW, self.dir)
        self.assertEqual(list(self.dir.iterdir()), [])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    unittest.main(argv=[sys.argv[0]], verbosity=2 if a.v else 1)
