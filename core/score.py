#!/usr/bin/env python3
"""Scoring & calibration report over settled paper positions.

PROTECTED CORE — the trading agent must not edit files under core/.

Reports, overall and per category:
  n, win rate, P&L, ROI, mean Brier (agent) vs mean Brier (market price at
  entry) — the single most important number: negative brier_delta means the
  agent's estimates beat the market's own price as a forecast.
Also a calibration table (est-prob buckets vs realized frequency) and
per-strategy-revision P&L so self-improvement is measurable across commits.

Usage: python3 core/score.py [--json] [--skip-mtm]
"""
import argparse
import datetime as dt
import json
import math
import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "journal" / "ledger.jsonl"


def stats(entries):
    n = len(entries)
    wins = sum(1 for e in entries if e["status"] == "won")
    pnl = sum(e["pnl_usd"] for e in entries)
    staked = sum(e["stake_usd"] for e in entries)
    brier_agent = sum((e["est_prob"] - (1 if e["status"] == "won" else 0)) ** 2
                      for e in entries) / n
    brier_market = sum((e["market_prob_at_entry"] - (1 if e["status"] == "won" else 0)) ** 2
                       for e in entries) / n
    return {
        "n": n, "wins": wins, "win_rate": round(wins / n, 3),
        "pnl_usd": round(pnl, 2), "roi": round(pnl / staked, 3) if staked else 0,
        "brier_agent": round(brier_agent, 4), "brier_market": round(brier_market, 4),
        "brier_delta": round(brier_agent - brier_market, 4),
    }


def luck_adjusted(entries):
    """Expected wins under the agent's own estimates vs actual, as a z-score.

    Distinguishes "estimates were wrong" from "estimates were fine, variance
    hit": if every est_prob were exactly right, wins ~ sum(p) ± sqrt(sum p(1-p)).
    """
    exp = sum(e["est_prob"] for e in entries)
    var = sum(e["est_prob"] * (1 - e["est_prob"]) for e in entries)
    wins = sum(1 for e in entries if e["status"] == "won")
    z = (wins - exp) / math.sqrt(var) if var > 0 else 0.0
    return {"expected_wins": round(exp, 2), "actual_wins": wins, "z": round(z, 2)}


def mark_to_market(open_entries):
    """Best-effort live marks for open positions (needs network)."""
    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for e in open_entries:
        try:
            bid, ask = pmapi.best_prices(e["token_id"])
        except Exception as err:  # noqa: BLE001 — MTM is advisory, never fatal
            rows.append({"id": e["id"], "error": str(err)[:80]})
            continue
        mid = (bid + ask) / 2 if bid is not None and ask is not None else bid or ask or 0.0
        past_end = False
        try:
            past_end = dt.datetime.fromisoformat(e["end_date"].replace("Z", "+00:00")) < now
        except Exception:  # noqa: BLE001
            pass
        rows.append({
            "id": e["id"], "q": e["question"][:60], "outcome": e["outcome"],
            "entry": e["entry_price"], "mid": round(mid, 3),
            "cost_usd": e["stake_usd"], "mark_usd": round(e["shares"] * mid, 2),
            "unrealized_usd": round(e["shares"] * mid - e["stake_usd"], 2),
            "past_end_date": past_end,
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-mtm", action="store_true",
                    help="skip live mark-to-market of open positions (offline)")
    args = ap.parse_args()

    entries = [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()] \
        if LEDGER.exists() else []
    settled = [e for e in entries if e["status"] in ("won", "lost")]
    if not settled:
        print(json.dumps({"settled": 0, "open": sum(1 for e in entries if e["status"] == "open")}))
        return

    report = {"overall": stats(settled), "luck_adjusted": luck_adjusted(settled),
              "by_edge_class": {}, "by_category": {}, "by_strategy_rev": {},
              "calibration": []}
    by_class = defaultdict(list)
    by_cat = defaultdict(list)
    by_rev = defaultdict(list)
    for e in settled:
        by_class[e.get("edge_class") or "unclassified"].append(e)
        by_cat[e["category"]].append(e)
        by_rev[e.get("strategy_rev") or "unknown"].append(e)
    for cls, es in sorted(by_class.items()):
        report["by_edge_class"][cls] = stats(es)
    for cat, es in sorted(by_cat.items()):
        report["by_category"][cat] = stats(es)
    for rev, es in sorted(by_rev.items()):
        report["by_strategy_rev"][rev] = stats(es)

    open_pos = [e for e in entries if e["status"] == "open"]
    if open_pos and not args.skip_mtm:
        report["open_mtm"] = mark_to_market(open_pos)

    buckets = defaultdict(list)
    for e in settled:
        buckets[min(int(e["est_prob"] * 10), 9)].append(e)
    for b in sorted(buckets):
        es = buckets[b]
        report["calibration"].append({
            "est_range": f"{b/10:.1f}-{(b+1)/10:.1f}", "n": len(es),
            "realized": round(sum(1 for e in es if e["status"] == "won") / len(es), 3),
        })

    if args.json:
        print(json.dumps(report, indent=2))
        return
    o = report["overall"]
    print(f"settled={o['n']} win_rate={o['win_rate']} pnl=${o['pnl_usd']} roi={o['roi']}")
    print(f"brier: agent={o['brier_agent']} market={o['brier_market']} "
          f"delta={o['brier_delta']} ({'BEATING market' if o['brier_delta'] < 0 else 'behind market'})")
    la = report["luck_adjusted"]
    print(f"luck-adjusted: expected wins (own ests)={la['expected_wins']} "
          f"actual={la['actual_wins']} z={la['z']:+.2f}")
    print("\nby edge class:")
    for cls, s in report["by_edge_class"].items():
        print(f"  {cls:12} n={s['n']:3} win={s['win_rate']:.2f} pnl=${s['pnl_usd']:+8.2f} "
              f"brier_delta={s['brier_delta']:+.4f}")
    if report.get("open_mtm"):
        print("\nopen positions (live mark-to-market, advisory):")
        for r in report["open_mtm"]:
            if "error" in r:
                print(f"  {r['id']} MTM unavailable: {r['error']}")
                continue
            flag = " PAST END DATE" if r["past_end_date"] else ""
            print(f"  {r['id']} {r['outcome']:3} entry={r['entry']} mid={r['mid']} "
                  f"cost=${r['cost_usd']:.2f} mark=${r['mark_usd']:.2f} "
                  f"unrealized=${r['unrealized_usd']:+.2f}{flag}")
    print("\nby category:")
    for cat, s in report["by_category"].items():
        print(f"  {cat:12} n={s['n']:3} win={s['win_rate']:.2f} pnl=${s['pnl_usd']:+8.2f} "
              f"brier_delta={s['brier_delta']:+.4f}")
    print("\nby strategy rev:")
    for rev, s in report["by_strategy_rev"].items():
        print(f"  {rev[:8]:8} n={s['n']:3} pnl=${s['pnl_usd']:+8.2f} brier_delta={s['brier_delta']:+.4f}")
    print("\ncalibration (est vs realized):")
    for c in report["calibration"]:
        print(f"  {c['est_range']}: n={c['n']:3} realized={c['realized']:.2f}")


if __name__ == "__main__":
    main()
