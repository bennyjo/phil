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


# Gamma tags each market with the CLOB protocol it trades on. V1 markets carry
# their token ids in clobTokenIds. Protocol V2 markets (from 2026-11-02) set
# clobTokenIds to null and carry positionIds instead; whether /book and the
# resolution fields work the same for them is unconfirmed, so they are
# skipped until read-only V2 support lands. A market with no version predates
# the tag and is V1.
SUPPORTED_VERSIONS = {"v1"}


def market_version(market):
    return market.get("version") or "v1"


def token_ids(market):
    """CLOB token ids of a gamma market record in outcome order, or None when
    the market is on an unsupported protocol version or its ids are unusable."""
    if market_version(market) not in SUPPORTED_VERSIONS:
        return None
    try:
        ids = json.loads(market.get("clobTokenIds") or "null")
        outcomes = json.loads(market.get("outcomes") or "null")
    except (ValueError, TypeError):
        return None
    if not (isinstance(ids, list) and isinstance(outcomes, list)
            and ids and len(ids) == len(outcomes)):
        return None
    return ids


def market_tokens(market):
    """Map outcome name -> clob token id for a gamma market record, or None
    when token_ids() cannot read the market."""
    ids = token_ids(market)
    if ids is None:
        return None
    return dict(zip(json.loads(market["outcomes"]), ids))
