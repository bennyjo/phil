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


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def book_quote(token_id):
    """Best bid and ask of a CLOB token (None if a side is empty), with the
    book's min_order_size (shares) and tick_size, each None when absent."""
    book = clob_book(token_id)
    bids = [float(b["price"]) for b in book.get("bids", [])]
    asks = [float(a["price"]) for a in book.get("asks", [])]
    return {"bid": max(bids) if bids else None, "ask": min(asks) if asks else None,
            "min_order_size": _float(book.get("min_order_size")),
            "tick_size": _float(book.get("tick_size"))}


def last_trade_price(token_id):
    """Last traded price of a CLOB token, None if it never traded. The book's
    own last_trade_price is market-wide (both outcome books of a market
    carry the same value), so read this per-token endpoint instead; it
    answers a never-traded token with a "0.5" placeholder and an empty side."""
    r = get_json(f"{CLOB}/last-trade-price", {"token_id": token_id})
    return _float(r.get("price")) if r.get("side") else None


def best_prices(token_id):
    """Return (best_bid, best_ask) for a CLOB token, None if side empty."""
    q = book_quote(token_id)
    return q["bid"], q["ask"]


# docs.polymarket.com/concepts/prices-orderbook: "The displayed price is the
# midpoint of the bid-ask spread. If the spread is wider than $0.10, the last
# traded price is shown instead." A one-sided book has no spread, so it shows
# the last trade too; with no last trade, fall back to whatever the book has.
DISPLAY_MAX_SPREAD = 0.10


def displayed_price(token_id, bid, ask):
    """(price, source) Polymarket displays for a token's book: source is
    "mid", "last_trade", or "book" for the no-trade fallback; price is None
    for an empty, never-traded book. Fetches the last trade only when used."""
    two_sided = bid is not None and ask is not None
    if two_sided and round(ask - bid, 4) <= DISPLAY_MAX_SPREAD:
        return (bid + ask) / 2, "mid"
    last = last_trade_price(token_id)
    if last is not None:
        return last, "last_trade"
    return ((bid + ask) / 2 if two_sided else bid if bid is not None else ask), "book"


def taker_fee_per_share(market, price):
    """Taker fee in USDC per share bought at price, from the Gamma market record.

    docs.polymarket.com/trading/fees: "fee = C x feeRate x p x (1 - p)" on
    markets with feesEnabled; market-details documents feeSchedule.rate and an
    exponent "applied to the price component". Raises ValueError when fees are
    enabled but the record carries no usable rate, so a fill never assumes zero.
    """
    if not market.get("feesEnabled"):
        return 0.0
    sched = market.get("feeSchedule") or {}
    rate, exponent = _float(sched.get("rate")), _float(sched.get("exponent", 1))
    if rate is None or exponent is None:
        raise ValueError(f"feesEnabled but feeSchedule is {sched!r}")
    return rate * (price * (1 - price)) ** exponent


# Gamma tags each market with the CLOB protocol it trades on, and the version
# alone selects the outcome ids: clobTokenIds for "v1", positionIds for "v2".
# Both fields can be populated, so their presence does not select the
# protocol (docs.polymarket.com/market-data/market-details). Whether /book and
# the resolution fields work the same for V2 is unconfirmed, so V2 markets are
# skipped until read-only V2 support lands. The V2 migration guide says to
# "Reject missing or unsupported versions", so an untagged market is rejected
# too (market_version returns None).
SUPPORTED_VERSIONS = {"v1"}


def market_version(market):
    return market.get("version")


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
