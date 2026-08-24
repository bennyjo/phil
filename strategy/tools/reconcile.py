"""Funnel <-> forecast coverage checker — AGENT-EDITABLE (strategy/tools/).

Added by DEEP-2026-08-21 after the coverage weld (playbook, Funnel
instrumentation) was violated twice on its first day in force: the
2026-08-20 14:27Z and 18:17Z FULL cycles recorded 4 forecasts
(e5d0e44532c3, 9a1c771fd651, 371aa91ed8bc, 84e1b257aa68) with no funnel
line — the fourth and fifth funnel-coverage defects in five windows.
DEEP-2026-08-20 declared the next recurrence a compliance pattern; this is
the escalation: a mechanical check instead of more prose.

Checks, over a trailing window (default 24h):
  1. Every forecasts.jsonl row's id appears in some funnel.jsonl
     `researched[].forecast_id` (substring match — funnel entries may
     annotate the id, e.g. "df7062f3e89d (existing, unchanged)").
  2. Every funnel `researched` entry with an estimate-bearing skip reason
     (no-edge, market-agrees, outside-view-veto, category-bar,
     wide-spread-veto, bet) carries a forecast_id.
  3. Every funnel line carries `pool_by_query` (non-empty object) and
     `pool_total` (number) — the mandatory-fields rule (playbook, Funnel
     instrumentation / DEEP-2026-08-18). Added DEEP-2026-08-24 after the
     prose rule was violated twice in two days post-flagging (2026-08-23
     00:11Z and 2026-08-24 03:11Z lines both omitted pool_total, the
     second one the AfD bet cycle); same escalation shape as this tool's
     own origin: a mechanical check instead of more prose.

Exit 0 with "OK" when both hold; exit 1 listing each orphan otherwise.
Run before the commit of any FULL cycle that recorded a forecast — the
check is the weld; a FULL-cycle commit while this fails is a discipline
violation, not an oversight (playbook, Coverage weld).

Usage:
  python3 strategy/tools/reconcile.py [--hours 24]
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ESTIMATE_BEARING = {
    "no-edge", "market-agrees", "outside-view-veto", "category-bar",
    "wide-spread-veto", "bet", "bet-placed",
}


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def load_jsonl(path):
    rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"WARN unparseable line in {path.name}", file=sys.stderr)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24.0)
    args = ap.parse_args()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)

    forecasts = load_jsonl(ROOT / "journal" / "forecasts.jsonl")
    funnel = load_jsonl(ROOT / "strategy" / "funnel.jsonl")

    funnel_ids = []          # all forecast_id strings seen in funnel entries
    missing_fid = []         # estimate-bearing funnel entries without one
    schema_gaps = []         # funnel lines missing mandatory pool fields
    for entry in funnel:
        ts = parse_ts(entry.get("cycle", ""))
        recent = ts is not None and ts >= cutoff
        if recent:
            if not entry.get("pool_by_query"):
                schema_gaps.append(
                    f"funnel {entry.get('cycle')} missing pool_by_query"
                )
            if not isinstance(entry.get("pool_total"), (int, float)):
                schema_gaps.append(
                    f"funnel {entry.get('cycle')} missing pool_total"
                )
        for cand in entry.get("researched", []):
            fid = cand.get("forecast_id")
            if fid:
                funnel_ids.append(str(fid))
            elif cand.get("acknowledged"):
                # Documented, unrepairable gap (e.g. a backfilled entry whose
                # estimate was never recorded and cannot be reconstructed).
                # Acknowledging is itself an audit event — deep retros grep
                # for these; it must never be used on a repairable gap.
                continue
            elif recent and cand.get("skip_reason") in ESTIMATE_BEARING:
                missing_fid.append(
                    f"funnel {entry.get('cycle')} market {cand.get('market_id')} "
                    f"skip={cand.get('skip_reason')} has no forecast_id"
                )
    joined = " ".join(funnel_ids)

    orphans = []
    for row in forecasts:
        ts = parse_ts(row.get("ts", ""))
        if ts is None or ts < cutoff:
            continue
        rid = str(row.get("id", ""))
        if rid and rid not in joined:
            orphans.append(
                f"forecast {rid} ({row.get('ts')} {row.get('category')}) "
                f"has no funnel line"
            )

    problems = orphans + missing_fid + schema_gaps
    if problems:
        for p in problems:
            print(p)
        print(f"FAIL: {len(problems)} coverage gap(s) in last {args.hours:g}h")
        return 1
    print(f"OK: funnel<->forecast coverage reconciles over last {args.hours:g}h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
