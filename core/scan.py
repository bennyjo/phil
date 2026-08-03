#!/usr/bin/env python3
"""Scan Polymarket for candidate short-term markets.

PROTECTED CORE — the trading agent must not edit files under core/.

Applies only the *protected* filters (banned patterns, resolution window,
price bounds). Everything else — category preferences, liquidity thresholds,
research-worthiness — is the agent's job, driven by strategy/playbook.md.

Usage: python3 core/scan.py [--hours 48] [--min-volume-24h 500] [--limit 400]
Output: JSON lines, one candidate market per line.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTECTED = json.loads((ROOT / "config" / "protected.json").read_text())


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def iso(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=48)
    ap.add_argument("--min-volume-24h", type=float, default=500)
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--min-total-volume", type=float, default=0,
                    help="server-side lifetime-volume floor (gamma volume_num_min). "
                         "Required to reach events more than ~1 day out: results are "
                         "paged in endDate order and the near-term universe is "
                         "thousands of sub-daily markets deep, so without this the "
                         "scan never escapes today regardless of --hours.")
    args = ap.parse_args()

    banned = [re.compile(p, re.I) for p in PROTECTED["banned_question_patterns"]]
    now = utcnow()
    horizon = now + dt.timedelta(hours=args.hours)
    min_end = now + dt.timedelta(minutes=PROTECTED["min_minutes_to_resolution"])

    seen = set()
    kept = 0
    offset = 0
    while offset < args.limit:
        query = dict(
            closed="false", order="endDate", ascending="true",
            limit=100, offset=offset,
            end_date_min=iso(min_end), end_date_max=iso(horizon),
        )
        if args.min_total_volume > 0:
            query["volume_num_min"] = args.min_total_volume
        batch = pmapi.gamma_markets(**query)
        if not batch:
            break
        offset += len(batch)
        for m in batch:
            q = m.get("question") or ""
            if m.get("id") in seen:
                continue
            seen.add(m.get("id"))
            if any(p.search(q) for p in banned):
                continue
            if float(m.get("volume24hr") or 0) < args.min_volume_24h:
                continue
            try:
                prices = [float(p) for p in json.loads(m.get("outcomePrices", "[]"))]
            except (ValueError, TypeError):
                continue
            if not prices:
                continue
            # skip effectively-decided markets (in-play blowouts, resolved-in-waiting)
            if max(prices) > PROTECTED["max_entry_price"] or min(prices) < PROTECTED["min_entry_price"]:
                continue
            kept += 1
            print(json.dumps({
                "market_id": m.get("id"),
                "question": q,
                "end_date": m.get("endDate"),
                "outcomes": json.loads(m.get("outcomes", "[]")),
                "outcome_prices": prices,
                "clob_token_ids": json.loads(m.get("clobTokenIds", "[]")),
                "volume_24h": float(m.get("volume24hr") or 0),
                "liquidity": float(m.get("liquidityNum") or 0),
                "slug": m.get("slug"),
                "description": (m.get("description") or "")[:500],
            }))
    print(f"scan: {kept} candidates within {args.hours}h "
          f"(vol24h>={args.min_volume_24h})", file=sys.stderr)


if __name__ == "__main__":
    main()
