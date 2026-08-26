#!/usr/bin/env python3
"""Event-trigger watcher: does a catalyst justify a TRIGGERED cycle right now?

PROTECTED CORE - the trading agent must not edit files under core/.

Usage: python3 core/watch.py check

This runs from an offset cloud routine (~15 min cadence). It prints exactly
one JSON verdict on stdout and ALWAYS exits 0; any failure prints
{"trigger": false, "error": ...} - a broken check must never manufacture a
cycle. Quiet ticks are the normal case: the routine reads `trigger` and stops.

What it watches, all read from the agent-owned strategy/watchlist.json with
the caps below enforced HERE, so a watchlist edit cannot widen them:
  1. price_moves - CLOB /prices-history per entry: fire when the mid moved by
     at least move_threshold over the last window_min minutes. Stateless, so
     there is no committed price baseline to go stale between runners.
  2. new_market - one gamma query, newest first: fire on markets created in
     the last 25 minutes that clear the liquidity floor (and the optional
     keyword filter).
  3. calendar - {label, fire_at, window_min} entries the agent maintains from
     its own research, giving its release-time knowledge a mechanical outlet.

Caps (code, not config): at most 15 price_moves entries, move_threshold floor
0.05, at most 10 calendar entries, at most 3 new-market fires per run, at most
6 fires per UTC day. Entries past their "expires" are skipped and reported
under "expired" for the agent to prune.

Double-fire guards, all evaluated BEFORE anything fires:
  * per-key 6h cooldown (journal/watch-state.json);
  * origin/main's recent cycle commits: any cycle: or cycle(triggered):
    commit under 20 minutes old suppresses every key, and a cycle(triggered):
    commit under 45 minutes old whose subject names a key suppresses that key.
    A git failure suppresses nothing and says so in the verdict's notes;
  * the daily fire budget, counted from journal/watch-triggers.jsonl.
When suppression is already total the REST calls are skipped entirely, so a
quiet tick behind a fresh cycle costs nothing.

State files reach origin only via the triggered cycle's own commit
(at-least-once semantics); CYCLE.md's duplicate-position check is what makes a
re-fire harmless.

CLOB and gamma calls use the urllib-then-curl fallback from
strategy/tools/quote.py (urllib TLS-fingerprint block, verified 2026-08-05).
Requests are paced ~150ms apart and capped at 17 per run - far under the
60 req/min limit. Polling itself is free.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
WATCHLIST = ROOT / "strategy" / "watchlist.json"
STATE_FILE = ROOT / "journal" / "watch-state.json"
TRIGGERS_FILE = ROOT / "journal" / "watch-triggers.jsonl"
PROTECTED_FILE = ROOT / "config" / "protected.json"

MAX_PRICE_MOVES = 15          # watchlist entries honoured, in file order
MIN_MOVE_THRESHOLD = 0.05     # floor on move_threshold, in probability points
MAX_CALENDAR = 10
MAX_NEW_MARKET_FIRES = 3      # per run - a batch market drop is not 40 cycles
DAILY_FIRE_BUDGET = 6         # fires per UTC day, counted from the jsonl
COOLDOWN_S = 6 * 3600         # per-key
STATE_TTL_S = 48 * 3600       # fired-map garbage collection
RECENT_CYCLE_S = 20 * 60      # any cycle commit this fresh suppresses all
SAME_KEY_CYCLE_S = 45 * 60    # a triggered commit this fresh suppresses its key
NEW_MARKET_AGE_S = 25 * 60
MAX_CALLS = 17                # 15 price moves + 1 gamma + 1 spare
PACE_S = 0.15

# Used when the watchlist is missing or unreadable, so a bad agent edit cannot
# turn the watcher off - only narrow it.
DEFAULT_NEW_MARKET = {"enabled": True, "min_liquidity": 5000, "keywords": []}

# Same TLS-fingerprint story as strategy/tools/quote.py: a real UA gets urllib
# past the 403, but the 2026-08-05 12:31Z cycle saw urllib blocked while curl
# with an identical UA/URL returned 200. Fall back rather than let a transport
# quirk read as "no catalyst".
UA = "Mozilla/5.0 (compatible; paper-trader-watch)"

_calls = 0


def warn(msg):
    print(f"watch: {msg}", file=sys.stderr)


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def iso(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value):
    """Parse an ISO-8601 timestamp from the watchlist or state. UTC, or None."""
    if not isinstance(value, str) or not value.strip():
        return None
    s = value.strip().replace("Z", "+00:00")
    try:
        ts = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=dt.timezone.utc)


def fetch_json(url, params=None):
    """GET url as JSON: urllib first, curl on any failure. Paced and capped."""
    global _calls
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    if _calls >= MAX_CALLS:
        raise RuntimeError(f"request cap reached ({MAX_CALLS}) before GET {url}")
    if _calls:
        time.sleep(PACE_S)
    _calls += 1
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except Exception as e_urllib:  # noqa: BLE001 - transport quirk, not an answer
        try:
            out = subprocess.run(
                ["curl", "-s", "--max-time", "15", "-H", f"User-Agent: {UA}", url],
                capture_output=True, text=True, timeout=20, check=True,
            )
            return json.loads(out.stdout)
        except Exception as e_curl:  # noqa: BLE001 - surface both halves
            raise RuntimeError(f"GET {url} failed (urllib: {e_urllib}; "
                               f"curl: {e_curl})") from e_curl


# --- watchlist ------------------------------------------------------------

def load_watchlist():
    """Read the agent's watchlist defensively.

    An unusable file degrades to the new-market check on built-in defaults - it
    never crashes the run and never silently watches nothing at all.
    """
    fallback = {"new_market": dict(DEFAULT_NEW_MARKET)}
    if not WATCHLIST.is_file():
        warn("strategy/watchlist.json missing; running the new-market check only")
        return fallback
    try:
        wl = json.loads(WATCHLIST.read_text())
        if not isinstance(wl, dict):
            raise ValueError("top level is not an object")
        return wl
    except Exception as e:  # noqa: BLE001 - a bad edit degrades, never crashes
        warn(f"strategy/watchlist.json unusable ({type(e).__name__}: {e}); "
             f"running the new-market check only")
        return fallback


def expired(entry, now):
    """True if the entry's "expires" is in the past (absent/unparseable: no)."""
    ts = parse_iso(entry.get("expires"))
    return ts is not None and ts <= now


