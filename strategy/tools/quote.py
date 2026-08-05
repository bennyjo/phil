#!/usr/bin/env python3
"""Preview the live CLOB book for an outcome token before placing a bet.

Usage: python3 strategy/tools/quote.py <token_id> [<token_id> ...]

Lesson from 2026-07-30 cycle: core/scan.py outcome_prices are stale mids;
fills happen at the best ask, which can be several cents worse on
near-resolved markets. Check the ask here and apply risk.json min_edge to
the ASK, not the scan price, before calling core/ledger.py place.
"""
import json
import subprocess
import sys
import urllib.request

BOOK_URL = "https://clob.polymarket.com/book?token_id={}"

# The CLOB API 403s the default "Python-urllib/x.y" User-Agent (verified
# 2026-07-31: same UA -> 403, any real UA -> 200). Any browser/curl-style UA
# passes. But a real UA alone isn't sufficient either: the 2026-08-05 12:31Z
# cycle hit a 403 via urllib with this exact header while curl with an
# identical UA/URL returned 200 on the same token -- looks like a urllib
# TLS-fingerprint block (Cloudflare or similar fronting the CLOB), not just
# UA sniffing. Fall back to curl on any urllib failure rather than surface
# the error, since curl has been reliable every time it's been tried.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; paper-trader-quote)"}


def fetch_curl(url):
    out = subprocess.run(
        ["curl", "-s", "--max-time", "15", "-H", f"User-Agent: {HEADERS['User-Agent']}", url],
        capture_output=True, text=True, timeout=20, check=True,
    )
    return json.loads(out.stdout)


def main(token_ids):
    for tid in token_ids:
        url = BOOK_URL.format(tid)
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                book = json.load(r)
        except Exception as e_urllib:
            try:
                book = fetch_curl(url)
            except Exception as e_curl:
                print(json.dumps({"token_id": tid, "error": f"urllib: {e_urllib}; curl: {e_curl}"}))
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
