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

usage: python3 strategy/tools/v2cell.py [--since 2026-11-09] [--until 2026-11-15]
"""
import argparse
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIGHT = 0.06


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
    ap.add_argument("--since", default="2026-11-01")
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
            if (ask - bid <= TIGHT + 1e-9) != tight:
                continue
            out.append(r)
        return out

    print(f"window {a.since}..{a.until}; tight = spread <= {TIGHT}")
    print(f"v2 TIGHT  {cell(pick('v2', True))}  (open: {len(pick('v2', True, False)) - len(pick('v2', True))})")
    print(f"v2 wide   {cell(pick('v2', False))}  (context only; mid-scoring artifact risk)")
    print(f"v1 TIGHT  {cell(pick('v1', True))}  (baseline, same window)")


if __name__ == "__main__":
    main()
