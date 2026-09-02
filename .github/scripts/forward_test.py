#!/usr/bin/env python3
"""Forward test of the gnhf policy: fire once there is enough new data.

The gnhf run of 2026-09-02 chose strategy/policy.py v3 by reading all 420
settled forecasts, so its replay score is in-sample. The forward test
scores the same policy on every forecast whose outcome was still unknown
when that run ended (settled_ts > CUTOFF), including the five bets the
policy pre-registered on the then-open rows.

This script is the trigger. It prints NOT_YET until MIN_SETTLED rows have
settled after the cutoff, then writes a GitHub issue body with the forward
numbers, the pre-registered bets, and the pass criteria judged
mechanically. The workflow opens the issue once.

Usage: python3 .github/scripts/forward_test.py [--out PATH] [--force]
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
FORECASTS = ROOT / "journal" / "forecasts.jsonl"

CUTOFF = "2026-09-02T00:14:36Z"  # gnhf run 1 ended (orchestrator:end)
MIN_SETTLED = 100                # rows settled after the cutoff before we judge
MAX_SETTLED = 300                # judge regardless of bet count once this many settled
PREREGISTERED = {                # v3's decisions on the rows open at the cutoff
    "a3ab895344cf": "no",
    "d48834ed8f41": "no",
    "e9f9221a3afb": "yes",
    "650a1bcef8e7": "no",
    "0b03a937a48d": "yes",
}
# Pass criteria, fixed before any forward row settled:
MIN_BETS = 15            # fewer bets than this is "not enough evidence", not a fail
MAX_SINGLE_BET_SHARE = 0.5  # no one bet may carry more than half of a positive pnl


def settled_after_cutoff():
    n = 0
    for line in FORECASTS.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") in ("won", "lost") and (r.get("settled_ts") or "") > CUTOFF:
            n += 1
    return n


def forward_report():
    out = subprocess.run(
        [sys.executable, str(ROOT / "core" / "replay.py"), "--after", CUTOFF, "--json"],
        check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def judge(h, bets):
    if h["n_bets"] < MIN_BETS:
        return "NOT ENOUGH BETS", f"{h['n_bets']} bets, criteria need at least {MIN_BETS}"
    if h["cw_return"] <= 0:
        return "FAIL", f"forward cw_return {h['cw_return']:+.4f} is not above zero"
    if h["pnl"] > 0:
        top = max(b["pnl"] for b in bets)
        if top / h["pnl"] > MAX_SINGLE_BET_SHARE:
            return "FAIL", (f"one bet carries {top / h['pnl']:.0%} of the pnl, "
                            f"limit {MAX_SINGLE_BET_SHARE:.0%}")
    return "PASS", f"cw_return {h['cw_return']:+.4f} on {h['n_bets']} bets, no single bet dominates"


def body(n_settled, report):
    h, bets = report["held_out"], report["bets"]
    verdict, why = judge(h, bets)
    by_id = {b["id"]: b for b in bets}
    rows = []
    for line in FORECASTS.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r["id"] in PREREGISTERED:
                rows.append(r)
    prereg = []
    for r in rows:
        b = by_id.get(r["id"])
        pnl = f"{b['pnl']:+.2f}" if b else "no fill"
        prereg.append(f"| {r['id']} | {PREREGISTERED[r['id']]} | {r['status']} | {pnl} | {r['question'][:60]} |")
    bd = "-" if h["brier_delta"] is None else f"{h['brier_delta']:+.4f}"
    return f"""## Forward test of strategy/policy.py v3 is ready

**Verdict: {verdict}** ({why})

{n_settled} forecasts have settled since the gnhf run ended at {CUTOFF}
(threshold {MIN_SETTLED}). The policy was scored on all of them with
`python3 core/replay.py --after {CUTOFF}`. Nobody tuned on these outcomes.

| Metric | Forward | In-sample (5 folds, for reference) |
|---|---|---|
| cw_return | {h['cw_return']:+.4f} | +0.743 |
| pnl | {h['pnl']:+.2f} | +121.68 |
| bets | {h['n_bets']} / {h['n_rows']} rows | 19 / 336 |
| win rate | {h['win_rate']} | 0.895 |
| brier_delta vs market | {bd} | -0.0248 |

### Pre-registered bets (open at the cutoff)

| id | side | status | pnl | question |
|---|---|---|---|---|
{chr(10).join(prereg)}

### Criteria (fixed 2026-09-02, before any forward row settled)

- At least {MIN_BETS} forward bets, else the test is inconclusive and waits.
- Forward cw_return above zero.
- No single bet carries more than {MAX_SINGLE_BET_SHARE:.0%} of a positive pnl.

### Next actions

1. Write the verdict and the table above into `journal/operator-notes.md`.
2. If PASS: ask the deep retro to consider adopting the 0.20-0.45 price dead zone into `risk.json`. The both-sides small-edge rule adds bets and needs a second forward window first.
3. If FAIL: the branch history is the writeup. Change nothing in `strategy/`.
4. Either way, the next gnhf run uses a sealed cutoff so the agent evaluates only on rows settled before it.

Full bet list: `python3 core/replay.py --after {CUTOFF} --bets`
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="write the issue body here when ready")
    ap.add_argument("--force", action="store_true", help="write the report even below the threshold")
    a = ap.parse_args()
    n = settled_after_cutoff()
    report = forward_report() if (n >= MIN_SETTLED or a.force) else None
    n_bets = report["held_out"]["n_bets"] if report else 0
    # Fire once there is enough data AND enough bets to judge; if the policy
    # bets so rarely that MIN_BETS never arrives, fire anyway at MAX_SETTLED,
    # because "too few bets to test" is itself the finding.
    ready = a.force or (n >= MIN_SETTLED and (n_bets >= MIN_BETS or n >= MAX_SETTLED))
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"ready={'true' if ready else 'false'}\nsettled={n}\nbets={n_bets}\n")
    if not ready:
        stage = "settled" if n < MIN_SETTLED else f"bets {n_bets}/{MIN_BETS}, settled"
        print(f"NOT_YET {stage} after cutoff: {n}/{MIN_SETTLED} (judge regardless at {MAX_SETTLED})")
        return
    text = body(n, report)
    if a.out:
        pathlib.Path(a.out).write_text(text)
        print(f"READY settled after cutoff: {n}/{MIN_SETTLED}; body written to {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
