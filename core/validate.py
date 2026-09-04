#!/usr/bin/env python3
"""Repo integrity tripwires — run by CI on every push. Offline, no network.

PROTECTED CORE — the trading agent must not edit files under core/.

Checks that an unattended cycle cannot have left the repo broken or unsafe:

  - real_trading_enabled is still false (flipping it is a human decision;
    CI failing loudly is the backstop if it ever changes in a commit)
  - config/protected.json, strategy/risk.json, strategy/schedule.json parse
    and their load-bearing fields are sane
  - the agent's editable sizing policy stays inside the protected caps
  - journal/ledger.jsonl is well-formed and every row respects the caps
  - journal/forecasts.jsonl (stake-free forecasts) rows are well-formed
  - the screener block stays inside its hard batch/pool ceilings, and
    journal/screener-quota/*.json / screener.jsonl are well-formed
  - every Python file under core/ and strategy/ still compiles

Usage: python3 core/validate.py
"""
import datetime as dt
import json
import pathlib
import py_compile
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

LEDGER_REQUIRED = {
    "id", "ts", "market_id", "question", "outcome", "token_id",
    "entry_price", "est_prob", "stake_usd", "status",
}
LEDGER_STATUSES = {"open", "won", "lost", "void"}

FORECAST_REQUIRED = {
    "id", "ts", "market_id", "question", "outcome", "token_id",
    "est_prob", "market_prob_at_record", "category", "skip_reason", "status",
}

SCREENER_REQUIRED = {
    "ts", "market_id", "question", "model", "prompt_rev", "probs", "mids",
    "divergence", "confidence", "reason", "batch_id", "input_tokens",
    "output_tokens", "cost_usd",
}

errors = []


def err(msg):
    errors.append(msg)


def load_json(relpath):
    path = ROOT / relpath
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        err(f"{relpath}: missing")
    except json.JSONDecodeError as e:
        err(f"{relpath}: invalid JSON — {e}")
    return None


def check_iso_z(relpath, field, value):
    try:
        dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        err(f"{relpath}: {field} is not a YYYY-MM-DDTHH:MM:SSZ timestamp: {value!r}")


KNOWN_EDGE_CLASSES = {"info-race", "cross-market", "book-devig", "other"}
REAL_HARD_CEILINGS = {"max_stake_usd": 2.0, "daily_stake_cap_usd": 10.0,
                      "max_open_positions": 20}
# Same story for the screening tier's load. Screening runs on subagents the
# cycle agent fans out, so the day's cost is batches, not dollars: these are the
# ceilings the config tunables may not pass, and core/screen.py clamps to the
# same numbers.
SCREENER_MAX_BATCHES_CEILING = 300
SCREENER_POOL_CEILING = 400
SCREENER_INT_RANGES = {
    "batch_size": (1, 50), "top_n": (1, 50),
    "max_batches_per_day": (1, SCREENER_MAX_BATCHES_CEILING),
    "max_pool_after_strata": (50, SCREENER_POOL_CEILING),
}

