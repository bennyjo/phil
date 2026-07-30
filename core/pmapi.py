"""Polymarket API helpers (read-only). Stdlib only.

PROTECTED CORE — the trading agent must not edit files under core/.
"""
import json
import time
import urllib.parse
import urllib.request

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
UA = {"User-Agent": "pearl-explorations-paper-trader/0.1"}


def get_json(url, params=None, retries=3):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except Exception as e:  # noqa: BLE001 — retry then surface
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {retries} tries: {last_err}")


def gamma_markets(**params):
    return get_json(f"{GAMMA}/markets", params)


def gamma_market(market_id):
    return get_json(f"{GAMMA}/markets/{market_id}")


def clob_book(token_id):
    return get_json(f"{CLOB}/book", {"token_id": token_id})


def best_prices(token_id):
    """Return (best_bid, best_ask) for a CLOB token, None if side empty."""
    book = clob_book(token_id)
    bids = [float(b["price"]) for b in book.get("bids", [])]
    asks = [float(a["price"]) for a in book.get("asks", [])]
    return (max(bids) if bids else None, min(asks) if asks else None)


def market_tokens(market):
    """Map outcome name -> clob token id for a gamma market record."""
    outcomes = json.loads(market.get("outcomes", "[]"))
    token_ids = json.loads(market.get("clobTokenIds", "[]"))
    return dict(zip(outcomes, token_ids))
