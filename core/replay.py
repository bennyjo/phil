#!/usr/bin/env python3
"""Walk-forward replay of a betting policy over the frozen forecast ledger.

PROTECTED CORE — the trading agent must not edit files under core/.

The forecast ledger (journal/forecasts.jsonl) records every researched
candidate with the agent's belief (est_prob) and the book at record time
(best_bid/best_ask). Beliefs are frozen; this tool asks only "given those
beliefs, which bets should have been placed, on which side, and how big?"
and scores a policy module (default strategy/policy.py) on held-out data.

Policy contract (strategy/policy.py):
  fit(history) -> state        optional; history = settled rows the policy
                               may learn from (all rows strictly before the
                               fold being scored, WITH outcomes in `won`).
  decide(row, state) -> None | {"side": "yes" | "no", "stake_usd": float}
                               row = the forecast as recorded, outcome
                               fields stripped. None = no bet.

Fill model (mirrors core/ledger.py: honest CLOB fills, no mid):
  yes  buys the recorded outcome token at best_ask_at_record
  no   buys the complement at (1 - best_bid_at_record)
  pnl  = stake / price - stake if the side wins, else -stake
Protected caps (config/protected.json) apply: stake is clipped to
max_stake_usd, entries outside [min_entry_price, max_entry_price], banned
question patterns and < min_minutes_to_resolution are rejected (no fill).

Walk-forward: settled rows are sorted by record time and cut into K
contiguous folds. Fold 0 is training-only. For each later fold the policy
is fitted on every earlier fold and scored on that fold. The held-out
score is the aggregate over folds 1..K-1.

Reported on the held-out set:
  n_bets, staked, pnl, roi = pnl / staked (stake-weighted return),
  cw_return = roi - 1 stake-weighted standard error of the per-bet return
              (the selection score: a policy must be robustly, not luckily,
              positive; zero bets scores 0),
  brier_delta = mean Brier(est_prob) - mean Brier(market mid at record)
              over the rows the policy bet on (negative = the beliefs the
              policy chose to act on beat the market).

Usage: python3 core/replay.py [--policy PATH] [--folds K] [--json] [--bets]
"""
import argparse
import datetime as dt
import importlib.util
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORECASTS = ROOT / "journal" / "forecasts.jsonl"
PROTECTED = json.loads((ROOT / "config" / "protected.json").read_text())
DEFAULT_POLICY = ROOT / "strategy" / "policy.py"

OUTCOME_FIELDS = ("status", "outcome_won", "settled_ts", "superseded_by",
                  "superseded_ts")


def _parse_ts(s):
    """ISO-8601 UTC timestamp; end_date may carry fractional seconds."""
    if s.endswith("Z"):
        s = s[:-1]
    return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)


