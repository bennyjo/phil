"""Touch-family shading rule: the probability to record from touch.py's raw output.

estimate(raw, mid, row) -> float in [0, 1]
  raw  touch.py's p_touch at the measured vol
  mid  the market's mid (displayed price) at forecast time
  row  {"spot", "barrier", "days", "ann_vol"}: the touch.py inputs, nothing more

`touch.py --mid <m>` prints this as p_rule. core/touch_replay.py (protected)
scores this file and touch.py against every resolved crypto touch market of
the last 90 days; CYCLE.md step 3 makes its PASS the bar for editing either.

Current rule: DEEP-2026-10-16 rule 1. Above the mid, record the mid plus half
the gap to the raw output; at or below the mid, record raw.
"""


def estimate(raw, mid, row):
    if raw > mid:
        return mid + 0.5 * (raw - mid)
    return raw
