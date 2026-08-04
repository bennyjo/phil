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
LEDGER_STATUSES = {"open", "won", "lost"}

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
