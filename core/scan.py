#!/usr/bin/env python3
"""Scan Polymarket for candidate short-term markets.

PROTECTED CORE — the trading agent must not edit files under core/.

Split of responsibilities (changed 2026-08-03):
  * WHAT TO LOOK FOR is the agent's: `strategy/discovery.py` supplies the
    gamma queries (windows, volume/liquidity floors, ordering, tags). The
    agent owns its own sensing and can widen or retarget it when its evidence
    says the candidate pool is an artifact rather than the market.
  * WHAT IS ALLOWED stays here: banned market classes, minimum time to
    resolution, entry-price bounds and the output contract are enforced after
    discovery, on every candidate, and cannot be bypassed by a query.

V2 markets with at least the placeholder line of book depth flow out tagged
with their version like V1 ones.
core/ledger.py bets the binary ones and refuses the rest (pmapi.tradable).

If `strategy/discovery.py` is missing, raises, or returns nothing usable, this
falls back to the built-in default query and says so on stderr — a broken
discovery module degrades sensing, it never silently returns an empty market.

Usage: python3 core/scan.py [--hours 168] [--min-volume-24h 0] [--limit 400]
Output: JSON lines, one candidate market per line.
"""
import argparse
import collections
import datetime as dt
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import archive  # noqa: E402
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTECTED = json.loads((ROOT / "config" / "protected.json").read_text())
# Gamma version -> markets keep() skipped for lack of usable token ids.
UNSUPPORTED = collections.Counter()
# Gamma version -> distinct markets the listings returned, before any filter.
LISTED = collections.Counter()
# V2 markets by book depth: "kept", "thin" (under the placeholder line), or "empty".
V2_BOOKS = collections.Counter()
# Market id -> book fields of every non-banned market read, for core/archive.py.
BOOKS = {}


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def iso(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def default_queries(args, min_end, horizon):
    q = {"_label": "default", "closed": "false", "order": "endDate",
         "ascending": "true", "end_date_min": iso(min_end),
         "end_date_max": iso(horizon)}
    if args.min_total_volume > 0:
        q["volume_num_min"] = args.min_total_volume
    return [q]


def discovery_queries(args, min_end, horizon):
    """Ask the agent-owned discovery module what to look for."""
    try:
        sys.path.insert(0, str(ROOT / "strategy"))
        import discovery  # noqa: PLC0415 — optional, agent-owned
        qs = discovery.queries(now=utcnow(), min_end=min_end, horizon=horizon,
                               args=vars(args), protected=PROTECTED)
        qs = [dict(q) for q in qs if isinstance(q, dict)]
        if not qs:
            raise ValueError("discovery.queries() returned no usable queries")
        for q in qs:
            q.setdefault("closed", "false")
            # a query may not reach past the protected resolution floor
            q["end_date_min"] = max(str(q.get("end_date_min") or ""), iso(min_end))
        print(f"scan: discovery.py supplied {len(qs)} quer{'y' if len(qs) == 1 else 'ies'}",
              file=sys.stderr)
        return qs
    except Exception as e:  # noqa: BLE001 — any failure falls back, loudly
        print(f"scan: discovery.py unusable ({type(e).__name__}: {e}); "
              f"falling back to default query", file=sys.stderr)
        return default_queries(args, min_end, horizon)


def v2_sweep(args, min_end, horizon):
    """Core's own V2 query, so a V2 market cannot go unseen. Gamma leaves
    volume24hr and liquidityNum null on V2 markets that have traded, which hides
    them from queries with those floors or orderings. volumeNum is filled in."""
    return {"_label": "v2-sweep", "version": "v2", "closed": "false",
            "order": "volumeNum", "ascending": "false",
            "end_date_min": iso(min_end), "end_date_max": iso(horizon)}


def drop_thin_v2(recs):
    """Drop V2 records whose books are empty or under placeholder_liquidity_usd
    of depth, and count them. Most V2 books are empty, with placeholder 0.5/0.5
    prices that pass keep() and would spend the screener slots V1 markets get.
    Unreadable books count as empty, so an outage costs V2 this scan and never
    touches V1.

    Depth is the bid dollars of all the market's tokens. A Yes ask at p is the
    No bid at 1-p, so this counts each resting order once. Gamma's liquidityNum,
    the figure score.placeholder_book judges, is this same number once it catches
    up: all 11 live V2 markets matched to the cent on 2026-11-07. The live book
    has neither that field's lag nor its nulls (see v2_sweep)."""
    tokens = [t for r in recs if r["version"] == "v2" for t in r["clob_token_ids"]]
    if not tokens:
        return recs
    try:
        books = pmapi.clob_books(tokens)
        depth = {b.get("asset_id"): pmapi.bid_depth_usd(b) for b in books}
    except (RuntimeError, KeyError, TypeError, ValueError) as e:
        print(f"scan: v2 books unreadable: {e}", file=sys.stderr)
        books, depth = [], {}
    live = {b.get("asset_id") for b in books if b.get("bids") or b.get("asks")}
    kept = []
    for r in recs:
        if r["version"] == "v2":
            state = "empty"
            if live.intersection(r["clob_token_ids"]):
                usd = sum(depth.get(t, 0.0) for t in r["clob_token_ids"])
                state = "kept" if usd >= PROTECTED["placeholder_liquidity_usd"] else "thin"
            V2_BOOKS[state] += 1
            if state != "kept":
                continue
        kept.append(r)
    return kept


def keep(m, seen, banned, args):
    """Protected admissibility filter. Returns the output record or None."""
    q = m.get("question") or ""
    if m.get("id") in seen:
        return None
    seen.add(m.get("id"))
    LISTED[pmapi.market_version(m)] += 1
    if any(p.search(q) for p in banned):
        return None
    BOOKS[str(m.get("id"))] = archive.book_row(m)
    if float(m.get("volume24hr") or 0) < args.min_volume_24h:
        return None
    try:
        prices = [float(p) for p in json.loads(m.get("outcomePrices", "[]"))]
    except (ValueError, TypeError):
        return None
    if not prices:
        return None
    # skip effectively-decided markets (in-play blowouts, resolved-in-waiting)
    if max(prices) > PROTECTED["max_entry_price"] or min(prices) < PROTECTED["min_entry_price"]:
        return None
    # An unsupported version or unusable ids: skip it rather than crash the scan.
    token_ids = pmapi.token_ids(m)
    if token_ids is None:
        UNSUPPORTED[pmapi.market_version(m)] += 1
        return None
    event = (m.get("events") or [{}])[0]
    return {
        "market_id": m.get("id"),
        "version": pmapi.market_version(m),
        "question": q,
        "end_date": m.get("endDate"),
        "event_id": event.get("id"),
        "event_slug": event.get("slug"),
        "outcomes": json.loads(m.get("outcomes", "[]")),
        "outcome_prices": prices,
        "clob_token_ids": token_ids,
        "volume_24h": float(m.get("volume24hr") or 0),
        "liquidity": float(m.get("liquidityNum") or 0),
        "slug": m.get("slug"),
        "description": (m.get("description") or "")[:500],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=168)
    ap.add_argument("--min-volume-24h", type=float, default=0)
    ap.add_argument("--limit", type=int, default=400,
                    help="max markets paged per query")
    ap.add_argument("--min-total-volume", type=float, default=50000,
                    help="lifetime-volume floor (gamma volume_num_min) for the "
                         "DEFAULT query. Results page in endDate order and the "
                         "near-term universe is thousands of sub-daily markets "
                         "deep, so without a floor the scan never escapes today "
                         "regardless of --hours. strategy/discovery.py may set "
                         "its own per-query floors.")
    args = ap.parse_args()

    banned = [re.compile(p, re.I) for p in PROTECTED["banned_question_patterns"]]
    now = utcnow()
    horizon = now + dt.timedelta(hours=args.hours)
    min_end = now + dt.timedelta(minutes=PROTECTED["min_minutes_to_resolution"])

    seen, kept = set(), 0
    for base in discovery_queries(args, min_end, horizon) + [v2_sweep(args, min_end, horizon)]:
        label = base.pop("_label", "unlabeled")
        got = 0
        offset = 0
        while offset < args.limit:
            try:
                batch = pmapi.gamma_markets(**dict(base, limit=100, offset=offset))
            except RuntimeError as e:
                print(f"scan: query {label!r} failed: {e}", file=sys.stderr)
                break
            if not batch:
                break
            offset += len(batch)
            recs = [keep(m, seen, banned, args) for m in batch]
            for rec in drop_thin_v2([r for r in recs if r]):
                got += 1
                kept += 1
                # The query that first found it: screen.py counts the
                # funnel row's pool_by_query from this.
                rec["query"] = label
                print(json.dumps(rec))
        print(f"scan: query {label!r} -> {got} candidates", file=sys.stderr)
    if UNSUPPORTED:
        print(f"scan: skipped {sum(UNSUPPORTED.values())} markets with no usable "
              f"token ids, by Gamma version: {dict(UNSUPPORTED)}", file=sys.stderr)
    print(f"scan: Gamma listed by version: {dict(sorted(LISTED.items(), key=str))}; "
          f"v2 markets kept: {V2_BOOKS['kept']}, "
          f"dropped for a thin book (under ${PROTECTED['placeholder_liquidity_usd']:g}): "
          f"{V2_BOOKS['thin']}, "
          f"dropped for an empty book: {V2_BOOKS['empty']}", file=sys.stderr)
    print(f"scan: {kept} candidates total within {args.hours}h", file=sys.stderr)
    archive.append_books(BOOKS, int(now.timestamp()))


if __name__ == "__main__":
    main()
