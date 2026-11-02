#!/usr/bin/env python3
"""The cycle's funnel row: opened by core, enriched by the agent.

PROTECTED CORE - the trading agent must not edit files under core/.

Why this exists (operator, 2026-10-25, proposal P10): the prose rule "every
FULL cycle appends a strategy/funnel.jsonl row" lapsed again and again - 0 of
12 FULLs on 10-21/22, rows reconstructed after the fact on 10-24, none at all
for the 04:12Z and 06:15Z FULLs on 10-25. So the row is now mechanical:
`core/screen.py prepare`, which every FULL runs in CYCLE.md step 4 (also when
the screener quota is exhausted), opens the cycle's row, and `collect` fills
in the screener counts. A FULL can no longer end without its row.

One row per FULL or TRIGGERED cycle, and who owns which field:
  * Core owns the measured fields in CORE_KEYS: the cycle stamp, tick type,
    runner, strategy_rev, the trigger keys, the scan pool (`pool_total`,
    `pool_by_query`) and the screener counts (`screened`, `escalated`,
    `screener_batches`).
  * The agent owns everything else - `researched`, `placed`, `settled`,
    `mode`, `mech`, `headline_arena`, the `screener` prose, notes - and adds
    it with `merge`, which rewrites that one row in place. The agent never
    appends a second row for a core-opened cycle; `merge` refuses to touch a
    core field, and refuses when the named row does not exist.
  * A second `prepare` in the same cycle (same runner, within REOPEN_WINDOW)
    reuses the open row instead of appending another, so a re-run screen
    still leaves exactly one row.

Every recorded forecast lands in a funnel row (operator, 2026-10-31, the
TRIGGERED residual of P10): TRIGGERED ticks skip step 4, so `prepare` opens
no row for them, and the agent kept reading the FULL-row rule as FULL-only -
four TRIGGERED forecasts in 24h on 10-30/31 had no row until the next FULL
backfilled them by hand. So `core/forecast.py record` now calls
record_forecast(), which adds a `researched` entry carrying the forecast_id
(`recorded_by: core/forecast.py`) to this cycle's core-opened row:
  * the row this runner's cycle opened within REOPEN_WINDOW - the FULL row
    from `prepare`, or the TRIGGERED row the tick's first forecast opened;
  * unless journal/watch-triggers.jsonl holds a fire newer than that row:
    then this is a TRIGGERED tick, and its first forecast opens a
    `tick_type: TRIGGERED` row (opened_by core/forecast.py) whose `trigger`
    field lists the fired keys. A forecast with neither a row nor a fire
    opens a `tick_type: UNKNOWN` row, so the forecast is covered without
    hiding a FULL that skipped `prepare` (reconcile check 6 still sees it).
`merge` keeps those entries: an agent `researched` list replaces the row's
list, and every core-recorded entry whose forecast_id it does not name is
appended back. `researched` must be a list of objects; merge refuses
anything else (a bare count used to replace the list).

Usage:
  python3 core/funnel.py merge --cycle <ts> --json '{"researched": [...]}'
  python3 core/funnel.py merge --cycle <ts> --file reports/funnel-row.json
  python3 core/funnel.py show --cycle <ts>
`<ts>` is the `funnel_cycle` that `prepare` printed (header and stderr), or
that `core/forecast.py record` printed on a TRIGGERED tick.
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
WATCH_TRIGGERS = ROOT / "journal" / "watch-triggers.jsonl"

OPENED_BY = "core/screen.py"
RECORDED_BY = "core/forecast.py"
CORE_OPENERS = frozenset({OPENED_BY, RECORDED_BY})
CORE_KEYS = frozenset({
    "cycle", "tick_type", "runner", "strategy_rev", "opened_by", "trigger",
    "pool_total", "pool_by_query", "screened", "escalated", "screener_batches",
})
REOPEN_WINDOW = dt.timedelta(minutes=45)
# watch.py records a fire a few minutes before the TRIGGERED tick it starts
# records its first forecast; a fire older than this started no current tick.
TRIGGER_WINDOW = dt.timedelta(minutes=60)


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
    return lambda row: row.get("opened_by") in CORE_OPENERS and row.get("cycle") == cycle


def _fid_text(researched):
    """Every forecast_id in a researched list, joined for substring lookup."""
    return " ".join(str(e.get("forecast_id")) for e in researched
                    if isinstance(e, dict) and e.get("forecast_id"))


def _check_researched(value):
    if not isinstance(value, list) or not all(isinstance(e, dict) for e in value):
        raise ValueError("researched must be a JSON list of objects, one per "
                         "researched candidate")


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


def recent_fire(now):
    """(fire time, comma-joined keys) of the newest watch fire within
    TRIGGER_WINDOW before now, else (None, None)."""
    if not WATCH_TRIGGERS.is_file():
        return None, None
    fires = []
    for line in WATCH_TRIGGERS.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(row.get("utc")) if isinstance(row, dict) else None
        if ts is not None and dt.timedelta(0) <= now - ts <= TRIGGER_WINDOW:
            fires.append((ts, str(row.get("key") or "")))
    if not fires:
        return None, None
    newest = max(ts for ts, _ in fires)
    return newest, ",".join(key for ts, key in fires if ts == newest and key)


def record_forecast(now, runner, entry):
    """Add a recorded forecast to this cycle's core-opened row. Returns the
    row's cycle stamp. `entry` must carry `forecast_id`; see the docstring
    for which row it lands in."""
    lines = _lines()
    fire_ts, keys = recent_fire(now)
    found = _find(lines, lambda row: row.get("opened_by") in CORE_OPENERS
                  and row.get("runner") == runner)
    if found:
        i, row = found
        opened = _parse_ts(row.get("cycle"))
        if (opened is not None and dt.timedelta(0) <= now - opened <= REOPEN_WINDOW
                and (fire_ts is None or opened >= fire_ts)):
            researched = row.get("researched")
            if not isinstance(researched, list):
                researched = []
            if str(entry["forecast_id"]) not in _fid_text(researched):
                researched.append(entry)
            row["researched"] = researched
            lines[i] = json.dumps(row)
            _write(lines)
            return row["cycle"]
    cycle = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    row = {"cycle": cycle, "strategy_rev": strategy_rev(),
           "tick_type": "TRIGGERED" if fire_ts else "UNKNOWN", "runner": runner}
    if keys:
        row["trigger"] = keys
    row.update({"researched": [entry], "opened_by": RECORDED_BY})
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
    if "researched" in fields:
        _check_researched(fields["researched"])
    lines = _lines()
    found = _find(lines, _core_row(cycle))
    if found is None:
        raise KeyError(f"no core-opened funnel row for cycle {cycle}")
    i, row = found
    if not core and "researched" in fields:
        named = _fid_text(fields["researched"])
        old = row.get("researched")
        kept = [e for e in (old if isinstance(old, list) else [])
                if isinstance(e, dict) and e.get("recorded_by") == RECORDED_BY
                and str(e.get("forecast_id")) not in named]
        fields = {**fields, "researched": fields["researched"] + kept}
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
                   help="the funnel_cycle that screen.py prepare or "
                        "forecast.py record printed")
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
