#!/usr/bin/env python3
"""Fetch sibling markets on the same Polymarket event for cross-market checks.

Usage: python3 strategy/tools/siblings.py <market_id>

Why this exists (operator-notes.md 2026-08-05 §1): "Polymarket-internal
cross-market consistency" is our best-evidenced edge class (`1e8dec1078ba`
won), and checking it is pure arithmetic on prices we already have -- no
external source to 403. But nothing surfaced the sibling set itself: a gamma
`/markets` record only carries its own price. Verified live 2026-08-05: a
gamma market record includes an `events` list (`m["events"][0]["id"]`), and
`gamma-api.polymarket.com/events/<id>` returns every sibling market on that
event with current `outcomePrices` in one call -- e.g. a soccer exact-score
event returned 17 sibling markets in one request. `core/pmapi.py` doesn't
expose an events fetch (protected, not our file to add to), so this calls the
gamma API directly, same pattern as core/pmapi.get_json.

Prints one JSON line per sibling market (including the queried one) with the
Yes-outcome price, then a `_sum_check` line: for mutually-exclusive siblings
(a bracket/exact-score/winner event), the Yes prices should sum to ~1.0
(minus vig); a sum far from 1.0 on two OVERLAPPING siblings (e.g. a bracket
whose range contains another market's threshold) is not itself inconsistent
-- work out the actual logical implication before calling it an edge
(playbook Edge class 2 validity test).
"""
import json
import sys
import urllib.request

EVENTS_URL = "https://gamma-api.polymarket.com/events/{}"
MARKET_URL = "https://gamma-api.polymarket.com/markets?id={}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; paper-trader-siblings)"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def main(market_id):
    # NOTE: /markets/<id> (singular) omits the `events` field entirely; only
    # the /markets?id=<id> (list-shaped) response carries it. Verified live
    # 2026-08-05 -- do not "simplify" this back to the singular path.
    matches = fetch(MARKET_URL.format(market_id))
    market = matches[0] if matches else {}
    events = market.get("events") or []
    if not events:
        print(json.dumps({"error": "no event on this market", "market_id": market_id}))
        return
    event_id = events[0]["id"]
    event = fetch(EVENTS_URL.format(event_id))
    siblings = event.get("markets") or []
    yes_sum = 0.0
    for m in siblings:
        try:
            prices = json.loads(m.get("outcomePrices") or "[]")
            yes_price = float(prices[0]) if prices else None
        except (ValueError, TypeError, IndexError):
            yes_price = None
        if yes_price is not None:
            yes_sum += yes_price
        print(json.dumps({
            "market_id": m.get("id"),
            "question": m.get("question"),
            "yes_price": yes_price,
            "closed": m.get("closed"),
            "is_query_target": m.get("id") == market_id,
        }))
    print(json.dumps({"_sum_check": round(yes_sum, 4), "n_siblings": len(siblings),
                       "event_title": event.get("title"),
                       "note": "siblings must be MUTUALLY EXCLUSIVE for this sum to mean "
                               "anything -- verify from the questions before treating "
                               "sum far from 1.0 as an edge"}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