def price_move_entries(wl, now, out_expired):
    entries = wl.get("price_moves")
    if not isinstance(entries, list):
        if entries is not None:
            warn("watchlist price_moves is not a list; ignoring it")
        return []
    kept = []
    for raw in entries:
        if not isinstance(raw, dict):
            continue
        market_id = str(raw.get("market_id") or "").strip()
        token_id = str(raw.get("token_id") or "").strip()
        label = str(raw.get("label") or "").strip() or f"market {market_id}"
        if not market_id or not token_id:
            warn(f"watchlist price_moves entry {label!r} has no market_id/token_id; skipped")
            continue
        if expired(raw, now):
            out_expired.append(f"pricemove:{market_id}")
            continue
        try:
            threshold = float(raw.get("move_threshold", MIN_MOVE_THRESHOLD))
        except (TypeError, ValueError):
            threshold = MIN_MOVE_THRESHOLD
        try:
            window = int(float(raw.get("window_min", 60)))
        except (TypeError, ValueError):
            window = 60
        kept.append({
            "market_id": market_id,
            "token_id": token_id,
            "label": label,
            # caps live here, not in the agent's file
            "move_threshold": max(threshold, MIN_MOVE_THRESHOLD),
            # /prices-history?interval=1h only reaches back an hour
            "window_min": min(max(window, 5), 60),
        })
        if len(kept) >= MAX_PRICE_MOVES:
            if len(entries) > MAX_PRICE_MOVES:
                warn(f"watchlist has {len(entries)} price_moves entries; "
                     f"honouring the first {MAX_PRICE_MOVES}")
            break
    return kept


