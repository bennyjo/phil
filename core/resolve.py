#!/usr/bin/env python3
"""Settle open paper positions against official Polymarket resolutions.

PROTECTED CORE — the trading agent must not edit files under core/.

For each open position, fetch the market; if it is closed with a decisive
outcome price (>=0.99 for one side), settle won/lost. Markets closed without
decisive prices (disputed/void) settle as void (stake returned) after a grace
period. Rewrites journal/ledger.jsonl in place (single writer).

Usage: python3 core/resolve.py
"""
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "journal" / "ledger.jsonl"
VOID_GRACE_HOURS = 48


def main():
    if not LEDGER.exists():
        print("resolve: no ledger yet")
        return
    entries = [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()]
    now = dt.datetime.now(dt.timezone.utc)
    settled = []
    for e in entries:
        if e["status"] != "open":
            continue
        try:
            m = pmapi.gamma_market(e["market_id"])
        except RuntimeError as err:
            print(f"resolve: fetch failed for {e['market_id']}: {err}", file=sys.stderr)
            continue
        if not m.get("closed"):
            continue
        outcomes = json.loads(m.get("outcomes", "[]"))
        prices = [float(p) for p in json.loads(m.get("outcomePrices", "[]"))]
        decisive = {o: p for o, p in zip(outcomes, prices) if p >= 0.99}
        if decisive:
            won = e["outcome"] in decisive
            e["status"] = "won" if won else "lost"
            e["settled_ts"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            e["pnl_usd"] = round(e["shares"] - e["stake_usd"], 4) if won else -e["stake_usd"]
            e["outcome_won"] = max(zip(prices, outcomes))[1]
            settled.append(e)
        else:
            end = dt.datetime.fromisoformat(e["end_date"].replace("Z", "+00:00"))
            if now - end > dt.timedelta(hours=VOID_GRACE_HOURS):
                e["status"] = "void"
                e["settled_ts"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
                e["pnl_usd"] = 0.0
                settled.append(e)
    LEDGER.write_text("".join(json.dumps(e) + "\n" for e in entries))
    for e in settled:
        print(f"{e['status'].upper():5} {e['pnl_usd']:+7.2f}  est={e['est_prob']:.2f} "
              f"mkt={e['entry_price']:.2f}  [{e['category']}] {e['question'][:70]}")
    print(f"resolve: settled {len(settled)} of {sum(1 for e in entries if e['status'] != 'open') + len(settled)} "
          f"({sum(1 for e in entries if e['status'] == 'open')} still open)")


if __name__ == "__main__":
    main()
