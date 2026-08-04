#!/usr/bin/env python3
"""Paper broker: place simulated positions and track the bankroll.

PROTECTED CORE — the trading agent must not edit files under core/.
The agent CALLS this to bet; it cannot bypass the caps in config/protected.json
because this is the only writer of journal/ledger.jsonl.

Fills are honest: a paper BUY fills at the live CLOB best ask for the chosen
outcome token (crossing the spread, like a real taker order). If the book is
empty or the fill violates protected caps, the bet is rejected.

Usage:
  place:  python3 core/ledger.py place --market-id 123 --outcome Yes \
            --est-prob 0.62 --stake 10 --category earnings \
            --rationale "consensus beat rate 78%, whisper above street"
  status: python3 core/ledger.py status
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "journal" / "ledger.jsonl"
PROTECTED = json.loads((ROOT / "config" / "protected.json").read_text())


def read_ledger():
    if not LEDGER.exists():
        return []
    return [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()]


def bankroll(entries):
    cash = PROTECTED["sim_bankroll_usd"]
    for e in entries:
        if e["status"] in ("open", "won", "lost", "void"):
            cash -= e["stake_usd"]
        if e["status"] == "won":
            cash += e["shares"]  # $1 per share
        elif e["status"] == "void":
            cash += e["stake_usd"]
    return cash


def cmd_status(entries):
    open_pos = [e for e in entries if e["status"] == "open"]
    settled = [e for e in entries if e["status"] in ("won", "lost")]
    pnl = sum((e["shares"] - e["stake_usd"]) if e["status"] == "won" else -e["stake_usd"]
              for e in settled)
    print(json.dumps({
        "cash": round(bankroll(entries), 2),
        "open_positions": len(open_pos),
        "settled": len(settled),
        "wins": sum(1 for e in settled if e["status"] == "won"),
        "realized_pnl": round(pnl, 2),
        "open": [{"id": e["id"], "q": e["question"][:70], "outcome": e["outcome"],
                  "entry": e["entry_price"], "est": e["est_prob"], "ends": e["end_date"]}
                 for e in open_pos],
    }, indent=2))


def cmd_place(args, entries):
    open_pos = [e for e in entries if e["status"] == "open"]
    if len(open_pos) >= PROTECTED["max_open_positions"]:
        sys.exit(f"REJECTED: max_open_positions ({PROTECTED['max_open_positions']}) reached")
    if args.stake > PROTECTED["max_stake_usd"]:
        sys.exit(f"REJECTED: stake {args.stake} > max_stake_usd {PROTECTED['max_stake_usd']}")
    if args.stake > bankroll(entries):
        sys.exit("REJECTED: insufficient sim cash")
    if not 0.0 < args.est_prob < 1.0:
        sys.exit("REJECTED: est-prob must be in (0,1)")
    if any(e["market_id"] == args.market_id and e["outcome"] == args.outcome
           for e in open_pos):
        sys.exit("REJECTED: already have an open position on this market+outcome")

    m = pmapi.gamma_market(args.market_id)
    if m.get("closed"):
        sys.exit("REJECTED: market is closed")
    tokens = pmapi.market_tokens(m)
    if args.outcome not in tokens:
        sys.exit(f"REJECTED: outcome {args.outcome!r} not in {list(tokens)}")
    bid, ask = pmapi.best_prices(tokens[args.outcome])
    if ask is None:
        sys.exit("REJECTED: no asks in the book (cannot fill)")
    if not PROTECTED["min_entry_price"] <= ask <= PROTECTED["max_entry_price"]:
        sys.exit(f"REJECTED: fill price {ask} outside protected bounds")

    entry = {
        "id": uuid.uuid4().hex[:12],
        "ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "market_id": args.market_id,
        "question": m.get("question"),
        "slug": m.get("slug"),
        "end_date": m.get("endDate"),
        "outcome": args.outcome,
        "token_id": tokens[args.outcome],
        "entry_price": ask,
        "best_bid_at_entry": bid,
        "market_prob_at_entry": ask,
        "est_prob": args.est_prob,
        "edge": round(args.est_prob - ask, 4),
        "stake_usd": args.stake,
        "shares": round(args.stake / ask, 4),
        "category": args.category,
        "edge_class": args.edge_class,
        "rationale": args.rationale,
        "strategy_rev": args.strategy_rev,
        "status": "open",
    }
    with LEDGER.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps({"placed": entry["id"], "filled_at": ask, "edge": entry["edge"],
                      "shares": entry["shares"], "question": entry["question"]}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("place")
    p.add_argument("--market-id", required=True)
    p.add_argument("--outcome", required=True, help="exact outcome name, e.g. Yes")
    p.add_argument("--est-prob", type=float, required=True,
                   help="agent's probability that this outcome wins")
    p.add_argument("--stake", type=float, required=True)
    p.add_argument("--category", required=True,
                   help="agent-assigned category, e.g. earnings/soccer/esports/news")
    p.add_argument("--edge-class", required=True,
                   choices=["info-race", "cross-market", "book-devig", "other"],
                   help="playbook edge class this bet claims (scored separately)")
    p.add_argument("--rationale", required=True, help="one-line reason (for the retro)")
    p.add_argument("--strategy-rev", default="", help="git rev of strategy/ used")
    sub.add_parser("status")
    args = ap.parse_args()

    entries = read_ledger()
    if args.cmd == "status":
        cmd_status(entries)
    else:
        cmd_place(args, entries)


if __name__ == "__main__":
    main()
