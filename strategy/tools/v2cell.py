#!/usr/bin/env python3
"""V2 forecast cell (operator note 2026-11-07 ~08:30Z, integrated 2026-11-07 12:1xZ).

core/edge_board.py has no version table, so this computes the `v2` cell the
operator asked for from journal/forecasts.jsonl:
  - rows with version == "v2", settled (won/lost), not superseded by a later row
  - TIGHT slice only: best_ask_at_record - best_bid_at_record <= 0.06
    (wide-book mids flatter dBrier: DEEP-2026-11-07 wide -0.067 vs tight +0.011)
  - brier_delta = mean((est - y)^2) - mean((market_prob_at_record - y)^2),
    negative = beating the displayed price. Same sign convention as score.py.
Also prints the wide slice and the V1 tight baseline over the same dates, for
context only. Read-only; report the TIGHT line in retros.

DEEP-2026-11-09: depth-aware TIGHT. A row is TIGHT only if spread <= 0.06 AND
its top ask holds >= $25 (first `topask=<shares>` in the note x best_ask).
Rows with a sub-$25 top ask are demoted to wide (Knicks 0dd569698c25 / Spurs
45ad4328d413 were ~5-share asks: tight by spread, not by depth). V2 rows with
no topask note are counted and reported, not silently trusted. The TIGHT line
is also split by benchmark: `spread-derived` in the note (ML inferred from a
point spread, an unvalidated conversion) vs sportsbook-odds rows.

usage: python3 strategy/tools/v2cell.py [--since 2026-11-09] [--until 2026-11-15]
       (default --since is the sweep start, 2026-11-09)
"""
import argparse
import json
import math
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIGHT = 0.06
MIN_TOP_USD = 25.0
DEPTH_DEMOTE = {"0dd569698c25", "45ad4328d413"}  # pre-topask rows, ~5-share asks
TOPASK = re.compile(r"topask=(\d+(?:\.\d+)?)")


def depth_ok(r):
    """True/False on a $25 top-ask test; None when the note carries no topask."""
    if r["id"] in DEPTH_DEMOTE:
        return False
    m = TOPASK.search(r.get("note") or "")
    if not m:
        return None
    return float(m.group(1)) * float(r["best_ask_at_record"]) >= MIN_TOP_USD


def spread_derived(r):
    return "spread-derived" in (r.get("note") or "").lower()


def load():
    with open(os.path.join(ROOT, "journal", "forecasts.jsonl")) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    superseded = {r.get("supersedes") for r in rows if r.get("supersedes")}
    return rows, superseded


def cell(rows):
    n = len(rows)
    if not n:
        return "n=0"
    d = []
    for r in rows:
        y = 1.0 if r["status"] == "won" else 0.0
        d.append((r["est_prob"] - y) ** 2 - (r["market_prob_at_record"] - y) ** 2)
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1)) if n > 1 else float("nan")
    se = sd / math.sqrt(n) if n > 1 else float("nan")
    events = len({r["market_id"] for r in rows})
    return (f"n={n} events={events} brier_delta={m:+.4f} "
            f"[{m - 1.96 * se:+.4f},{m + 1.96 * se:+.4f}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-11-09")
    ap.add_argument("--until", default="2099-12-31")
    a = ap.parse_args()
    rows, superseded = load()

    def pick(version, tight, settled=True):
        out = []
        for r in rows:
            day = r.get("ts", "")[:10]
            if r.get("version") != version or not (a.since <= day <= a.until):
                continue
            if r["id"] in superseded:
                continue
            if settled and r.get("status") not in ("won", "lost"):
                continue
            bid, ask = r.get("best_bid_at_record"), r.get("best_ask_at_record")
            if bid is None or ask is None or r.get("market_prob_at_record") is None:
                continue
            is_tight = ask - bid <= TIGHT + 1e-9
            if is_tight and version == "v2" and depth_ok(r) is False:
                is_tight = False
            if is_tight != tight:
                continue
            out.append(r)
        return out

    print(f"window {a.since}..{a.until}; tight = spread <= {TIGHT}")
    t = pick('v2', True)
    print(f"v2 TIGHT  {cell(t)}  (open: {len(pick('v2', True, False)) - len(t)})")
    print(f"  odds-bench      {cell([r for r in t if not spread_derived(r)])}")
    print(f"  spread-derived  {cell([r for r in t if spread_derived(r)])}")
    nodepth = [r for r in pick('v2', True, False) if depth_ok(r) is None]
    if nodepth:
        print(f"  WARNING: {len(nodepth)} v2 TIGHT row(s) lack topask= in the note: "
              + " ".join(r['id'] for r in nodepth))
    print(f"v2 wide   {cell(pick('v2', False))}  (context only; mid-scoring artifact risk)")
    print(f"v1 TIGHT  {cell(pick('v1', True))}  (baseline, same window)")


if __name__ == "__main__":
    main()
