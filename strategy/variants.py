"""Agent variants for core/edge_board.py (contract in its header).

tight-cap10 (DEEP-2026-11-27): on a tight book (ask - bid <= 0.06) the recorded
estimate is clipped to mid +/- 0.10. Evidence: 30-day tight-book dBrier is
+0.0043 [+0.0011, +0.0074] (scoreboard 2026-11-27, n=1359, 369 events), and
the 116 rows with |est - mid| >= 0.10 carry +5.61 of the +5.78 summed deficit;
rows under 0.10 net to ~0. Held-out paired test on rows settled before that
window: -0.0251 [-0.0525, +0.0024] over 124 events (225 rows).

DEEP-2026-11-28 candidates (development columns only; see the retro (d)):
  tight-cap05     clip to mid +/- 0.05 on tight books (I-20261128-0600-3).
  tight-soft10    keep 25% of the excess beyond mid +/- 0.10 (I-20261128-0600-3).
  stack-spread    logit pool (stack) fitted separately on tight and wide
                  books (I-20261128-0600-1, Satopaa et al. 2014 logit pooling).
  stack-horizon   stack fitted separately for rows under and over 24h to the
                  end date (FLB worsens with horizon, Princeton thesis 2026;
                  I-20261128-0600-2).
  tail-defer      on tight books with mid <= 0.15 or >= 0.85, use the mid
                  (favourite-longshot literature, I-20261128-0600-2).
"""
import math

TIGHT_SPREAD = 0.06
CAP = 0.10


def _tight(row):
    bid, ask = row.get("best_bid_at_record"), row.get("best_ask_at_record")
    return bid is not None and ask is not None and round(ask - bid, 4) <= TIGHT_SPREAD


def fit_none(history):
    return None


def _clip(row, cap, keep=0.0):
    if not _tight(row):
        return None
    mid, est = row["market_prob_at_record"], row["est_prob"]
    lo, hi = mid - cap, mid + cap
    if est > hi:
        return hi + keep * (est - hi)
    if est < lo:
        return lo - keep * (lo - est)
    return est


def predict_tight_cap10(row, _state):
    return _clip(row, CAP)


def predict_tight_cap05(row, _state):
    return _clip(row, 0.05)


def predict_tight_soft10(row, _state):
    return _clip(row, CAP, keep=0.25)


def _logit(p):
    p = min(max(p, 0.005), 0.995)
    return math.log(p / (1 - p))


def _fit_ab(data):
    a, b = 1.0, 0.0
    for _ in range(25):
        ga = gb = haa = hab = hbb = 0.0
        for xm, xe, y in data:
            p = 1 / (1 + math.exp(-(a * xm + b * xe)))
            w = p * (1 - p)
            ga += (y - p) * xm
            gb += (y - p) * xe
            haa += w * xm * xm
            hab += w * xm * xe
            hbb += w * xe * xe
        haa, hbb = haa + 1e-6, hbb + 1e-6
        det = haa * hbb - hab * hab
        da, db = (hbb * ga - hab * gb) / det, (haa * gb - hab * ga) / det
        a, b = a + da, b + db
        if abs(da) + abs(db) < 1e-6:
            break
    return a, b


def fit_stack_spread(history):
    seg = {True: [], False: []}
    for h in history:
        seg[_tight(h)].append((_logit(h["market_prob_at_record"]), _logit(h["est_prob"]),
                               float(h["won"])))
    return {k: (_fit_ab(v) if len(v) >= 50 else None) for k, v in seg.items()}


def predict_stack_spread(row, state):
    ab = state.get(_tight(row))
    if ab is None:
        return None
    a, b = ab
    z = a * _logit(row["market_prob_at_record"]) + b * _logit(row["est_prob"])
    return 1 / (1 + math.exp(-z))


def _long(row):
    end, ts = row.get("end_date") or "", row.get("ts") or ""
    try:
        import datetime as dt
        e = dt.datetime.fromisoformat(end[:19])
        t = dt.datetime.fromisoformat(ts[:19])
    except ValueError:
        return None
    return (e - t).total_seconds() > 86400


def fit_stack_horizon(history):
    seg = {True: [], False: []}
    for h in history:
        k = _long(h)
        if k is not None:
            seg[k].append((_logit(h["market_prob_at_record"]), _logit(h["est_prob"]),
                           float(h["won"])))
    return {k: (_fit_ab(v) if len(v) >= 50 else None) for k, v in seg.items()}


def predict_stack_horizon(row, state):
    k = _long(row)
    ab = state.get(k) if k is not None else None
    if ab is None:
        return None
    a, b = ab
    z = a * _logit(row["market_prob_at_record"]) + b * _logit(row["est_prob"])
    return 1 / (1 + math.exp(-z))


def predict_tail_defer(row, _state):
    if not _tight(row):
        return None
    mid = row["market_prob_at_record"]
    return mid if (mid <= 0.15 or mid >= 0.85) else None


VARIANTS = {
    "tight-cap10": (fit_none, predict_tight_cap10),
    "tight-cap05": (fit_none, predict_tight_cap05),
    "tail-defer": (fit_none, predict_tail_defer),
}
# tight-cap10 had its reserved check 2026-11-27 (SHADOW n=49 events=27, journal/replay/trials.jsonl).
# Reserved checks 2026-11-28: tight-cap05 PASS n=148 events=64, tail-defer SHADOW n=225 events=100
# (journal/replay/trials.jsonl). tight-soft10, stack-spread and stack-horizon were dropped on the
# development columns (no gain over tight-cap10 / built-in stack); their code stays for the record.
RESERVED = []
