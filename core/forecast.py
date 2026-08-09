#!/usr/bin/env python3
"""Forecast ledger: score every researched estimate, not just bets.

PROTECTED CORE — the trading agent must not edit files under core/.
This is the only writer of journal/forecasts.jsonl (resolve.py settles rows).

The experiment's honest metric is brier_delta — is the agent's probability a
better forecast than the market's own price? — and measuring that needs no
stake. Research that ends in a skip (no-edge, market-agrees) still produced
an estimate; recording it here turns ~10-30 researched candidates/day into
scored calibration feedback instead of ~0-1 settled bets/day.

No caps, no edge floor, no fill: the market baseline is the MID at record
time ((bid+ask)/2), not the ask a bet would fill at — a forecast has no
transaction, and the mid is the stricter benchmark. Forecast brier_delta is
therefore NOT comparable to bet brier_delta; score.py reports them in
separate sections. est_prob is the agent's honest belief, formed before
anchoring on the price, exactly as for bets.

One live forecast per market+outcome: recurring re-checks of the same market
must not flood the stats with correlated rows (revision support is a v2
question, on evidence).

Usage:
  record: python3 core/forecast.py record --market-id 123 --outcome Yes \
            --est-prob 0.62 --category econ --skip-reason no-edge \
            [--fit-score 4] [--note "..."] [--strategy-rev abc1234]
  status: python3 core/forecast.py status
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import uuid
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORECASTS = ROOT / "journal" / "forecasts.jsonl"


def read_forecasts():
    if not FORECASTS.exists():
        return []
    return [json.loads(line) for line in FORECASTS.read_text().splitlines() if line.strip()]


def cmd_status(rows):
    print(json.dumps({
        "total": len(rows),
        "by_status": dict(Counter(r["status"] for r in rows)),
        "by_skip_reason": dict(Counter(r.get("skip_reason") or "?" for r in rows)),
        "settled_wins": sum(1 for r in rows if r["status"] == "won"),
    }, indent=2))


def cmd_record(args, rows):
    if not 0.0 < args.est_prob < 1.0:
        sys.exit("REJECTED: est-prob must be in (0,1)")
    if any(r["market_id"] == args.market_id and r["outcome"] == args.outcome
           and r["status"] == "open" for r in rows):
        sys.exit("REJECTED: already have an open forecast on this market+outcome")

    m = pmapi.gamma_market(args.market_id)
    if m.get("closed"):
        sys.exit("REJECTED: market is closed")
    tokens = pmapi.market_tokens(m)
    if args.outcome not in tokens:
        sys.exit(f"REJECTED: outcome {args.outcome!r} not in {list(tokens)}")
    bid, ask = pmapi.best_prices(tokens[args.outcome])
    if bid is None and ask is None:
        sys.exit("REJECTED: empty book — no market probability to benchmark against")
    mid = (bid + ask) / 2 if bid is not None and ask is not None else bid or ask

    row = {
        "id": uuid.uuid4().hex[:12],
        "ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "market_id": args.market_id,
        "question": m.get("question"),
        "slug": m.get("slug"),
        "end_date": m.get("endDate"),
        "outcome": args.outcome,
        "token_id": tokens[args.outcome],
        "est_prob": args.est_prob,
        "best_bid_at_record": bid,
        "best_ask_at_record": ask,
        "market_prob_at_record": round(mid, 4),
        "category": args.category,
        "skip_reason": args.skip_reason,
        "fit_score": args.fit_score,
        "note": args.note,
        "strategy_rev": args.strategy_rev,
        "status": "open",
    }
    with FORECASTS.open("a") as f:
        f.write(json.dumps(row) + "\n")
    print(json.dumps({"recorded": row["id"], "mid": row["market_prob_at_record"],
                      "bid": bid, "ask": ask, "delta_vs_mid": round(args.est_prob - mid, 4),
                      "question": row["question"]}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("record")
    p.add_argument("--market-id", required=True)
    p.add_argument("--outcome", required=True, help="exact outcome name, e.g. Yes")
    p.add_argument("--est-prob", type=float, required=True,
                   help="agent's honest probability, formed before reading the price")
    p.add_argument("--category", required=True,
                   help="agent-assigned category, e.g. earnings/soccer/esports/news")
    p.add_argument("--skip-reason", required=True,
                   help="funnel disposition: bet|no-edge|market-agrees|... "
                        "(use 'bet' when a place follows this forecast)")
    p.add_argument("--fit-score", type=int, default=None, help="playbook fit score 0-5")
    p.add_argument("--note", default="", help="one line of context (optional)")
    p.add_argument("--strategy-rev", default="", help="git rev of strategy/ used")
    sub.add_parser("status")
    args = ap.parse_args()

    rows = read_forecasts()
    if args.cmd == "status":
        cmd_status(rows)
    else:
        cmd_record(args, rows)


if __name__ == "__main__":
    main()
