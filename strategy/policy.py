"""Betting policy over frozen forecast beliefs (scored by core/replay.py).

AGENT-EDITABLE. Given a recorded forecast (belief est_prob plus the book at
record time), decide whether to bet, which side, and how much. Beliefs are
frozen; only the decision rule evolves. Keep a change only if the held-out
walk-forward score from `python3 core/replay.py` improves.

Contract: decide(row, state) -> None | {"side": "yes"|"no", "stake_usd": x}
Optional fit(history) -> state for walk-forward-learned parameters.

Rules (v3, 2026-09-02):
  1. Both sides are candidates. Yes fills at the ask; No fills at 1 - bid.
     Edge = belief for the side minus its fill price.
  2. Bet only in the small-edge band 0.02 <= edge <= 0.07. Larger claimed
     edges are where the beliefs are overconfident: the >0.10 band is 0W/5L
     in the bet ledger and net negative in every veto counterfactual, and on
     replay 0.07-0.10 adds bets without adding return.
  3. Fill price must sit in 0.10..0.90. Below 0.10 the beliefs carry the
     classic longshot bias (0 for 16 on replay across both sides); above
     0.90 the payoff cannot cover the miss rate.
  4. Never buy a token priced 0.20 <= price < 0.45, on either side (v3).
     This is the mid-longshot zone and the beliefs are badly miscalibrated
     there: over every settled row with a non-negative edge on that side
     (78 rows, any spread, any edge size) the bought token wins 18% of the
     time at a mean price of 0.32 and a mean belief of 0.39, for -0.49 per
     $1 staked. Yes side: 45 rows, 16% wins. No side: 33 rows, 21% wins.
     Every neighbouring boundary (0.15/0.25 low, 0.40/0.47/0.50 high) also
     beats v2, so the zone is a plateau, not a tuned edge. The 0.10-0.20
     band stays open: it is thin (about 25 rows universe-wide) but net
     positive on both sides.
  5. Spread (ask - bid) <= 0.03. A wide book means the recorded ask is not
     a real price, and on the frozen beliefs every spread bucket from 0.03
     to 0.07 is net negative across all candidates (35 rows, -12.3 per $1
     staked) while 0.00-0.02 is positive. The cap is inclusive and the
     spread is rounded to 4 places first: half the 3-cent books fail a raw
     float comparison.
  6. Flat $5 stake. Edge-scaled, Kelly, price-scaled, price-tiered and
     max-stake sizing all lowered the held-out score. Price-tiered ($10
     above 0.5, $2 below) is the most robust sizing without the Bank of
     Israel rows (+0.168 / +0.143) but costs 0.14 of headline cw_return.

Replay scores below are IN-SAMPLE. Every threshold was chosen with all
420 settled rows visible and the policy has no fit() step, so the
walk-forward split holds nothing out from the rule selection. The first
out-of-sample evidence is the forecasts still open on 2026-09-02.
Replay (5 folds, 420 settled rows, 336 in scored folds): cw_return +0.743,
pnl +121.68 on 19 bets, brier_delta -0.0248. 10 folds: +0.624.
Without the Bank of Israel rows: +0.388 (5 folds) / +0.287 (10 folds),
the first version that is clearly positive on that check.
v2 (no dead zone) scored +0.345 / +0.240 with pnl +101.83 on 26 bets,
and +0.033 / -0.047 without the Bank of Israel rows.
v1 (spread <= 0.06) scored +0.239 / +0.155 with pnl +92.93 on 29 bets.
Baseline (the written risk.json rules: Yes only, edge 0.04-0.10, flat $5)
scores -0.506 held out, pnl -3.06 on 10 bets.
Caveat: two sibling Bank of Israel rows at price 0.12 contribute +73 of
the pnl; the no-Bank-of-Israel numbers above are the robustness check.
Rejected in the v3 round (lower headline score, or a gain that vanished
without the Bank of Israel rows): a 6h/24h/48h floor on time to
resolution, a walk-forward calibration shrinkage toward the market mid
(history Brier picks a factor near 0, so it kills almost every bet),
MIN_PRICE 0.30/0.45/0.50, MAX_PRICE 0.95, MIN_EDGE 0.015/0.025, MAX_EDGE
0.08/0.10, spread cap 0.02, requiring fit_score, preferring the No side
when both qualify.
"""

MIN_EDGE = 0.02
MAX_EDGE = 0.07
MIN_PRICE = 0.10
MAX_PRICE = 0.90
DEAD_ZONE = (0.20, 0.45)  # never buy a token priced in [lo, hi)
MAX_SPREAD = 0.03
STAKE_USD = 5.0


def candidates(row):
    """Both sides with their fill price and edge, or None if no book."""
    ask, bid = row.get("best_ask_at_record"), row.get("best_bid_at_record")
    if ask is None or bid is None:
        return None
    p = row["est_prob"]
    no_price = round(1 - bid, 4)
    return ask, bid, [("yes", ask, p - ask), ("no", no_price, (1 - p) - no_price)]


def decide(row, state=None):
    c = candidates(row)
    if not c:
        return None
    ask, bid, sides = c
    if round(ask - bid, 4) > MAX_SPREAD:
        return None
    for side, price, edge in sides:
        if not MIN_EDGE <= edge <= MAX_EDGE:
            continue
        if not MIN_PRICE <= price <= MAX_PRICE:
            continue
        if DEAD_ZONE[0] <= price < DEAD_ZONE[1]:
            continue
        return {"side": side, "stake_usd": STAKE_USD}
    return None
