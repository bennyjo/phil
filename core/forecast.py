#!/usr/bin/env python3
"""Forecast ledger: score every researched estimate, not just bets.

PROTECTED CORE — the trading agent must not edit files under core/.
This is the only writer of journal/forecasts.jsonl (resolve.py settles rows).

The experiment's honest metric is brier_delta — is the agent's probability a
better forecast than the market's own price? — and measuring that needs no
stake. Research that ends in a skip (no-edge, market-agrees) still produced
an estimate; recording it here turns ~10-30 researched candidates/day into
scored calibration feedback instead of ~0-1 settled bets/day.

No caps, no edge floor, no fill: the market baseline is the MID at record
time ((bid+ask)/2), not the ask a bet would fill at — a forecast has no
transaction, and the mid is the stricter benchmark. Forecast brier_delta is
therefore NOT comparable to bet brier_delta; score.py reports them in
separate sections. est_prob is the agent's honest belief, formed before
anchoring on the price, exactly as for bets.

One live forecast per market+outcome: recurring re-checks of the same market
must not flood the stats with correlated rows. A materially changed read
(|delta est_prob| >= 0.05, or a changed funnel decision) may replace the live
row via record --supersede: the rows are linked (supersedes / superseded_by),
only the latest row counts in headline scoring, and the superseded row still
settles into score.py's separate revised-away slice - whether revisions
actually improve estimates is measured, not assumed (PLBY 2026-08-10: the
revision was worse than the original).

Estimation rules ship in shadow. A row that a playbook rule moved carries
--rule <id> --raw-prob <estimate before the rule>, with --est-prob the rule's
value. core/score.py grades each rule by the paired Brier difference of those
two numbers on the same outcomes; until its verdict is pass, the recorded
est_prob is the raw estimate and the rule's value sits in rule_prob, so an
unvalidated rule never moves the headline score or a bet. A failed rule is
retired: new rows tagged with it are refused. At most RULE_BUDGET rules may
be in play at once.

Usage:
  record: python3 core/forecast.py record --market-id 123 --outcome Yes \
            --est-prob 0.62 --category econ --skip-reason no-edge \
            [--fit-score 4] [--note "..."] [--strategy-rev abc1234] \
            [--confirm-extreme] [--supersede] \
            [--rule half-gap-below-mid --raw-prob 0.70]
  status: python3 core/forecast.py status
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import uuid
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402
import score  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORECASTS = ROOT / "journal" / "forecasts.jsonl"

# A supersede must change something material: a re-record of an unchanged
# estimate is the correlated-row flooding the one-live-row rule exists to
# prevent, not a revision.
MIN_REVISION_DELTA = 0.05

# An |est_prob - mid| gap this large is either a deliberate extreme
# disagreement (rare: the outside-view-veto class) or an inverted outcome
# side (fe954ed9f325: --outcome No with the Yes-side est_prob, silently
# recording the opposite of the researched belief). The flag costs one
# keystroke exactly when the agent should be pausing anyway; the typo gets
# caught at the only moment it is fixable.
EXTREME_DISAGREEMENT = 0.40

# Rule budget: at most this many estimation rules in play (not retired, and
# tagged on a row in the last RULE_IDLE_DAYS). Every concurrent rule is one
# more chance of a false pass at the scorer's bar, and the playbook grew
# ~60 KB a week while rules were adopted on 1 to 3 events; a small budget
# keeps the set under test small enough to reach verdicts.
RULE_BUDGET = 6
RULE_IDLE_DAYS = 14
RULE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,47}$")


def read_forecasts():
    if not FORECASTS.exists():
        return []
    return [json.loads(line) for line in FORECASTS.read_text().splitlines() if line.strip()]


def cmd_status(rows):
    print(json.dumps({
        "total": len(rows),
        "by_status": dict(Counter(r["status"] for r in rows)),
        "by_skip_reason": dict(Counter(r.get("skip_reason") or "?" for r in rows)),
        "settled_wins": sum(1 for r in rows if r["status"] == "won"),
        "revised_away": sum(1 for r in rows if r.get("superseded_by")),
    }, indent=2))


def _num(value):
    """gamma numeric field -> float rounded to cents, or None if absent/unparseable."""
    if value in (None, ""):
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def rule_state(args, rows):
    """(recorded est_prob, rule fields) for this row; exits on a refusal."""
    if args.rule is None and args.raw_prob is None:
        return args.est_prob, {}
    if args.rule is None or args.raw_prob is None:
        sys.exit("REJECTED: --rule and --raw-prob go together: name the rule "
                 "that moved the estimate and the estimate before it")
    if not RULE_ID.match(args.rule):
        sys.exit(f"REJECTED: rule id {args.rule!r} must be a lowercase slug "
                 "(a-z, 0-9, dashes, 2-48 chars), the id its playbook section names")
    if not 0.0 < args.raw_prob < 1.0:
        sys.exit("REJECTED: raw-prob must be in (0,1)")
    if round(args.raw_prob - args.est_prob, 4) == 0:
        sys.exit("REJECTED: --raw-prob equals --est-prob: the rule did not move "
                 "this estimate, so record it without --rule")
    verdicts = score.rule_verdicts(rows)
    v = verdicts.get(args.rule)
    if v and v["verdict"] == "fail":
        sys.exit(f"REJECTED: rule {args.rule!r} is retired by its paired test "
                 f"(paired {v['mean_delta']:+.4f}, ci99.5 {v['ci']}, "
                 f"{v['events']} events): record your estimate without it")
    cutoff = (dt.datetime.now(dt.timezone.utc)
              - dt.timedelta(days=RULE_IDLE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if v is None or v["last_ts"] < cutoff:
        # a new rule, or an idle one coming back: either takes a free slot
        active = sorted(k for k, w in verdicts.items()
                        if w["verdict"] != "fail" and w["last_ts"] >= cutoff)
        if len(active) >= RULE_BUDGET:
            sys.exit(f"REJECTED: rule budget full ({RULE_BUDGET} in play: "
                     f"{', '.join(active)}). Retire one in the playbook and let "
                     f"it idle {RULE_IDLE_DAYS} days, or record without --rule")
    bound = bool(v) and v["verdict"] == "pass"
    return (args.est_prob if bound else args.raw_prob), {
        "rule": args.rule, "raw_prob": args.raw_prob, "rule_prob": args.est_prob,
        "rule_state": "bound" if bound else "shadow"}


def cmd_record(args, rows):
    if not 0.0 < args.est_prob < 1.0:
        sys.exit("REJECTED: est-prob must be in (0,1)")
    est, rule_fields = rule_state(args, rows)
    live = [r for r in rows
            if r["market_id"] == args.market_id and r["outcome"] == args.outcome
            and r["status"] == "open" and not r.get("superseded_by")]
    if live and not args.supersede:
        sys.exit("REJECTED: already have an open forecast on this market+outcome "
                 "(a materially changed read may supersede it: --supersede)")
    old = None
    if args.supersede:
        if not live:
            sys.exit("REJECTED: --supersede, but no live open forecast on this "
                     "market+outcome to supersede")
        old = live[0]
        # round like ledger.py's edge field so an exactly-boundary revision
        # (0.33 - 0.28 = 0.049999...) does not float-drop below the gate
        if (round(abs(est - old["est_prob"]), 4) < MIN_REVISION_DELTA
                and args.skip_reason == old.get("skip_reason")):
            sys.exit(f"REJECTED: supersede needs a material change — "
                     f"|delta est_prob| >= {MIN_REVISION_DELTA} "
                     f"(old {old['est_prob']}, new {est}) or a changed "
                     f"skip-reason (old {old.get('skip_reason')!r})")

    m = pmapi.gamma_market(args.market_id)
    if m.get("closed"):
        sys.exit("REJECTED: market is closed")
    tokens = pmapi.market_tokens(m)
    if tokens is None:
        sys.exit(f"REJECTED: no usable CLOB token ids (Gamma version "
                 f"{pmapi.market_version(m)!r}; supported: "
                 f"{sorted(pmapi.SUPPORTED_VERSIONS)})")
    if args.outcome not in tokens:
        sys.exit(f"REJECTED: outcome {args.outcome!r} not in {list(tokens)}")
    bid, ask = pmapi.best_prices(tokens[args.outcome])
    if bid is None and ask is None:
        sys.exit("REJECTED: empty book — no market probability to benchmark against")
    mid = (bid + ask) / 2 if bid is not None and ask is not None else bid or ask

    # a rule-tagged row checks both of its numbers, whichever one is recorded
    gap, name, p = max((abs(p - mid), name, p) for name, p in
                       (("est-prob", args.est_prob), ("raw-prob", args.raw_prob))
                       if p is not None)
    if gap > EXTREME_DISAGREEMENT and not args.confirm_extreme:
        sys.exit(f"REJECTED: {name} {p} vs market mid {round(mid, 4)} "
                 f"for outcome {args.outcome!r} differs by {round(gap, 4)} "
                 f"(> {EXTREME_DISAGREEMENT}). If this extreme disagreement is your "
                 "researched belief, re-run with --confirm-extreme; if not, you "
                 "probably inverted the outcome side (est_prob must be for the "
                 f"named outcome {args.outcome!r}, not its complement).")

    row = {
        "id": uuid.uuid4().hex[:12],
        "ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "market_id": args.market_id,
        "question": m.get("question"),
        "slug": m.get("slug"),
        "end_date": m.get("endDate"),
        "outcome": args.outcome,
        "token_id": tokens[args.outcome],
        "est_prob": est,
        **rule_fields,
        "best_bid_at_record": bid,
        "best_ask_at_record": ask,
        "market_prob_at_record": round(mid, 4),
        # Book size at record time, from the same gamma record scan.py reads.
        # Added 2026-09-09 so research edge can be split by liquidity later;
        # gnhf run 5 had to drop that feature for lack of it. None when gamma
        # omits the field - never a guess, never a later re-read.
        "liquidity_at_record": _num(m.get("liquidityNum")),
        "volume_24h_at_record": _num(m.get("volume24hr")),
        "category": args.category,
        "skip_reason": args.skip_reason,
        "fit_score": args.fit_score,
        "note": args.note,
        "strategy_rev": args.strategy_rev,
        "status": "open",
    }
    if old is not None:
        # The old row stays open so resolve.py still settles it (score.py
        # grades it in the revised-away slice, not the headline stats).
        row["supersedes"] = old["id"]
        old["superseded_by"] = row["id"]
        old["superseded_ts"] = row["ts"]
        FORECASTS.write_text("".join(json.dumps(r) + "\n" for r in rows + [row]))
    else:
        with FORECASTS.open("a") as f:
            f.write(json.dumps(row) + "\n")
    out = {"recorded": row["id"], "mid": row["market_prob_at_record"],
           "bid": bid, "ask": ask, "est_prob": est,
           "delta_vs_mid": round(est - mid, 4), "question": row["question"]}
    if rule_fields:
        out["rule"] = {"id": args.rule, "state": rule_fields["rule_state"],
                       "raw_prob": args.raw_prob, "rule_prob": args.est_prob}
    if old is not None:
        out["supersedes"] = old["id"]
        out["delta_est_prob"] = round(est - old["est_prob"], 4)
    print(json.dumps(out, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("record")
    p.add_argument("--market-id", required=True)
    p.add_argument("--outcome", required=True, help="exact outcome name, e.g. Yes")
    p.add_argument("--est-prob", type=float, required=True,
                   help="agent's honest probability, formed before reading the price")
    p.add_argument("--category", required=True,
                   help="agent-assigned category, e.g. earnings/soccer/esports/news")
    p.add_argument("--skip-reason", required=True,
                   help="funnel disposition: bet|no-edge|market-agrees|... "
                        "(use 'bet' when a place follows this forecast)")
    p.add_argument("--supersede", action="store_true",
                   help="replace this market+outcome's live open forecast with a "
                        "materially changed read (links the rows; the old one is "
                        "graded in the revised-away slice, not the headline stats)")
    p.add_argument("--confirm-extreme", action="store_true",
                   help="required when |est_prob - mid| > "
                        f"{EXTREME_DISAGREEMENT}: confirms the extreme "
                        "disagreement is deliberate, not an inverted outcome side")
    p.add_argument("--rule", default=None,
                   help="id of the playbook estimation rule that moved this "
                        "estimate (needs --raw-prob; --est-prob is the rule's value)")
    p.add_argument("--raw-prob", type=float, default=None,
                   help="the estimate before --rule moved it; recorded as "
                        "est_prob while the rule is in shadow")
    p.add_argument("--fit-score", type=int, default=None, help="playbook fit score 0-5")
    p.add_argument("--note", default="", help="one line of context (optional)")
    p.add_argument("--strategy-rev", default="", help="git rev of strategy/ used")
    sub.add_parser("status")
    args = ap.parse_args()

    rows = read_forecasts()
    if args.cmd == "status":
        cmd_status(rows)
    else:
        cmd_record(args, rows)


if __name__ == "__main__":
    main()
