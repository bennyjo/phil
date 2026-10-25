#!/usr/bin/env python3
"""The FULL cycle's funnel row: opened by core, enriched by the agent.

PROTECTED CORE - the trading agent must not edit files under core/.

Why this exists (operator, 2026-10-25, proposal P10): the prose rule "every
FULL cycle appends a strategy/funnel.jsonl row" lapsed again and again - 0 of
12 FULLs on 10-21/22, rows reconstructed after the fact on 10-24, none at all
for the 04:12Z and 06:15Z FULLs on 10-25. So the row is now mechanical:
`core/screen.py prepare`, which every FULL runs in CYCLE.md step 4 (also when
the screener quota is exhausted), opens the cycle's row, and `collect` fills
in the screener counts. A FULL can no longer end without its row.

One row per FULL cycle, and who owns which field:
  * Core owns the measured fields in CORE_KEYS: the cycle stamp, tick type,
    runner, strategy_rev, the scan pool (`pool_total`, `pool_by_query`) and
    the screener counts (`screened`, `escalated`, `screener_batches`).
  * The agent owns everything else - `researched`, `placed`, `settled`,
    `mode`, `mech`, `headline_arena`, the `screener` prose, notes - and adds
    it with `merge`, which rewrites that one row in place. The agent never
    appends a second row for a FULL cycle; `merge` refuses to touch a core
    field, and refuses when the named row does not exist.
  * A second `prepare` in the same cycle (same runner, within REOPEN_WINDOW)
    reuses the open row instead of appending another, so a re-run screen
    still leaves exactly one row.

TRIGGERED ticks skip step 4, so no row is opened for them; they keep
appending their own row as before.

Usage:
  python3 core/funnel.py merge --cycle <ts> --json '{"researched": [...]}'
  python3 core/funnel.py merge --cycle <ts> --file reports/funnel-row.json
  python3 core/funnel.py show --cycle <ts>
`<ts>` is the `funnel_cycle` that `prepare` printed (header and stderr).
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
FUNNEL = ROOT / "strategy" / "funnel.jsonl"

OPENED_BY = "core/screen.py"
CORE_KEYS = frozenset({
    "cycle", "tick_type", "runner", "strategy_rev", "opened_by",
    "pool_total", "pool_by_query", "screened", "escalated", "screener_batches",
})
REOPEN_WINDOW = dt.timedelta(minutes=45)


def _parse_ts(value):
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _lines():
    return FUNNEL.read_text().splitlines() if FUNNEL.is_file() else []


def _write(lines):
    """Replace the file atomically. Untouched lines keep their exact bytes."""
    FUNNEL.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=FUNNEL.parent, prefix=".funnel-")
    with os.fdopen(fd, "w") as fh:
        fh.write("".join(line + "\n" for line in lines))
    os.replace(tmp, FUNNEL)


def _find(lines, match):
    """Index and row of the newest line whose row satisfies match, else None."""
    for i in range(len(lines) - 1, -1, -1):
        try:
            row = json.loads(lines[i])
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and match(row):
            return i, row
    return None


def _core_row(cycle):
    return lambda row: row.get("opened_by") == OPENED_BY and row.get("cycle") == cycle


def strategy_rev():
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10, check=True)
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001 - provenance is nice-to-have, never fatal
        return "unknown"


def open_row(now, runner, fields):
    """Open this FULL cycle's row, or reuse the one this cycle already opened.

    `fields` are core fields (the pool and screener counts). Returns the
    row's cycle stamp, the key every later update names.
    """
    lines = _lines()
    found = _find(lines, lambda row: row.get("opened_by") == OPENED_BY)
    if found:
        i, row = found
        opened = _parse_ts(row.get("cycle"))
        if (row.get("runner") == runner and opened is not None
                and dt.timedelta(0) <= now - opened <= REOPEN_WINDOW):
            row.update(fields)
            lines[i] = json.dumps(row)
            _write(lines)
            return row["cycle"]
    cycle = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {"cycle": cycle, "strategy_rev": strategy_rev(), "tick_type": "FULL",
           "runner": runner, **fields, "researched": [], "opened_by": OPENED_BY}
    lines.append(json.dumps(row))
    _write(lines)
    return cycle


def update_row(cycle, fields, core=False):
    """Merge fields into the row core opened for cycle. Returns the row.

    Raises KeyError when no such row exists, and ValueError when a non-core
    caller names a core field.
    """
    if not core:
        owned = sorted(CORE_KEYS & set(fields))
        if owned:
            raise ValueError(f"core-owned field(s) {owned} - core measures these")
    lines = _lines()
    found = _find(lines, _core_row(cycle))
    if found is None:
        raise KeyError(f"no core-opened funnel row for cycle {cycle}")
    i, row = found
    row.update(fields)
    lines[i] = json.dumps(row)
    _write(lines)
    return row


def cmd_merge(args):
    try:
        text = pathlib.Path(args.file).read_text() if args.file else args.json
        fields = json.loads(text)
    except (OSError, json.JSONDecodeError) as e:
        print(f"funnel: unreadable fields ({type(e).__name__}: {e})", file=sys.stderr)
        return 1
    if not isinstance(fields, dict) or not fields:
        print("funnel: fields must be a non-empty JSON object", file=sys.stderr)
        return 1
    try:
        row = update_row(args.cycle, fields)
    except (KeyError, ValueError) as e:
        print(f"funnel: {e.args[0]}; nothing written", file=sys.stderr)
        return 1
    print(json.dumps(row))
    print(f"funnel: merged {sorted(fields)} into the {args.cycle} row",
          file=sys.stderr)
    return 0


def cmd_show(args):
    found = _find(_lines(), _core_row(args.cycle))
    if found is None:
        print(f"funnel: no core-opened funnel row for cycle {args.cycle}",
              file=sys.stderr)
        return 1
    print(json.dumps(found[1]))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("merge", help="add the agent's fields to this cycle's row")
    m.add_argument("--cycle", required=True,
                   help="the funnel_cycle that screen.py prepare printed")
    src = m.add_mutually_exclusive_group(required=True)
    src.add_argument("--json", help="a JSON object of fields")
    src.add_argument("--file", help="a file holding a JSON object of fields")
    m.set_defaults(func=cmd_merge)

    s = sub.add_parser("show", help="print this cycle's row")
    s.add_argument("--cycle", required=True)
    s.set_defaults(func=cmd_show)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