def calendar_entries(wl, now, out_expired):
    entries = wl.get("calendar")
    if not isinstance(entries, list):
        if entries is not None:
            warn("watchlist calendar is not a list; ignoring it")
        return []
    kept = []
    for raw in entries:
        if not isinstance(raw, dict):
            continue
        label = str(raw.get("label") or "").strip()
        fire_at = parse_iso(raw.get("fire_at"))
        if not label or fire_at is None:
            warn(f"watchlist calendar entry {label or '(unlabelled)'!r} has no "
                 f"label/fire_at; skipped")
            continue
        if expired(raw, now):
            out_expired.append(f"cal:{label}")
            continue
        try:
            window = int(float(raw.get("window_min", 30)))
        except (TypeError, ValueError):
            window = 30
        if now >= fire_at + dt.timedelta(minutes=max(window, 1)):
            out_expired.append(f"cal:{label}")
            continue
        kept.append({"label": label, "fire_at": fire_at,
                     "window_min": min(max(window, 1), 180)})
        if len(kept) >= MAX_CALENDAR:
            if len(entries) > MAX_CALENDAR:
                warn(f"watchlist has {len(entries)} calendar entries; "
                     f"honouring the first {MAX_CALENDAR}")
            break
    return kept


# --- checks ---------------------------------------------------------------

def check_price_moves(entries, notes):
    """Fire on entries whose mid moved >= threshold inside their window."""
    fires = []
    for e in entries:
        try:
            body = fetch_json(f"{pmapi.CLOB}/prices-history",
                              {"market": e["token_id"], "interval": "1h"})
        except Exception as exc:  # noqa: BLE001 - one dead token is not a verdict
            notes.append(f"price history for {e['label']}: {exc}")
            continue
        history = body.get("history") if isinstance(body, dict) else body
        points = []
        for p in history or []:
            try:
                points.append((int(p["t"]), float(p["p"])))
            except (KeyError, TypeError, ValueError):
                continue
        if len(points) < 2:
            notes.append(f"price history for {e['label']}: fewer than 2 usable points")
            continue
        points.sort()
        last_t, last_p = points[-1]
        cutoff = last_t - e["window_min"] * 60
        older = [p for p in points if p[0] <= cutoff]
        base_t, base_p = older[-1] if older else points[0]
        move = last_p - base_p
        if abs(move) < e["move_threshold"]:
            continue
        span_min = round((last_t - base_t) / 60)
        fires.append({
            "kind": "price_move",
            "key": f"pricemove:{e['market_id']}",
            "market_id": e["market_id"],
            "detail": (f"{base_p:.3f} -> {last_p:.3f} ({move:+.3f}) over {span_min} min, "
                       f"threshold {e['move_threshold']:.3f}"),
            "context": {
                # no gamma call here: the watchlist label is the agent's own
                # description of the market, and the call budget belongs to the
                # price history.
                "question": e["label"],
                "label": e["label"],
                "price_from": round(base_p, 4),
                "price_to": round(last_p, 4),
                "market_id": e["market_id"],
                "kind": "price_move",
            },
        })
    return fires


def banned_patterns():
    """Protected banned-question patterns, so a fire can never be unbettable."""
    try:
        protected = json.loads(PROTECTED_FILE.read_text())
        return [re.compile(p, re.I) for p in protected["banned_question_patterns"]]
    except Exception as e:  # noqa: BLE001 - filter is a courtesy, not a gate
        warn(f"config/protected.json unusable for the banned-question filter "
             f"({type(e).__name__}: {e}); new-market fires are unfiltered")
        return []


