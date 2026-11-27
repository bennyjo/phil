"""Agent variants for core/edge_board.py (contract in its header).

tight-cap10 (DEEP-2026-11-27): on a tight book (ask - bid <= 0.06) the recorded
estimate is clipped to mid +/- 0.10. Evidence: 30-day tight-book dBrier is
+0.0043 [+0.0011, +0.0074] (scoreboard 2026-11-27, n=1359, 369 events), and
the 116 rows with |est - mid| >= 0.10 carry +5.61 of the +5.78 summed deficit;
rows under 0.10 net to ~0. Held-out paired test on rows settled before that
window: -0.0251 [-0.0525, +0.0024] over 124 events (225 rows).
"""

TIGHT_SPREAD = 0.06
CAP = 0.10


def fit_none(history):
    return None


def predict_tight_cap10(row, _state):
    bid, ask = row.get("best_bid_at_record"), row.get("best_ask_at_record")
    if bid is None or ask is None or round(ask - bid, 4) > TIGHT_SPREAD:
        return None
    mid, est = row["market_prob_at_record"], row["est_prob"]
    return min(max(est, mid - CAP), mid + CAP)


VARIANTS = {"tight-cap10": (fit_none, predict_tight_cap10)}
# tight-cap10 had its reserved check 2026-11-27 (SHADOW n=49 events=27, journal/replay/trials.jsonl);
# taken out so later edits spend no check.
RESERVED = []
