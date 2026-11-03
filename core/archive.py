#!/usr/bin/env python3
"""Archive market data that Polymarket's APIs stop serving.

PROTECTED CORE - the trading agent must not edit files under core/.

A replay can only test what history still exists. 5-minute prices last at
least 60 days (docs.polymarket.com), and no endpoint serves a past book,
spread, or liquidity: Gamma returns those fields for open markets only. So
this saves two things, for future replays and nothing in a cycle reads them:

Prices: `python3 core/archive.py` (CYCLE.md step 6b) writes one write-once
file per market end date, journal/archive/prices/YYYY-MM-DD-<runner>.jsonl.gz.
The runner in the name keeps two runners' files from conflicting in git.
It covers every closed binary market of at least $1k lifetime volume that
isn't banned (config/protected.json) or tagged sports. One JSON row per market:
  {"market_id", "version", "question", "token" (the first outcome, Yes on a
   Yes/No market), "end", "closed", "bucket": 300, "t0", "dt", "p"}
A point's time is t0 plus the first i gaps of dt, and p[i] is its price. Each
run works through the missing dates, oldest first because they expire first,
until --budget-s runs out, so a missed day catches up by itself while the data
still exists. The newest date is two days ago, so most of its markets are
closed; a market still open then is missed.

Books: core/scan.py calls append_books() with the fields of every non-banned
market it reads, at no extra request. One JSON row per scan in
journal/archive/books/YYYY-MM.jsonl: {"at", "books": {market_id: [bestBid,
bestAsk, spread, liquidityNum]}}. V2 markets can carry nulls.

Hindsight: a file must not hand a replay the answer.
  - A windowed /v2/prices-history read of a resolved market carries exact-tick
    points (resolution_seconds 0) priced at or next to the payout, stamped
    inside the window. Only 5-minute buckets are kept, so those are never
    stored, and the read ends at the market's close.
  - No outcome is stored. A replay reads it from Gamma, only to score.
  - A stored point at time T is the price as of T: on 80 sampled points
    (2026-11-03) it matched an `as_of=T` read, exactly on 79 and within 0.005
    on all. So a forecast at t may use a point only if T <= t. An `as_of` answer labels the
    same price one bucket earlier, with T + bucket <= t.

Never blocks a cycle: it exits 0 on any failure and writes a date's file only
once the date is complete, so a failed date is retried by a later run.

Usage: python3 core/archive.py [--budget-s 180]
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import gzip
import json
import os
import pathlib
import re
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402
from screen import runner_id  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRICES_DIR = ROOT / "journal" / "archive" / "prices"
BOOKS_DIR = ROOT / "journal" / "archive" / "books"
PROTECTED = ROOT / "config" / "protected.json"

KEYSET = f"{pmapi.GAMMA}/markets/keyset"
HIST = "https://data-api.polymarket.com/v2/prices-history"
DAY = 86400
BUCKET = 300
# The API refuses a 5-minute read over about 14 days (HTTP 400 at 17), and
# scan.py never looks further ahead than that (--hours 336).
MAX_SPAN = 14 * DAY
NEWEST_LAG_DAYS = 2
OLDEST_LAG_DAYS = 55     # inside the documented 60 days of 5-minute data
MIN_VOLUME = 1000
HIST_INTERVAL_S = 0.06   # ~167 reads per 10 s, under the published 200
MAX_FAILED_SHARE = 0.10

http = pmapi.get_json    # tests swap this for an offline fake
_pace_lock = threading.Lock()
_next_read = [0.0]


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(s):
    """Gamma's two formats: 2026-10-20T04:00:00Z and 2026-10-20 04:11:08.07+00."""
    return int(dt.datetime.fromisoformat(re.sub(r"(Z|\+00)$", "+00:00", s)).timestamp())


# --------------------------------------------------------------------- books

def book_row(market):
    return [market.get(k) for k in ("bestBid", "bestAsk", "spread", "liquidityNum")]