def check_new_markets(cfg, now, notes):
    """Fire on freshly created markets clearing the liquidity/keyword floor."""
    if not isinstance(cfg, dict) or not cfg.get("enabled", False):
        return []
    try:
        min_liquidity = float(cfg.get("min_liquidity", 5000))
    except (TypeError, ValueError):
        min_liquidity = 5000.0
    keywords = [str(k).strip().lower() for k in cfg.get("keywords") or []
                if str(k).strip()]
    try:
        batch = fetch_json(f"{pmapi.GAMMA}/markets",
                           {"closed": "false", "order": "createdAt",
                            "ascending": "false", "limit": 100})
    except Exception as exc:  # noqa: BLE001 - quiet beats wrong
        notes.append(f"new-market query: {exc}")
        return []
    banned = banned_patterns()
    fires = []
    for m in batch or []:
        created = parse_iso(m.get("createdAt"))
        if created is None or (now - created).total_seconds() > NEW_MARKET_AGE_S:
            continue
        try:
            liquidity = float(m.get("liquidityNum") or 0)
        except (TypeError, ValueError):
            liquidity = 0.0
        if liquidity < min_liquidity:
            continue
        question = str(m.get("question") or "")
        if keywords and not any(k in question.lower() for k in keywords):
            continue
        if any(p.search(question) for p in banned):
            continue
        # Listings whose game is already underway are repricing races the
        # cycle agent cannot research in time (4 declined fires, 2026-08-26);
        # gamma listing time is not research-opportunity time for these.
        game_start = parse_iso(m.get("gameStartTime"))
        if game_start is not None and game_start <= now:
            continue
        market_id = str(m.get("id") or "").strip()
        if not market_id:
            continue
        fires.append({
            "kind": "new_market",
            "key": f"newmarket:{market_id}",
            "market_id": market_id,
            "detail": (f"created {m.get('createdAt')}, liquidity {liquidity:.0f} "
                       f"(floor {min_liquidity:.0f})"),
            "context": {
                "question": question,
                "label": m.get("slug") or question,
                "price_from": None,
                "price_to": None,
                "market_id": market_id,
                "kind": "new_market",
            },
        })
        if len(fires) >= MAX_NEW_MARKET_FIRES:
            notes.append(f"new-market fires capped at {MAX_NEW_MARKET_FIRES} this run")
            break
    return fires


def check_calendar(entries, now):
    """Fire on entries whose window (fire_at .. fire_at+window_min) is open."""
    fires = []
    for e in entries:
        end = e["fire_at"] + dt.timedelta(minutes=e["window_min"])
        if not (e["fire_at"] <= now < end):
            continue
        fires.append({
            "kind": "calendar",
            "key": f"cal:{e['label']}",
            "market_id": None,
            "detail": f"window {iso(e['fire_at'])} .. {iso(end)}",
            "context": {
                "question": e["label"],
                "label": e["label"],
                "price_from": None,
                "price_to": None,
                "market_id": None,
                "kind": "calendar",
            },
        })
    return fires


# --- guards ---------------------------------------------------------------

def load_state():
    if not STATE_FILE.is_file():
        return {"last_fire_utc": None, "fired": {}}
    try:
        state = json.loads(STATE_FILE.read_text())
        fired = state.get("fired")
        return {"last_fire_utc": state.get("last_fire_utc"),
                "fired": fired if isinstance(fired, dict) else {}}
    except Exception as e:  # noqa: BLE001 - a corrupt state file is not a licence to storm
        warn(f"journal/watch-state.json unusable ({type(e).__name__}: {e}); "
             f"treating every key as freshly fired this run")
        return None


def cooling_down(state, key, now):
    ts = parse_iso(state["fired"].get(key))
    return ts is not None and (now - ts).total_seconds() < COOLDOWN_S


