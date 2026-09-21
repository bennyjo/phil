#!/usr/bin/env python3
"""Settle open paper positions AND forecasts against official Polymarket resolutions.

PROTECTED CORE — the trading agent must not edit files under core/.

For each open row (bets in journal/ledger.jsonl, stake-free forecasts in
journal/forecasts.jsonl), fetch the market; if it is closed with a decisive
outcome price (>=0.99 for one side), settle won/lost. Markets closed without
decisive prices (disputed/void) settle as void after a grace period (stake
returned for bets; forecasts are excluded from scoring). Rewrites both files
in place (single writer, alongside ledger.py/forecast.py appends).

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
FORECASTS = ROOT / "journal" / "forecasts.jsonl"
VOID_GRACE_HOURS = 48


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def dump_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _iso_z(value):
    """Normalise a gamma timestamp ('2026-09-21 06:12:04+00', ISO with Z or an
    offset) to the journal's 'YYYY-MM-DDTHH:MM:SSZ' form. None when unparseable."""
    if not value or not isinstance(value, str):
        return None
    s = value.strip().replace(" ", "T").replace("Z", "+00:00")
    if s[-3:] in ("+00", "-00"):
        s += ":00"
    try:
        t = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def settlement_ts(m, now):
    """The market's own close time, so two runners settling the same row write
    identical rows (2026-09-21: the cloud routine and the operator loop settled
    the same forecast in the same minute, differed only in a wall-clock
    settled_ts, and forecasts.jsonl is deliberately not union-merged, so the
    operator loop's rebase aborted). Falls back to the wall clock when gamma
    carries no close time."""
    return (_iso_z(m.get("closedTime")) or _iso_z(m.get("umaEndDate"))
            or now.strftime("%Y-%m-%dT%H:%M:%SZ"))


def settle_against_market(e, m, now):
    """Settle one open row against a fetched gamma market. Returns True if settled.

    Bet rows (those with "shares") also get pnl_usd; forecast rows don't.
    settled_ts is the market's close time (deterministic across runners);
    noticed_ts is when this runner saw it, which is what settlement-duty
    timing in retros should use.
    """
    if not m.get("closed"):
        return False
    outcomes = json.loads(m.get("outcomes", "[]"))
    prices = [float(p) for p in json.loads(m.get("outcomePrices", "[]"))]
    decisive = {o: p for o, p in zip(outcomes, prices) if p >= 0.99}
    if decisive:
        won = e["outcome"] in decisive
        e["status"] = "won" if won else "lost"
        e["settled_ts"] = settlement_ts(m, now)
        e["noticed_ts"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        if "shares" in e:
            e["pnl_usd"] = round(e["shares"] - e["stake_usd"], 4) if won else -e["stake_usd"]
        e["outcome_won"] = max(zip(prices, outcomes))[1]
        return True
    end = dt.datetime.fromisoformat(e["end_date"].replace("Z", "+00:00"))
    if now - end > dt.timedelta(hours=VOID_GRACE_HOURS):
        e["status"] = "void"
        # Deterministic too: the void boundary is a pure function of end_date.
        e["settled_ts"] = (end + dt.timedelta(hours=VOID_GRACE_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        e["noticed_ts"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        if "shares" in e:
            e["pnl_usd"] = 0.0
        return True
    return False


def main():
    entries = load_jsonl(LEDGER)
    forecasts = load_jsonl(FORECASTS)
    if not entries and not forecasts:
        print("resolve: no ledger yet")
        return
    now = dt.datetime.now(dt.timezone.utc)

    market_cache = {}

    def get_market(market_id):
        if market_id not in market_cache:
            try:
                market_cache[market_id] = pmapi.gamma_market(market_id)
            except RuntimeError as err:
                print(f"resolve: fetch failed for {market_id}: {err}", file=sys.stderr)
                market_cache[market_id] = None
        return market_cache[market_id]

    settled, fsettled = [], []
    for e in entries:
        if e["status"] != "open":
            continue
        m = get_market(e["market_id"])
        if m is not None and settle_against_market(e, m, now):
            settled.append(e)
    for r in forecasts:
        if r["status"] != "open":
            continue
        m = get_market(r["market_id"])
        if m is not None and settle_against_market(r, m, now):
            fsettled.append(r)

    dump_jsonl(LEDGER, entries)
    if forecasts:
        dump_jsonl(FORECASTS, forecasts)

    for e in settled:
        print(f"{e['status'].upper():5} {e['pnl_usd']:+7.2f}  est={e['est_prob']:.2f} "
              f"mkt={e['entry_price']:.2f}  [{e['category']}] {e['question'][:70]}")
    for r in fsettled:
        print(f"FCAST {r['status'].upper():5} est={r['est_prob']:.2f} "
              f"mkt={r['market_prob_at_record']:.2f}  [{r['category']}] {r['question'][:70]}")
    print(f"resolve: settled {len(settled)} of {sum(1 for e in entries if e['status'] != 'open') + len(settled)} "
          f"({sum(1 for e in entries if e['status'] == 'open')} still open); "
          f"forecasts settled {len(fsettled)} "
          f"({sum(1 for r in forecasts if r['status'] == 'open')} still open)")


if __name__ == "__main__":
    main()