def load_rows():
    """Settled, fillable, non-superseded forecasts in record-time order."""
    rows = []
    with open(FORECASTS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("status") not in ("won", "lost"):
                continue
            if r.get("superseded_by"):
                continue  # a later belief on the same market replaced it
            if r.get("best_ask_at_record") is None:
                continue  # no book at record time: nothing could fill
            rows.append(r)
    rows.sort(key=lambda r: (r["ts"], r["id"]))
    return rows


def visible(r):
    """The row as the policy may see it: no outcome, no supersession."""
    return {k: v for k, v in r.items() if k not in OUTCOME_FIELDS}


def history_row(r):
    h = visible(r)
    h["won"] = r["status"] == "won"
    return h


def load_policy(path):
    spec = importlib.util.spec_from_file_location("replay_policy", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "decide"):
        sys.exit(f"policy {path} has no decide(row, state)")
    return mod


_BANNED = [re.compile(p) for p in PROTECTED["banned_question_patterns"]]


def fill(r, decision):
    """Apply the protected caps and the honest fill model.

    Returns (price, stake, pnl) or None if the bet is rejected/unfillable.
    """
    if not decision:
        return None
    side = decision.get("side")
    stake = float(decision.get("stake_usd", 0) or 0)
    if side not in ("yes", "no") or stake <= 0:
        return None
    stake = min(stake, PROTECTED["max_stake_usd"])
    if any(p.search(r["question"]) for p in _BANNED):
        return None
    try:
        minutes = (_parse_ts(r["end_date"]) - _parse_ts(r["ts"])).total_seconds() / 60
    except (KeyError, TypeError, ValueError):
        minutes = None
    if minutes is not None and minutes < PROTECTED["min_minutes_to_resolution"]:
        return None
    if side == "yes":
        price = r["best_ask_at_record"]
        wins = r["status"] == "won"
    else:
        bid = r.get("best_bid_at_record")
        if bid is None:
            return None
        price = round(1 - bid, 4)
        wins = r["status"] == "lost"
    if price is None or not PROTECTED["min_entry_price"] <= price <= PROTECTED["max_entry_price"]:
        return None
    pnl = stake / price - stake if wins else -stake
    return price, stake, pnl


def market_prob(r):
    """The market's own forecast at record time: the recorded mid, else the
    bid/ask midpoint. Never the ask alone, which would bias the Brier
    baseline against the market."""
    if r.get("market_prob_at_record") is not None:
        return r["market_prob_at_record"]
    bid, ask = r.get("best_bid_at_record"), r.get("best_ask_at_record")
    return (bid + ask) / 2 if bid is not None else ask


def summarize(bets):
    """bets: list of dicts with stake, pnl, est_prob, market_prob, won."""
    n = len(bets)
    if n == 0:
        return {"n_bets": 0, "staked": 0.0, "pnl": 0.0, "roi": 0.0,
                "cw_return": 0.0, "brier_delta": None, "win_rate": None}
    staked = sum(b["stake"] for b in bets)
    pnl = sum(b["pnl"] for b in bets)
    roi = pnl / staked
    # stake-weighted standard error of the per-bet return
    var = sum((b["stake"] * (b["pnl"] / b["stake"] - roi)) ** 2 for b in bets)
    se = math.sqrt(var) / staked if n > 1 else 1.0
    ba = sum((b["est_prob"] - b["won"]) ** 2 for b in bets) / n
    bm = sum((b["market_prob"] - b["won"]) ** 2 for b in bets) / n
    return {
        "n_bets": n, "staked": round(staked, 2), "pnl": round(pnl, 2),
        "roi": round(roi, 4), "cw_return": round(roi - se, 4),
        "brier_delta": round(ba - bm, 4),
        "win_rate": round(sum(b["won_bet"] for b in bets) / n, 3),
    }


def replay(policy, rows, folds):
    if folds < 2:
        sys.exit("--folds must be >= 2")
    size = math.ceil(len(rows) / folds)
    chunks = [rows[i:i + size] for i in range(0, len(rows), size)]
    fit = getattr(policy, "fit", None)
    per_fold, held_out = [], []
    for k in range(1, len(chunks)):
        train = [history_row(r) for c in chunks[:k] for r in c]
        state = fit(train) if fit else None
        bets = []
        for r in chunks[k]:
            filled = fill(r, policy.decide(visible(r), state))
            if not filled:
                continue
            price, stake, pnl = filled
            won = 1 if r["status"] == "won" else 0
            bets.append({
                "id": r["id"], "stake": stake, "pnl": pnl, "price": price,
                "est_prob": r["est_prob"],
                "market_prob": market_prob(r),
                "won": won, "won_bet": 1 if pnl > 0 else 0,
                "side": "yes" if price == r["best_ask_at_record"] else "no",
                "category": r.get("category"), "question": r["question"][:60],
            })
        s = summarize(bets)
        s.update({"fold": k, "n_rows": len(chunks[k]),
                  "from": chunks[k][0]["ts"][:10], "to": chunks[k][-1]["ts"][:10]})
        per_fold.append(s)
        held_out.extend(bets)
    agg = summarize(held_out)
    agg["n_rows"] = sum(len(c) for c in chunks[1:])
    return {"folds": per_fold, "held_out": agg, "n_rows_total": len(rows),
            "train_only_rows": len(chunks[0]), "bets": held_out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=str(DEFAULT_POLICY))
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--bets", action="store_true", help="list every held-out bet")
    a = ap.parse_args()
    rows = load_rows()
    report = replay(load_policy(a.policy), rows, a.folds)
    if a.json:
        print(json.dumps(report, indent=1))
        return
    if a.bets:
        for b in report["bets"]:
            print(f"  {b['id']} {b['side']:>3} px={b['price']:.3f} est={b['est_prob']:.3f} "
                  f"stake={b['stake']:.2f} pnl={b['pnl']:+7.2f} {b['category']:<24} {b['question']}")
    print(f"replay: {report['n_rows_total']} settled forecasts, {a.folds} walk-forward folds "
          f"(fold 0 = {report['train_only_rows']} rows, train only)")
    hdr = f"{'fold':>4} {'dates':<23} {'rows':>4} {'bets':>4} {'staked':>7} {'pnl':>8} {'roi':>7} {'cw_ret':>7} {'dBrier':>8}"
    print(hdr)
    for s in report["folds"]:
        bd = "-" if s["brier_delta"] is None else f"{s['brier_delta']:+.4f}"
        print(f"{s['fold']:>4} {s['from']}..{s['to']:<11} {s['n_rows']:>4} {s['n_bets']:>4} "
              f"{s['staked']:>7.2f} {s['pnl']:>+8.2f} {s['roi']:>+7.3f} {s['cw_return']:>+7.3f} {bd:>8}")
    h = report["held_out"]
    bd = "-" if h["brier_delta"] is None else f"{h['brier_delta']:+.4f}"
    print(f"{'HELD':>4} {'out (folds 1..K-1)':<23} {h['n_rows']:>4} {h['n_bets']:>4} "
          f"{h['staked']:>7.2f} {h['pnl']:>+8.2f} {h['roi']:>+7.3f} {h['cw_return']:>+7.3f} {bd:>8}")
    print(f"score (held-out cw_return): {h['cw_return']:+.4f}   pnl {h['pnl']:+.2f}   "
          f"brier_delta {bd}   bets {h['n_bets']}/{h['n_rows']}")


if __name__ == "__main__":
    main()