def git_suppression(now, notes):
    """(suppress_all, keys_named_by_recent_triggered_commits) from origin/main."""
    try:
        out = subprocess.run(
            ["git", "log", "origin/main", "-5", "--format=%s %ct"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=15, check=True,
        )
    except Exception as e:  # noqa: BLE001 - no history read: suppress nothing, say so
        notes.append(f"cycle-commit guard skipped (git failed: {type(e).__name__}: {e})")
        return False, []
    suppress_all, named = False, []
    for line in out.stdout.splitlines():
        subject, _, ct = line.rpartition(" ")
        try:
            age = now.timestamp() - int(ct)
        except ValueError:
            continue
        subject = subject.strip()
        triggered = subject.startswith("cycle(triggered):")
        if not (triggered or subject.startswith("cycle:")):
            continue
        if age < RECENT_CYCLE_S:
            suppress_all = True
        if triggered and age < SAME_KEY_CYCLE_S:
            named.append(subject)
    return suppress_all, named


def fires_today(now):
    """Fires already recorded for this UTC day, from the append-only trigger log."""
    if not TRIGGERS_FILE.is_file():
        return 0
    today = iso(now)[:10]
    count = 0
    for line in TRIGGERS_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if str(row.get("utc") or "")[:10] == today:
            count += 1
    return count


def record_fires(fires, state, now):
    """Append the trigger rows, then rewrite state with a 48h-GC'd fired map."""
    TRIGGERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    stamp = iso(now)
    with TRIGGERS_FILE.open("a") as fh:
        for f in fires:
            fh.write(json.dumps({"utc": stamp, "kind": f["kind"], "key": f["key"],
                                 "market_id": f["market_id"],
                                 "detail": f["detail"]}) + "\n")
    fired = {}
    for key, ts in state["fired"].items():
        parsed = parse_iso(ts)
        if parsed is not None and (now - parsed).total_seconds() < STATE_TTL_S:
            fired[key] = ts
    for f in fires:
        fired[f["key"]] = stamp
    STATE_FILE.write_text(json.dumps(
        {"last_fire_utc": stamp, "fired": dict(sorted(fired.items()))}, indent=2) + "\n")


# --- verdict --------------------------------------------------------------

def check():
    now = utcnow()
    notes, expired_keys = [], []
    wl = load_watchlist()
    moves = price_move_entries(wl, now, expired_keys)
    calendar = calendar_entries(wl, now, expired_keys)

    state = load_state()
    if state is None:  # unreadable state: never fire blind
        return {"trigger": False, "keys": [], "context": [], "expired": expired_keys,
                "notes": ["journal/watch-state.json unreadable; no fire this run"]}

    suppress_all, named_subjects = git_suppression(now, notes)
    budget_left = DAILY_FIRE_BUDGET - fires_today(now)
    if budget_left <= 0:
        suppress_all = True
        notes.append(f"daily fire budget spent ({DAILY_FIRE_BUDGET}/UTC day)")
    if suppress_all:
        # nothing can fire, so spend no requests finding out what would have
        notes.append("suppressed before checks: a cycle commit is under "
                     f"{RECENT_CYCLE_S // 60} min old or the daily budget is spent")
        return {"trigger": False, "keys": [], "context": [], "expired": expired_keys,
                "notes": notes}

    fires = (check_price_moves(moves, notes)
             + check_new_markets(wl.get("new_market"), now, notes)
             + check_calendar(calendar, now))

    kept = []
    for f in fires:
        if cooling_down(state, f["key"], now):
            notes.append(f"{f['key']} in cooldown ({COOLDOWN_S // 3600}h)")
            continue
        if any(f["key"] in s for s in named_subjects):
            notes.append(f"{f['key']} covered by a cycle(triggered): commit under "
                         f"{SAME_KEY_CYCLE_S // 60} min old")
            continue
        if len(kept) >= budget_left:
            notes.append(f"{f['key']} deferred: only {budget_left} fire(s) left "
                         f"in today's budget")
            continue
        kept.append(f)

    if not kept:
        return {"trigger": False, "keys": [], "context": [], "expired": expired_keys,
                "notes": notes}

    record_fires(kept, state, now)
    return {"trigger": True, "keys": [f["key"] for f in kept],
            "context": [f["context"] for f in kept], "expired": expired_keys,
            "notes": notes, "utc": iso(now)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="print one JSON trigger verdict; always exits 0")
    ap.parse_args()

    try:
        verdict = check()
    except Exception as e:  # noqa: BLE001 - a failed check is a quiet tick, never a fire
        verdict = {"trigger": False, "error": f"{type(e).__name__}: {e}"}
    print(json.dumps(verdict))
    print(f"watch: {_calls} request(s) this run", file=sys.stderr)


if __name__ == "__main__":
    main()
