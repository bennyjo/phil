"""Betting policy over frozen forecast beliefs (scored by core/replay.py).

AGENT-EDITABLE. Given a recorded forecast (belief est_prob plus the book at
record time), decide whether to bet, which side, and how much. Beliefs are
frozen; only the decision rule evolves. Keep a change only if the held-out
walk-forward score from `python3 core/replay.py` improves.

Contract: decide(row, state) -> None | {"side": "yes"|"no", "stake_usd": x}
Optional fit(history) -> state for walk-forward-learned parameters.

Rules (v2, 2026-09-02):
  1. Both sides are candidates. Yes fills at the ask; No fills at 1 - bid.
     Edge = belief for the side minus its fill price.
  2. Bet only in the small-edge band 0.02 <= edge <= 0.07. Larger claimed
     edges are where the beliefs are overconfident: the >0.10 band is 0W/5L
     in the bet ledger and net negative in every veto counterfactual, and on
     replay 0.07-0.10 adds bets without adding return.
  3. Fill price must sit in 0.10..0.90. Below 0.10 the beliefs carry the
     classic longshot bias (0 for 16 on replay across both sides); above
     0.90 the payoff cannot cover the miss rate.
  4. Spread (ask - bid) <= 0.03 (v2; v1 used the risk.json cap 0.06). A
     wide book means the recorded ask is not a real price, and on the
     frozen beliefs every spread bucket from 0.03 to 0.07 is net negative
     across all candidates (35 rows, -12.3 per $1 staked) while 0.00-0.02
     is positive. The cap is inclusive and the spread is rounded to 4
     places first: half the 3-cent books fail a raw float comparison.
  5. Flat $5 stake. Edge-scaled, Kelly, price-scaled and max-stake sizing
     all lowered or did not change the held-out score.

Replay (5 folds, 420 settled rows, 336 held out): cw_return +0.345,
pnl +101.83 on 26 bets, brier_delta -0.0137. 10 folds: +0.240.
v1 (spread <= 0.06) scored +0.239 / +0.155 with pnl +92.93 on 29 bets.
Baseline (the written risk.json rules: Yes only, edge 0.04-0.10, flat $5)
scores -0.506 held out, pnl -3.06 on 10 bets.
Caveat: two sibling Bank of Israel rows at price 0.12 contribute +73 of
the pnl. Excluding all Bank of Israel rows, v2 still beats v1 at both
fold counts (5 folds +0.033 vs -0.006; 10 folds -0.047 vs -0.076), which
is why the spread change was kept. Rejected this round because their
gain vanished without those rows: requiring fit_score, edge cap 0.065,
category kills (econ-pce, social-post-count), min 24h to resolution.
"""

MIN_EDGE = 0.02
MAX_EDGE = 0.07
MIN_PRICE = 0.10
MAX_PRICE = 0.90
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
        if MIN_EDGE <= edge <= MAX_EDGE and MIN_PRICE <= price <= MAX_PRICE:
            return {"side": side, "stake_usd": STAKE_USD}
    return None