def append_books(books, now, directory=None):
    """Append one scan's book fields. A failure here never reaches the scan."""
    try:
        if not books:
            return
        directory = pathlib.Path(directory or BOOKS_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        line = json.dumps({"at": iso(now), "books": books}, separators=(",", ":"))
        with open(directory / f"{iso(now)[:7]}.jsonl", "a") as f:
            f.write(line + "\n")
    except Exception as e:  # noqa: BLE001 - the archive must not stop a cycle
        print(f"archive: books not saved: {e}", file=sys.stderr)


# -------------------------------------------------------------------- prices

def list_day(day):
    """Every closed market, on either protocol version, ending on this date."""
    out, cursor = [], None
    while True:
        p = {"closed": "true", "end_date_min": iso(day), "end_date_max": iso(day + DAY - 1),
             "volume_num_min": MIN_VOLUME, "include_tag": "true", "limit": 500,
             "version": pmapi.LISTED_VERSIONS}
        if cursor:
            p["after_cursor"] = cursor
        d = http(KEYSET, p)
        out += d.get("markets") or []
        cursor = d.get("next_cursor")
        if not cursor or not d.get("markets"):
            return out


def eligible(market, banned):
    if any(p.search(market.get("question") or "") for p in banned):
        return False
    if "sports" in {t.get("slug") for t in market.get("tags") or []}:
        return False
    ids = pmapi.token_ids(market)
    return bool(ids) and len(ids) == 2


def series(market):
    """The market's archive row, or None when no 5-minute points remain."""
    close = parse_ts(market.get("closedTime") or market["endDate"])
    begin = parse_ts(market.get("startDate") or market.get("createdAt") or market["endDate"])
    start = max(begin, close - MAX_SPAN)
    if start >= close:
        return None
    with _pace_lock:
        wait = _next_read[0] - time.monotonic()
        _next_read[0] = max(_next_read[0], time.monotonic()) + HIST_INTERVAL_S
    if wait > 0:
        time.sleep(wait)
    token = str(pmapi.token_ids(market)[0])
    data = http(HIST, {"token_id": token, "start": start, "end": close,
                       "bucket_seconds": BUCKET}).get("data") or []
    pts = sorted((p for p in data
                  if p.get("resolution_seconds") == BUCKET and p["timestamp"] + BUCKET <= close),
                 key=lambda p: p["timestamp"])
    if not pts:
        return None
    times = [p["timestamp"] for p in pts]
    return {"market_id": str(market["id"]), "version": pmapi.market_version(market),
            "question": market.get("question"), "token": token, "end": market.get("endDate"),
            "closed": market.get("closedTime"), "bucket": BUCKET, "t0": times[0],
            "dt": [b - a for a, b in zip(times, times[1:])], "p": [p["price"] for p in pts]}


def archive_day(day, banned, directory):
    """Write one date's file. Raises RuntimeError, writing nothing, when too
    many reads fail: the date stays missing and a later run retries it."""
    markets = [m for m in list_day(day) if eligible(m, banned)]

    def read(market):
        try:
            return series(market), None
        except RuntimeError as e:   # pmapi.get_json gave up
            return None, e
    with cf.ThreadPoolExecutor(6) as ex:
        results = list(ex.map(read, markets))
    failed = sum(1 for _, err in results if err)
    if failed > MAX_FAILED_SHARE * len(markets):
        raise RuntimeError(f"{iso(day)[:10]}: {failed} of {len(markets)} price reads failed")
    rows = sorted((r for r, _ in results if r), key=lambda r: r["market_id"])
    raw = "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows).encode()
    path = directory / f"{iso(day)[:10]}-{runner_id()}.jsonl.gz"
    tmp = directory / f".{path.name}.tmp"
    tmp.write_bytes(gzip.compress(raw, mtime=0))
    os.replace(tmp, path)
    return {"date": iso(day)[:10], "markets": len(markets), "rows": len(rows), "failed": failed,
            "points": sum(len(r["p"]) for r in rows), "bytes": path.stat().st_size}


def missing_days(now, directory):
    """Dates the archive lacks and the API still serves, oldest first."""
    today = now - now % DAY
    days = (today - lag * DAY for lag in range(OLDEST_LAG_DAYS, NEWEST_LAG_DAYS - 1, -1))
    return [d for d in days if not any(directory.glob(f"{iso(d)[:10]}-*.jsonl.gz"))]


def run(budget_s, now, directory):
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob(".*.tmp"):     # left by a run killed mid-write
        stale.unlink()
    banned = [re.compile(p, re.I) for p in json.loads(PROTECTED.read_text())["banned_question_patterns"]]
    started, days, done = time.monotonic(), missing_days(now, directory), []
    for day in days:
        if time.monotonic() - started >= budget_s:
            break
        done.append(archive_day(day, banned, directory))
    return {"archived": done, "still_missing": len(days) - len(done)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--budget-s", type=float, default=180.0,
                    help="start no new date after this many seconds; a date takes about 60")
    args = ap.parse_args(argv)
    try:
        summary = run(args.budget_s, int(time.time()), pathlib.Path(PRICES_DIR))
    except Exception as e:  # noqa: BLE001 - the archive must not stop a cycle
        print(f"archive: stopped, a later run retries: {e}", file=sys.stderr)
        summary = {"error": str(e)}
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