protected = load_json("config/protected.json")
if protected:
    if protected.get("real_trading_enabled") not in (True, False):
        err("config/protected.json: real_trading_enabled must be a boolean")
    if protected.get("real_trading_enabled") is True:
        real = protected.get("real")
        if not isinstance(real, dict):
            err("config/protected.json: real_trading_enabled is true but the "
                "'real' caps block is missing — real mode without caps is "
                "never allowed")
        else:
            for field, ceiling in REAL_HARD_CEILINGS.items():
                v = real.get(field)
                if not isinstance(v, (int, float)) or v <= 0:
                    err(f"config/protected.json: real.{field} missing or not "
                        f"a positive number")
                elif v > ceiling:
                    err(f"config/protected.json: real.{field} = {v} exceeds "
                        f"the hard ceiling {ceiling} (raising it requires "
                        f"editing protected core, deliberately)")
            classes = real.get("allowed_edge_classes")
            if not (isinstance(classes, list) and classes
                    and set(classes) <= KNOWN_EDGE_CLASSES):
                err("config/protected.json: real.allowed_edge_classes must be "
                    f"a non-empty subset of {sorted(KNOWN_EDGE_CLASSES)}")
    for field in ("sim_bankroll_usd", "max_stake_usd", "max_open_positions",
                  "min_minutes_to_resolution", "max_entry_price", "min_entry_price"):
        if not isinstance(protected.get(field), (int, float)):
            err(f"config/protected.json: {field} missing or not numeric")

    screener = protected.get("screener")
    if not isinstance(screener, dict):
        err("config/protected.json: the 'screener' block is missing - "
            "core/screen.py needs batch_size/top_n/max_batches_per_day/"
            "max_pool_after_strata")
    else:
        for field, (low, high) in SCREENER_INT_RANGES.items():
            v = screener.get(field)
            if not isinstance(v, int) or isinstance(v, bool):
                err(f"config/protected.json: screener.{field} missing or not an "
                    f"integer")
            elif not low <= v <= high:
                err(f"config/protected.json: screener.{field} = {v} outside "
                    f"[{low}, {high}] (raising the ceiling requires editing "
                    f"protected core, deliberately)")

risk = load_json("strategy/risk.json")
if risk and protected:
    for field in ("default_stake_usd", "min_edge", "max_spread"):
        if not isinstance(risk.get(field), (int, float)):
            err(f"strategy/risk.json: {field} missing or not numeric")
    if isinstance(risk.get("default_stake_usd"), (int, float)) and \
            isinstance(protected.get("max_stake_usd"), (int, float)) and \
            risk["default_stake_usd"] > protected["max_stake_usd"]:
        err(f"strategy/risk.json: default_stake_usd {risk['default_stake_usd']} "
            f"exceeds protected max_stake_usd {protected['max_stake_usd']}")
    if isinstance(risk.get("min_edge"), (int, float)) and not 0 < risk["min_edge"] < 1:
        err(f"strategy/risk.json: min_edge {risk['min_edge']} outside (0, 1)")

schedule = load_json("strategy/schedule.json")
if schedule:
    if not (isinstance(schedule.get("min_full_cycles_per_day"), int)
            and schedule["min_full_cycles_per_day"] >= 1):
        err("strategy/schedule.json: min_full_cycles_per_day missing or < 1 "
            "(the agent may not pace itself to zero)")
    if schedule.get("next_full_cycle_after") is not None:
        check_iso_z("strategy/schedule.json", "next_full_cycle_after",
                    schedule["next_full_cycle_after"])

ledger_path = ROOT / "journal" / "ledger.jsonl"
if ledger_path.exists() and protected:
    for lineno, line in enumerate(ledger_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"ledger.jsonl:{lineno}: invalid JSON — {e}")
            continue
        missing = LEDGER_REQUIRED - row.keys()
        if missing:
            err(f"ledger.jsonl:{lineno}: missing fields {sorted(missing)}")
            continue
        if row["status"] not in LEDGER_STATUSES:
            err(f"ledger.jsonl:{lineno}: unknown status {row['status']!r}")
        if row["status"] != "open" and not ("pnl_usd" in row and "settled_ts" in row):
            err(f"ledger.jsonl:{lineno}: settled row lacks pnl_usd/settled_ts")
        if row["stake_usd"] > protected["max_stake_usd"]:
            err(f"ledger.jsonl:{lineno}: stake {row['stake_usd']} exceeds "
                f"max_stake_usd {protected['max_stake_usd']}")
        if not (protected["min_entry_price"] <= row["entry_price"]
                <= protected["max_entry_price"]):
            err(f"ledger.jsonl:{lineno}: entry_price {row['entry_price']} outside "
                f"[{protected['min_entry_price']}, {protected['max_entry_price']}]")
        if not 0 < row["est_prob"] <= 1:
            err(f"ledger.jsonl:{lineno}: est_prob {row['est_prob']} outside (0, 1]")

