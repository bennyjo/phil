#!/usr/bin/env python3
"""Scoring & calibration report over settled paper positions.

PROTECTED CORE — the trading agent must not edit files under core/.

Reports, overall and per category:
  n, win rate, P&L, ROI, mean Brier (agent) vs mean Brier (market price at
  entry) — the single most important number: negative brier_delta means the
  agent's estimates beat the market's own price as a forecast.
Also a calibration table (est-prob buckets vs realized frequency) and
per-strategy-revision P&L so self-improvement is measurable across commits.

Usage: python3 core/score.py [--json]
"""
import argparse
import json
import pathlib
from collections import defaultdict

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    entries = [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()] \
        if LEDGER.exists() else []
    settled = [e for e in entries if e["status"] in ("won", "lost")]
    if not settled:
        print(json.dumps({"settled": 0, "open": sum(1 for e in entries if e["status"] == "open")}))
        return

    report = {"overall": stats(settled), "by_category": {}, "by_strategy_rev": {},
              "calibration": []}
    by_cat = defaultdict(list)
    by_rev = defaultdict(list)
    for e in settled:
        by_cat[e["category"]].append(e)
        by_rev[e.get("strategy_rev") or "unknown"].append(e)
    for cat, es in sorted(by_cat.items()):
        report["by_category"][cat] = stats(es)
    for rev, es in sorted(by_rev.items()):
        report["by_strategy_rev"][rev] = stats(es)

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
