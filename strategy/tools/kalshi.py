#!/usr/bin/env python3
"""Cross-venue benchmark: fetch Kalshi market/event prices.

Usage:
  python3 strategy/tools/kalshi.py events --series-ticker KXFED
  python3 strategy/tools/kalshi.py markets --series-ticker KXFED --status open
  python3 strategy/tools/kalshi.py markets --event-ticker KXFED-26SEP

Reachability (operator-notes.md 2026-08-05 10:53Z, re-verified from this
runner 2026-08-05 ~13:30Z after the egress allowlist update):
  api.elections.kalshi.com -> 200 (was 403 pre-allowlist; direct fetch works
  now, no auth needed for public market data). api.manifold.markets is also
  200 but Manifold is play-money -- reference only, never a benchmark.
  www.metaculus.com/api2 is STILL 403 even with the allowlist (site-side bot
  block, confirmed both from a residential IP and this runner) -- don't use
  it; WebSearch-by-name is the only channel there.

Kalshi is real-money and overlaps Polymarket on Fed rate decisions, CPI/jobs
prints, and other scheduled economic and political events (playbook.md
Estimation §3). A market's yes_bid/yes_ask/no_bid/no_ask are already in
dollars (0-1), directly comparable to a Polymarket outcome price after
accounting for both platforms' spreads -- do not treat a single side's ask as
the "true" probability without checking the bid too.
"""
import json
import sys
import urllib.parse
import urllib.request

BASE = "https://api.elections.kalshi.com/trade-api/v2"


def fetch(path, params):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; paper-trader-kalshi)"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def cmd_events(args):
    params = {}
    for flag, key in (("--series-ticker", "series_ticker"), ("--status", "status")):
        if flag in args:
            params[key] = args[args.index(flag) + 1]
    params.setdefault("limit", "20")
    data = fetch("/events", params)
    for e in data.get("events", []):
        print(json.dumps({
            "event_ticker": e.get("event_ticker"),
            "title": e.get("title"),
            "strike_date": e.get("strike_date"),
            "settlement_source": (e.get("settlement_sources") or [{}])[0].get("url"),
        }))


def cmd_markets(args):
    params = {}
    for flag, key in (("--series-ticker", "series_ticker"), ("--event-ticker", "event_ticker"),
                       ("--status", "status")):
        if flag in args:
            params[key] = args[args.index(flag) + 1]
    params.setdefault("limit", "50")
    data = fetch("/markets", params)
    for m in data.get("markets", []):
        print(json.dumps({
            "ticker": m.get("ticker"),
            "title": m.get("yes_sub_title") or m.get("no_sub_title"),
            "close_time": m.get("close_time"),
            "yes_bid": m.get("yes_bid_dollars"),
            "yes_ask": m.get("yes_ask_dollars"),
            "no_bid": m.get("no_bid_dollars"),
            "no_ask": m.get("no_ask_dollars"),
            "status": m.get("status"),
        }))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("events", "markets"):
        sys.exit(__doc__)
    {"events": cmd_events, "markets": cmd_markets}[sys.argv[1]](sys.argv[2:])