forecasts_path = ROOT / "journal" / "forecasts.jsonl"
if forecasts_path.exists():
    for lineno, line in enumerate(forecasts_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"forecasts.jsonl:{lineno}: invalid JSON — {e}")
            continue
        missing = FORECAST_REQUIRED - row.keys()
        if missing:
            err(f"forecasts.jsonl:{lineno}: missing fields {sorted(missing)}")
            continue
        if row["status"] not in LEDGER_STATUSES:
            err(f"forecasts.jsonl:{lineno}: unknown status {row['status']!r}")
        if row["status"] != "open" and "settled_ts" not in row:
            err(f"forecasts.jsonl:{lineno}: settled row lacks settled_ts")
        if not 0 < row["est_prob"] < 1:
            err(f"forecasts.jsonl:{lineno}: est_prob {row['est_prob']} outside (0, 1)")
        if not 0 <= row["market_prob_at_record"] <= 1:
            err(f"forecasts.jsonl:{lineno}: market_prob_at_record "
                f"{row['market_prob_at_record']} outside [0, 1]")

screener_quota_dir = ROOT / "journal" / "screener-quota"
if (ROOT / "journal" / "screener-quota.json").exists():
    err("journal/screener-quota.json: the shared counter was retired on "
        "2026-09-04; the quota lives under journal/screener-quota/<runner>.json")
if screener_quota_dir.is_dir():
    for qpath in sorted(screener_quota_dir.glob("*.json")):
        rel = qpath.relative_to(ROOT).as_posix()
        quota = load_json(rel)
        if quota is None:
            continue
        day = quota.get("day")
        if not (isinstance(day, str) and day.strip()):
            err(f"{rel}: day missing or not a string")
        batches = quota.get("batches")
        if not isinstance(batches, int) or isinstance(batches, bool):
            err(f"{rel}: batches missing or not an integer")
        elif batches < 0:
            err(f"{rel}: batches {batches} is negative")

screener_path = ROOT / "journal" / "screener.jsonl"
if screener_path.exists():
    for lineno, line in enumerate(screener_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"screener.jsonl:{lineno}: invalid JSON - {e}")
            continue
        missing = SCREENER_REQUIRED - row.keys()
        if missing:
            err(f"screener.jsonl:{lineno}: missing fields {sorted(missing)}")
            continue
        # A malformed model answer is a logged screen_error row, not a failure -
        # but a row that claims a divergence must carry a usable one.
        div = row["divergence"]
        if div is not None and not (isinstance(div, (int, float))
                                    and not isinstance(div, bool)
                                    and 0 <= div <= 1):
            err(f"screener.jsonl:{lineno}: divergence {div!r} is not a number "
                f"in [0, 1]")
        if div is None and not row.get("screen_error"):
            err(f"screener.jsonl:{lineno}: no divergence and no screen_error - "
                f"every unscored row must say why")
        cost = row["cost_usd"]
        if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
            err(f"screener.jsonl:{lineno}: cost_usd {cost!r} is not a "
                f"non-negative number")

real_ledger_path = ROOT / "journal" / "real-ledger.jsonl"
if real_ledger_path.exists() and protected and isinstance(protected.get("real"), dict):
    real_cap = protected["real"].get("max_stake_usd")
    for lineno, line in enumerate(real_ledger_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"real-ledger.jsonl:{lineno}: invalid JSON — {e}")
            continue
        if isinstance(real_cap, (int, float)) and \
                isinstance(row.get("usd"), (int, float)) and row["usd"] > real_cap:
            err(f"real-ledger.jsonl:{lineno}: real stake {row['usd']} exceeds "
                f"real.max_stake_usd {real_cap}")

for pyfile in sorted((ROOT / "core").glob("*.py")) + \
        sorted((ROOT / "strategy").rglob("*.py")):
    try:
        py_compile.compile(str(pyfile), doraise=True)
    except py_compile.PyCompileError as e:
        err(f"{pyfile.relative_to(ROOT)}: does not compile — {e.msg}")

if errors:
    print(f"FAIL — {len(errors)} integrity error(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("OK — config, risk policy, schedule, ledger and Python sources all sane")
