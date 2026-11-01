"""Funnel-row shape check - AGENT-EDITABLE (strategy/tools/).

Added DEEP-2026-11-01. Five consecutive FULL rows (2026-10-31 16:15Z,
18:13Z, 20:13Z, 2026-11-01 00:14Z, 02:14Z) were merged with `researched`
as an int count instead of a list, and had to be backfilled by hand at
04:15Z Nov 1 (commit bf5bf705). An int breaks the deep retro's
forecast-coverage reconciliation (CYCLE.md step 6). core/funnel.py merge
does not type-check (operator proposal, journal/proposals.md); until it
does, run this after your last `funnel.py merge` and before committing:

  python3 strategy/tools/funnel_check.py [--last N]

It exits 1 and lists every problem in the last N rows (default 3):
`researched` / `placed` not lists, researched entries without a
forecast_id, or forecast_ids / ledger ids that do not exist. Read-only.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def ids(path):
    out = set()
    p = ROOT / path
    if p.exists():
        for line in p.open():
            line = line.strip()
            if line:
                try:
                    out.add(json.loads(line).get("id"))
                except json.JSONDecodeError:
                    pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=3)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (ROOT / "strategy/funnel.jsonl").open() if x.strip()]
    fids, lids = ids("journal/forecasts.jsonl"), ids("journal/ledger.jsonl")
    problems = []
    for r in rows[-a.last:]:
        tag = f"{r.get('cycle') or r.get('ts') or '?'} {r.get('tick_type')}"
        res = r.get("researched")
        if res is not None and not isinstance(res, list):
            problems.append(f"{tag}: researched is {type(res).__name__}, must be a list of dicts")
        for e in res if isinstance(res, list) else []:
            if not isinstance(e, dict) or not e.get("forecast_id"):
                problems.append(f"{tag}: researched entry without forecast_id: {str(e)[:80]}")
            elif e["forecast_id"] not in fids:
                problems.append(f"{tag}: forecast_id {e['forecast_id']} not in forecasts.jsonl")
        pl = r.get("placed")
        if isinstance(pl, list):
            for lid in pl:
                if lid not in lids:
                    problems.append(f"{tag}: placed id {lid} not in ledger.jsonl")
        elif pl not in (None, 0):
            problems.append(f"{tag}: placed is {type(pl).__name__} {pl!r}, use a list of ledger ids")
    for p in problems:
        print(p)
    print(f"funnel_check: {len(problems)} problem(s) in last {a.last} row(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
