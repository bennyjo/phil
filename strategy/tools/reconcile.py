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
  3. Every FULL-cycle funnel line (tick_type absent or "FULL") carries
     `pool_by_query` (non-empty object) and `pool_total` (number) — the
     mandatory-fields rule (playbook, Funnel instrumentation /
     DEEP-2026-08-18). Added DEEP-2026-08-24 after the prose rule was
     violated twice in two days post-flagging (2026-08-23 00:11Z and
     2026-08-24 03:11Z lines both omitted pool_total, the second one the
     AfD bet cycle); same escalation shape as this tool's own origin: a
     mechanical check instead of more prose. TRIGGERED-cycle lines are
     exempt (fixed 2026-08-25T02:53Z, false-positive on the 3rd straight
     TRIGGERED-cycle line): CYCLE.md's TRIGGERED tick skips step 4's
     broad scan by design, so those lines structurally have no pool to
     report — flagging them as gaps trained nothing, it just repeated a
     known-expected omission every trigger.
  5. Veto-settlement table duty (DEEP-2026-08-27): every settled
     (won/lost) forecasts.jsonl row with skip_reason outside-view-veto or
     wide-spread-veto and settled_ts >= 2026-08-23 (when DEEP-2026-08-23
     made the same-commit counterfactual-table extension a rule) must have
     its id appear somewhere in strategy/playbook.md — either as a table
     row or as a documented exclusion. The prose rule was violated three
     times on 2026-08-26 alone (Crowley 7dac557c4c19 at 07:28Z, the three
     PCE MoM rows at 15:21Z, the BoK pair at 04:13Z next day — the last
     logged as "veto-correct" when the vetoed read had in fact WON its
     counterfactual), so it gets the same escalation as checks 1-4: a
     mechanical check instead of more prose. A mere id mention doesn't
     prove the arithmetic was done — deep retros still audit quality —
     but it makes silent omission impossible.
  6. FULL-cycle funnel-line presence (DEEP-2026-08-27): every cycles.log
     line in the window whose first marker is "(FULL cycle" must have a
     funnel.jsonl line whose cycle ts falls in the 45 minutes before the
     log ts. The 2026-08-26 09:24Z FULL ran a complete scan+screen+research
     pass, recorded zero forecasts, wrote NO funnel line — and that absence
     blinded checks 3 and 4 (its 99-minute pacing-pointer breach was
     invisible because check 4 reads funnel lines, not cycle logs). The
     operator mandate says every FULL appends a line, forecasts or not.
  4. Pacing-pointer freshness (DEEP-2026-08-26): the newest FULL-cycle
     funnel line in the window must not postdate schedule.json's
     `next_full_cycle_after` by more than 65 minutes. DEEP-2026-08-25
     flagged a FULL cycle that ran past a stale pointer without
     advancing it (prose flag, first instance, weld pre-committed on
     repeat); it then repeated six times in 12 hours (the 2026-08-25
     22:16Z through 2026-08-26 04:17Z FULLs all ran against the
     17:21Z-set 20:15Z pointer). Running FULL every tick stays legal —
     but only by consciously advancing the pointer (to ~now or the next
     boundary) each FULL, which is the contract: every FULL commit
     touches the field or inherits a pointer still in the future. The
     65-minute grace absorbs the single tick that legitimately fires
     just past the pointer.

Exit 0 with "OK" when all hold; exit 1 listing each problem otherwise.
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
        is_full = entry.get("tick_type", "FULL") == "FULL"
        if recent and is_full:
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

    # Check 4: pacing-pointer freshness (see module docstring).
    pacing_gaps = []
    full_ts = [
        parse_ts(e.get("cycle", ""))
        for e in funnel
        if e.get("tick_type", "FULL") == "FULL" and parse_ts(e.get("cycle", ""))
    ]
    newest_full = max(full_ts) if full_ts else None
    if newest_full is not None and newest_full >= cutoff:
        try:
            sched = json.loads(
                (ROOT / "strategy" / "schedule.json").read_text()
            )
        except (OSError, json.JSONDecodeError):
            sched = {}
        pointer = parse_ts(sched.get("next_full_cycle_after", ""))
        if pointer is None or pointer < newest_full - timedelta(minutes=65):
            pacing_gaps.append(
                f"schedule.json next_full_cycle_after "
                f"({sched.get('next_full_cycle_after')}) is stale: newest "
                f"FULL funnel line {newest_full.isoformat()} ran >65min past "
                f"it — each FULL must advance the pointer or say why not"
            )

    # Check 5: veto-settlement table duty (see module docstring).
    VETO_TABLE_SINCE = "2026-08-23"
    try:
        playbook = (ROOT / "strategy" / "playbook.md").read_text()
    except OSError:
        playbook = ""
    latest = {}
    for row in forecasts:
        rid = str(row.get("id", ""))
        if rid:
            latest[rid] = row  # last write wins (supersede/settle updates)
    table_gaps = []
    for rid, row in latest.items():
        if (
            row.get("status") in ("won", "lost")
            and row.get("skip_reason") in ("outside-view-veto", "wide-spread-veto")
            and str(row.get("settled_ts", "")) >= VETO_TABLE_SINCE
            and rid not in playbook
        ):
            table_gaps.append(
                f"settled {row.get('skip_reason')} row {rid} "
                f"({row.get('settled_ts')} {row.get('category')}) absent from "
                f"playbook.md counterfactual ledger (add the row or a "
                f"documented exclusion)"
            )

    # Check 6: FULL-cycle funnel-line presence (see module docstring).
    funnel_line_gaps = []
    funnel_ts = sorted(t for t in full_ts if t is not None)
    cycles_path = ROOT / "journal" / "cycles.log"
    if cycles_path.exists():
        for line in cycles_path.read_text().splitlines():
            if not line[:4].isdigit() or " cycle done" not in line:
                continue
            i = line.find("(FULL cycle")
            j = line.find("(LIGHT tick")
            k = line.find("(TRIGGERED")
            markers = [(x, n) for n, x in (("FULL", i), ("LIGHT", j), ("TRIG", k)) if x != -1]
            if not markers or min(markers)[1] != "FULL":
                continue
            done_ts = parse_ts(line.split()[0])
            if done_ts is None or done_ts < cutoff:
                continue
            # Funnel lines are usually stamped during the cycle (up to
            # ~45min before "cycle done") but occasionally seconds after
            # the log line — hence the 10min grace on the other side.
            if not any(
                timedelta(minutes=-10) <= done_ts - ft <= timedelta(minutes=45)
                for ft in funnel_ts
            ):
                funnel_line_gaps.append(
                    f"FULL cycle logged {done_ts.isoformat()} has no funnel "
                    f"line in the preceding 45min — every FULL appends one "
                    f"(operator mandate, playbook Funnel instrumentation)"
                )

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

    problems = (
        orphans + missing_fid + schema_gaps + pacing_gaps + table_gaps
        + funnel_line_gaps
    )
    if problems:
        for p in problems:
            print(p)
        print(f"FAIL: {len(problems)} coverage gap(s) in last {args.hours:g}h")
        return 1
    print(f"OK: funnel<->forecast coverage reconciles over last {args.hours:g}h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
