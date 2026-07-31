#!/usr/bin/env python3
"""Devig bookmaker odds two ways: proportional and power.

Usage:
  python3 strategy/tools/devig.py 1.94 3.15 4.35          # decimal odds
  python3 strategy/tools/devig.py --probs 0.52 0.33 0.24  # raw implied probs

Why (DEEP-2026-07-31): proportional (divide-by-sum) devig spreads the vig
evenly across outcomes, but bookmakers load vig disproportionately onto
longshots (favorite-longshot bias). The power method — fair_i = raw_i^k with
k solved so the fair probs sum to 1 — shrinks small probabilities more,
typically pricing a sub-0.50 side 2-4 cents below the proportional number.
All 7 losing bets of 2026-07-30/31 bought the cheaper side off proportional
devigs. Use the POWER number as the estimate for any side priced below ~0.60;
the gap between the two methods is your devig-method uncertainty.
"""
import json
import sys


def power_devig(raw, tol=1e-10):
    """fair_i = raw_i^k, k solved by bisection so sum(fair) == 1."""
    lo, hi = 0.5, 20.0
    for _ in range(200):
        k = (lo + hi) / 2
        s = sum(p ** k for p in raw)
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            lo = k  # raw sums > 1: need larger k to shrink
        else:
            hi = k
    return [p ** k for p in raw], k


def main(argv):
    if argv and argv[0] == "--probs":
        raw = [float(x) for x in argv[1:]]
    else:
        raw = [1.0 / float(x) for x in argv]
    if len(raw) < 2 or any(not 0 < p < 1 for p in raw):
        sys.exit(__doc__)
    total = sum(raw)
    prop = [p / total for p in raw]
    powr, k = power_devig(raw)
    print(json.dumps({
        "raw_implied": [round(p, 4) for p in raw],
        "overround": round(total - 1.0, 4),
        "proportional": [round(p, 4) for p in prop],
        "power": [round(p, 4) for p in powr],
        "power_k": round(k, 4),
        "longshot_shading": [round(a - b, 4) for a, b in zip(prop, powr)],
    }))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1:])
