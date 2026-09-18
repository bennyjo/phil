#!/usr/bin/env python3
"""Driftless reflection-principle touch probability with a SOURCED vol input.

Usage:
  python3 strategy/tools/touch.py --spot 76074 --barrier 75000 --days 13 \
      --ann-vol 0.4725 --vol-source "Glassnode 1m realized vol, 2026-09-07"

Why (RETRO-20260918-1410): the touch-family ruling (DEEP-2026-09-01) retired
guessed-vol inputs, yet 4 of the 6 modeled crypto touch rows recorded after
it (dde658c37455, 61bc26d805b6, a28637cb4026, 8d1eb46b7c32) still used a
guessed or swept vol typed into a back-of-envelope formula. This tool is the
formula, and it refuses to run without a named vol source, so the note a
forecast quotes always carries one. It also prints the estimate at 0.75x and
1.25x the vol: if the sign of the edge flips inside that band, the row has no
robust disagreement with the market.

P(touch) = 2 * (1 - Phi(|ln(B/S)| / (sigma * sqrt(T)))). For commodity
ladders pass the ACTIVE-MONTH contract price as --spot (playbook, 2026-09-17)
and --year-days 252 with --days counted in sessions.

The output is a forecast input only: the family stays `unvalidated-method`
forecast-only until the ruling's re-grade bar is met.
"""
import argparse
import json
import math
import sys


def p_touch(spot, barrier, days, ann_vol, year_days):
    sd = ann_vol * math.sqrt(days / year_days)
    d = abs(math.log(barrier / spot)) / sd
    return math.erfc(d / math.sqrt(2))  # == 2 * (1 - Phi(d))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spot", type=float, required=True)
    ap.add_argument("--barrier", type=float, required=True)
    ap.add_argument("--days", type=float, required=True)
    ap.add_argument("--ann-vol", type=float, required=True,
                    help="annualized vol as a fraction, e.g. 0.47")
    ap.add_argument("--vol-source", required=True,
                    help="named, dated source of the vol number")
    ap.add_argument("--year-days", type=float, default=365.0)
    a = ap.parse_args(argv)
    if len(a.vol_source.strip()) < 8:
        ap.error("--vol-source must name a dated source (guessed vol is retired)")
    if not (a.spot > 0 and a.barrier > 0 and a.days > 0 and 0 < a.ann_vol < 5):
        ap.error("spot, barrier, days must be > 0 and ann-vol a fraction in (0, 5)")
    out = {
        "p_touch": round(p_touch(a.spot, a.barrier, a.days, a.ann_vol, a.year_days), 4),
        "p_touch_vol_x0.75": round(
            p_touch(a.spot, a.barrier, a.days, a.ann_vol * 0.75, a.year_days), 4),
        "p_touch_vol_x1.25": round(
            p_touch(a.spot, a.barrier, a.days, a.ann_vol * 1.25, a.year_days), 4),
        "gap_pct": round(100 * (a.barrier / a.spot - 1), 3),
        "ann_vol": a.ann_vol,
        "vol_source": a.vol_source.strip(),
        "skip_reason": "unvalidated-method",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
