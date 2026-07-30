#!/usr/bin/env python3
"""Preview the live CLOB book for an outcome token before placing a bet.

Usage: python3 strategy/tools/quote.py <token_id> [<token_id> ...]

Lesson from 2026-07-30 cycle: core/scan.py outcome_prices are stale mids;
fills happen at the best ask, which can be several cents worse on
near-resolved markets. Check the ask here and apply risk.json min_edge to
the ASK, not the scan price, before calling core/ledger.py place.
"""
import json
import sys
import urllib.request

BOOK_URL = "https://clob.polymarket.com/book?token_id={}"


def main(token_ids):
    for tid in token_ids:
        try:
            with urllib.request.urlopen(BOOK_URL.format(tid), timeout=15) as r:
                book = json.load(r)
        except Exception as e:
            print(json.dumps({"token_id": tid, "error": str(e)}))
            continue
        asks = sorted((float(a["price"]), float(a["size"])) for a in book.get("asks", []))
        bids = sorted(((float(b["price"]), float(b["size"])) for b in book.get("bids", [])), reverse=True)
        print(json.dumps({
            "token_id": tid[:16] + "...",
            "best_ask": asks[0] if asks else None,
            "best_bid": bids[0] if bids else None,
            "spread": round(asks[0][0] - bids[0][0], 4) if asks and bids else None,
            "top_asks": asks[:3],
        }))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
