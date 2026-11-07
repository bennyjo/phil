#!/usr/bin/env python3
"""Paper broker: place simulated positions and track the bankroll.

PROTECTED CORE — the trading agent must not edit files under core/.
The agent CALLS this to bet; it cannot bypass the caps in config/protected.json
because this is the only writer of journal/ledger.jsonl.

Fills are honest: a paper BUY walks the live CLOB asks for the chosen outcome
token, cheapest first (crossing the spread, like a real taker order), and pays
each level's taker fee out of the stake, so the stake buys fewer shares. If the
book is empty, the asks within the protected price bounds cannot fill the whole
stake (there are no partial fills), the order is below the book's min_order_size
(the CLOB would reject it), or the fill violates protected caps, the bet is
rejected.

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
V2_BET_SKIPS = ROOT / "journal" / "v2-bet-skips.jsonl"
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
            cash += e["stake_usd"] + e["pnl_usd"]  # what resolve.py paid out
    return cash


def skip_v2_bet(args, m):
    """Log a bet refused because its V2 market is read-only (see pmapi.tradable),
    so the bets V2 costs Phil stay countable."""
    reason = (f"this Gamma version {pmapi.market_version(m)!r} market is read-only: "
              f"Phil forecasts it but bets only V1 and binary V2 markets")
    with V2_BET_SKIPS.open("a") as f:
        f.write(json.dumps({
            "ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "market_id": args.market_id, "question": m.get("question"),
            "outcome": args.outcome, "version": pmapi.market_version(m),
            "est_prob": args.est_prob, "stake_usd": args.stake,
            "edge_class": args.edge_class, "strategy_rev": args.strategy_rev,
            "reason": reason}) + "\n")
    sys.exit(f"REJECTED: {reason}; logged to {V2_BET_SKIPS.name}")


def walk_asks(market, asks, stake):
    """Spend stake on ask levels (price, size), in order, each at its own price
    and taker fee. Returns (shares, fee_usd, unfilled_usd)."""
    shares = fee_usd = 0.0
    for price, size in asks:
        fee_per_share = pmapi.taker_fee_per_share(market, price)
        cost_per_share = price + fee_per_share
        wanted = stake / cost_per_share
        if wanted <= size:
            return shares + wanted, fee_usd + wanted * fee_per_share, 0.0
        shares += size
        fee_usd += size * fee_per_share
        stake -= size * cost_per_share
    return shares, fee_usd, stake


def cmd_status(entries):
    open_pos = [e for e in entries if e["status"] == "open"]
    settled = [e for e in entries if e["status"] in ("won", "lost")]
    pnl = sum(e["pnl_usd"] for e in entries if e["status"] in ("won", "lost", "void"))
    print(json.dumps({
        "cash": round(bankroll(entries), 2),
        "open_positions": len(open_pos),
        "settled": len(settled),
        "wins": sum(1 for e in settled if e["status"] == "won"),
        "realized_pnl": round(pnl, 2),
        "v2_bets_skipped": (len(V2_BET_SKIPS.read_text().splitlines())
                            if V2_BET_SKIPS.exists() else 0),
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
    if tokens is None:
        sys.exit(f"REJECTED: no usable CLOB token ids (Gamma version "
                 f"{pmapi.market_version(m)!r}; supported: "
                 f"{sorted(pmapi.SUPPORTED_VERSIONS)})")
    if args.outcome not in tokens:
        sys.exit(f"REJECTED: outcome {args.outcome!r} not in {list(tokens)}")
    if not pmapi.tradable(m):
        skip_v2_bet(args, m)
    q = pmapi.book_quote(tokens[args.outcome])
    bid, ask = q["bid"], q["ask"]
    if ask is None:
        sys.exit("REJECTED: no asks in the book (cannot fill)")
    if not PROTECTED["min_entry_price"] <= ask <= PROTECTED["max_entry_price"]:
        sys.exit(f"REJECTED: fill price {ask} outside protected bounds")
    fillable = [lvl for lvl in q["asks"] if lvl[0] <= PROTECTED["max_entry_price"]]
    try:
        shares, fee_usd, unfilled = walk_asks(m, fillable, args.stake)
    except ValueError as err:
        sys.exit(f"REJECTED: cannot price the taker fee ({err})")
    if round(unfilled, 6) > 0:
        sys.exit(f"REJECTED: asks within the protected bounds fill only "
                 f"${args.stake - unfilled:.2f} of the ${args.stake:g} stake; "
                 f"partial fills are not booked (lower the stake or skip)")
    # docs.polymarket.com/market-data/market-details: "Orders smaller than the
    # minimum order size are rejected." The book's min_order_size is in shares.
    if q["min_order_size"] and shares < q["min_order_size"]:
        sys.exit(f"REJECTED: {shares:.2f} shares is below the book's min_order_size "
                 f"{q['min_order_size']:g} (raise the stake or skip)")
    # What the shares cost per share before fees. market_prob_at_entry stays the
    # top ask, so the gap between them shows the walk's slippage.
    entry_price = round((args.stake - fee_usd) / shares, 6)

    entry = {
        "id": uuid.uuid4().hex[:12],
        "ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "market_id": args.market_id,
        "question": m.get("question"),
        "slug": m.get("slug"),
        "end_date": m.get("endDate"),
        "outcome": args.outcome,
        "token_id": tokens[args.outcome],
        "entry_price": entry_price,
        "best_bid_at_entry": bid,
        "market_prob_at_entry": ask,
        "est_prob": args.est_prob,
        "edge": round(args.est_prob - entry_price, 4),
        "stake_usd": args.stake,
        "shares": round(shares, 4),
        "fee_usd": round(fee_usd, 5),
        "category": args.category,
        "edge_class": args.edge_class,
        "rationale": args.rationale,
        "strategy_rev": args.strategy_rev,
        "status": "open",
    }
    with LEDGER.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps({"placed": entry["id"], "filled_at": entry_price, "edge": entry["edge"],
                      "shares": entry["shares"], "fee_usd": entry["fee_usd"],
                      "question": entry["question"]}, indent=2))


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
