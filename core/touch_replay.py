#!/usr/bin/env python3
"""Touch replay gate: score a touch estimation rule on every resolved crypto
touch market of the last 90 days.

PROTECTED CORE — the trading agent must not edit files under core/.

Phil's touch-family rules used to be adopted and re-graded on a few settled
rows from a handful of price paths. The market has already run the same
experiment thousands of times: every resolved "Will Bitcoin, Ethereum,
Solana, or XRP reach or dip to $X on <date> / in <month>?" market. This tool
replays strategy/tools/touch.py and its shading rule
strategy/tools/touch_rule.py (both agent-owned) over those markets and scores
the working-tree version against the committed one (--baseline, default
HEAD). CYCLE.md step 3 makes a PASS the bar for editing either file.

What a replayed forecast sees at its time t (and nothing later):
  - forecast times are fixed offsets from the window start (6, 12, 18 h into
    a daily window; days 3, 10, 17, 24 of a monthly one), never the actual
    close;
  - spot, the high or low so far, and the 30-day daily-close vol come from
    Binance 1-hour klines (the markets' resolution source) that CLOSED by t;
    a time whose barrier was already touched is dropped (not live at t);
  - the market price is Polymarket's displayed price read with
    /v2/prices-history `as_of=t` ONLY. A windowed read (start/end) of a
    resolved market returns the settlement payout as its last point, stamped
    inside the window: reading "the last price before t" from it reads the
    answer. price_at() refuses any other parameters, and a returned point is
    used only if its bucket ended by t (timestamp + resolution_seconds <= t);
  - the mid must be at most --max-mid-age seconds old (default 600: an
    estimator fed fresh klines and scored against an older price gets credit
    for the lag) and inside Phil's scan bounds [0.05, 0.95].
The outcome (Gamma outcomePrices) is read only to score. Each side runs in its
own `python3 -I` process that is handed one row at a time, in forecast-time
order, with only touch.py's inputs and the mid; it never holds an outcome or a
later row. touch_rule.py may use only its arguments and `math` (check_rule).

Scoring: dBrier = mean Brier(variant) - mean Brier(mid); negative beats the
market. "candidate - current" is the paired difference on the same rows.
Intervals are 95%, from a 2,000-draw bootstrap over price paths (asset,
window, end): strikes on one path share an outcome driver.

Gate (the line to paste in the retro):
  NO CHANGE  the candidate records the same value as the current version on
             every row (a refactor, or nothing edited);
  PASS       candidate - current has a 95% interval below zero over the whole
             window, a mean at or below zero on the 14-day holdout and in at
             least 3 of the window's 4 chronological folds, and differs on at
             least 20 price paths;
  FAIL       anything else, including any failed price read (rerun: successful
             reads are cached).
The line names the baseline commit and the candidate files' git blob hashes,
and every run is appended to journal/replay/runs.jsonl, so a pasted line can
be matched to its diff and reruns show.

Data: Gamma GET /markets/keyset (closed, tag 102134 "hit price", end-date
range) lists the markets; outcome ids are picked by `version` per
Polymarket's Protocol V2 guidance (positionIds for v2, clobTokenIds for v1).
Klines come from data-api.binance.vision (Binance's public market-data host,
reachable where api.binance.com is geo-blocked). Price reads are paced under
the published 200 per 10 s and cached append-only in
journal/replay/touch-prices.jsonl, so a cold run takes about 14 minutes and a
warm one (market list and klines only) well under a minute. Cache lines are
append-only and the first read of a key wins.

Usage: python3 core/touch_replay.py [--baseline REF] [--days 90]
                                    [--start ISO --end ISO] [--holdout-days 14]
                                    [--max-mid-age 600] [--json]
"""
import argparse
import ast
import concurrent.futures as cf
import datetime as dt
import json
import math
import pathlib
import random
import re
import subprocess
import sys
import tempfile
import threading
import time
import zoneinfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "journal" / "replay" / "touch-prices.jsonl"
RUNS = ROOT / "journal" / "replay" / "runs.jsonl"
TOOL = "strategy/tools/touch.py"
RULE = "strategy/tools/touch_rule.py"

KEYSET = f"{pmapi.GAMMA}/markets/keyset"
HIST = "https://data-api.polymarket.com/v2/prices-history"
KLINES = "https://data-api.binance.vision/api/v3/klines"
HIT_PRICE_TAG = 102134
SYMBOL = {"Bitcoin": "BTCUSDT", "Ethereum": "ETHUSDT", "Solana": "SOLUSDT", "XRP": "XRPUSDT"}
QUESTION = re.compile(r"^Will (Bitcoin|Ethereum|Solana|XRP) (reach|dip to) \$([\d,\.]+) "
                      r"(on|in) ([A-Za-z]+)( \d+)?\?$")
ET = zoneinfo.ZoneInfo("America/New_York")
H = 3600
DAY = 86400
MID_BAND = (0.05, 0.95)
HIST_INTERVAL_S = 0.06       # ~167 reads per 10 s, under the published 200
BOOT_DRAWS = 2000
MIN_CHANGED_PATHS = 20
FOLDS = 4
SIDE_INPUTS = ("spot", "barrier", "days", "ann_vol", "mid")   # what touch.py --mid has live
RULE_IMPORTS = {"math"}
RULE_BANNED_NAMES = {"open", "eval", "exec", "compile", "globals", "locals", "vars", "getattr",
                     "setattr", "delattr", "breakpoint", "input", "help", "memoryview"}

http = pmapi.get_json        # tests swap this for an offline fake
_pace_lock = threading.Lock()
_next_read = [0.0]


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(s):
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


# ---------------------------------------------------------------- price reads

def price_at(params):
    """The displayed price point of params["token_id"] as of params["as_of"],
    or None when the market had no price then.

    as_of ONLY: a windowed read of a resolved market ends with the settlement
    payout, which is the outcome. Anything but {token_id, as_of} is refused.
    """
    if set(params) != {"token_id", "as_of"}:
        raise ValueError(f"prices-history reads must be as_of only, got {sorted(params)}")
    with _pace_lock:
        wait = _next_read[0] - time.monotonic()
        _next_read[0] = max(_next_read[0], time.monotonic()) + HIST_INTERVAL_S
    if wait > 0:
        time.sleep(wait)
    t = params["as_of"]
    pts = [p for p in (http(HIST, params) or {}).get("data") or []
           if p["timestamp"] + p.get("resolution_seconds", 0) <= t]
    return max(pts, key=lambda p: p["timestamp"]) if pts else None


def usable_point(pt, t):
    """The point if its bucket ended by t (no lookahead), else None. Applied
    again on cached points, so a cache written by older code is re-checked."""
    if pt and pt["timestamp"] + pt.get("resolution_seconds", 0) <= t:
        return pt
    return None


def load_cache(path):
    cache = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                cache.setdefault((r["token"], r["as_of"]), r["point"])   # first read wins
    return cache


# --------------------------------------------------------------- market list

def list_range(start, end):
    """Every closed hit-price market whose end date is in [start, end]."""
    out, cursor = [], None
    while True:
        p = {"closed": "true", "tag_id": HIT_PRICE_TAG, "end_date_min": iso(start),
             "end_date_max": iso(end), "limit": 500}
        if cursor:
            p["after_cursor"] = cursor
        d = http(KEYSET, p)
        out += d.get("markets") or []
        cursor = d.get("next_cursor")
        if not cursor or not d.get("markets"):
            return out


def list_markets(start, end):
    """list_range over one-day slices in parallel: the endpoint serves 100 per
    cursor page, so one sequential walk of 90 days is ~140 slow pages."""
    days = [(a, min(a + DAY, end)) for a in range(start, end, DAY)]
    seen = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for page in ex.map(lambda r: list_range(*r), days):
            for m in page:
                seen.setdefault(str(m["id"]), m)
    return list(seen.values())


def yes_token(m):
    """The Yes outcome id, picked by the market's protocol version."""
    version = pmapi.market_version(m)
    raw = m.get("positionIds") if version == "v2" else m.get("clobTokenIds") if version == "v1" else None
    try:
        ids = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        return None
    return str(ids[0]) if isinstance(ids, list) and len(ids) == 2 else None


def parse_market(m):
    """A crypto reach/dip market resolved cleanly to Yes or No, else None."""
    mt = QUESTION.match(m.get("question") or "")
    if not mt:
        return None
    asset, kind, barrier, on_in, month, day = mt.groups()
    try:
        outcomes = json.loads(m.get("outcomes") or "null")
        prices = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
    except (ValueError, TypeError):
        return None
    token = yes_token(m)
    if outcomes != ["Yes", "No"] or sorted(prices) != [0.0, 1.0] or not token:
        return None
    end = parse_ts(m["endDate"])
    local = dt.datetime.fromtimestamp(end - 1, ET)        # the window's last ET day
    if on_in == "on" and day:
        window, first = "daily", local.replace(hour=0, minute=0, second=0, microsecond=0)
    elif on_in == "in" and not day:
        window, first = "monthly", local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        return None
    return {"id": str(m["id"]), "asset": asset, "kind": kind,
            "barrier": float(barrier.replace(",", "")), "window": window,
            "wstart": int(first.timestamp()), "end": end, "yes_token": token,
            "created": parse_ts(m.get("startDate") or m.get("createdAt")),
            "y": 1.0 if prices[0] == 1.0 else 0.0}


# -------------------------------------------------------------------- klines

def klines(symbol, start, end):
    """open_ts -> (high, low, close) of 1-hour bars opening in [start, end)."""
    rows, t = [], start * 1000
    while t < end * 1000:
        d = http(KLINES, {"symbol": symbol, "interval": "1h", "startTime": t, "limit": 1000})
        if not d:
            break
        rows += d
        t = d[-1][0] + H * 1000
        if len(d) < 1000:
            break
    return {r[0] // 1000: (float(r[2]), float(r[3]), float(r[4])) for r in rows}


def closed_bars(k, start, t):
    """Bars opening at or after start that closed by t, or None on a gap."""
    first = start - start % H
    bars = [k.get(h) for h in range(first, t - H + 1, H)]
    return None if any(b is None for b in bars) else bars


def vol30(k, t):
    """Annualized vol of the 30 daily (00:00 UTC) closes before t."""
    day0 = t - t % DAY
    closes = [k.get(day0 - i * DAY - H) for i in range(30, -1, -1)]
    if any(c is None for c in closes):
        return None
    rets = [math.log(closes[i + 1][2] / closes[i][2]) for i in range(30)]
    mu = sum(rets) / 30
    return math.sqrt(sum((r - mu) ** 2 for r in rets) / 29) * math.sqrt(365)


def forecast_times(mk):
    offs = (6 * H, 12 * H, 18 * H) if mk["window"] == "daily" else tuple(d * DAY for d in (3, 10, 17, 24))
    return [mk["wstart"] + o for o in offs if mk["wstart"] + o < mk["end"] - H]


# ---------------------------------------------------------------- build rows

def build_rows(start, end, max_mid_age, cache_path=None):
    """Replayed forecast rows plus a funnel of what was dropped and why."""
    cache_path = cache_path or CACHE
    listed = list_markets(start, end)
    mks = [p for p in (parse_market(m) for m in listed) if p and p["end"] <= end]
    funnel = {"listed": len(listed), "parsed": len(mks)}
    if not mks:
        return [], funnel
    lo, hi = min(m["wstart"] for m in mks) - 40 * DAY, max(m["end"] for m in mks)
    symbols = sorted({SYMBOL[m["asset"]] for m in mks})
    with cf.ThreadPoolExecutor(len(symbols)) as ex:
        K = dict(zip(symbols, ex.map(lambda s: klines(s, lo, hi), symbols)))
    cand = []
    for mk in mks:
        k = K[SYMBOL[mk["asset"]]]
        for t in forecast_times(mk):
            bars = closed_bars(k, mk["wstart"], t)
            if t < mk["created"] or not bars:
                continue
            if mk["kind"] == "reach" and max(b[0] for b in bars) >= mk["barrier"]:
                continue                                   # already touched: not live at t
            if mk["kind"] == "dip to" and min(b[1] for b in bars) <= mk["barrier"]:
                continue
            sig = vol30(k, t)
            if sig:
                cand.append((mk, t, bars[-1][2], sig))
    funnel["points"] = len(cand)

    cache = load_cache(cache_path)
    todo = sorted({(mk["yes_token"], t) for mk, t, _, _ in cand} - set(cache))
    errors = 0
    if todo:
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        def read(key):
            try:
                return key, price_at({"token_id": key[0], "as_of": key[1]}), None
            except RuntimeError as e:   # pmapi.get_json gave up; retried next run
                return key, None, e
        with open(cache_path, "a") as f, cf.ThreadPoolExecutor(6) as ex:
            for key, pt, err in ex.map(read, todo):
                if err:
                    errors += 1
                    continue
                cache[key] = pt
                f.write(json.dumps({"token": key[0], "as_of": key[1], "point": pt}) + "\n")
    funnel["fetched"], funnel["fetch_errors"] = len(todo) - errors, errors

    rows, drop = [], {"unpriced": 0, "stale": 0, "outside_band": 0}
    for mk, t, spot, sig in cand:
        pt = usable_point(cache.get((mk["yes_token"], t)), t)
        if not pt:
            drop["unpriced"] += 1
            continue
        age = t - pt["timestamp"] - pt.get("resolution_seconds", 0)
        if age > max_mid_age:
            drop["stale"] += 1
            continue
        if not MID_BAND[0] <= pt["price"] <= MID_BAND[1]:
            drop["outside_band"] += 1
            continue
        rows.append({"market_id": mk["id"], "asset": mk["asset"], "kind": mk["kind"],
                     "window": mk["window"], "end": mk["end"], "t": t,
                     "spot": spot, "barrier": mk["barrier"], "days": (mk["end"] - t) / DAY,
                     "ann_vol": sig, "mid": pt["price"], "mid_age_s": age, "y": mk["y"]})
    funnel.update(drop)
    funnel["rows"] = len(rows)
    return rows, funnel


# ----------------------------------------------------------------- rule sides

# Runs one side in a separate `python3 -I` process. It reads one row's inputs
# per line and answers before the next is sent, so it never holds a later row.
SIDE_CHILD = r"""
import importlib.util, json, sys
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
p_touch = load("touch", sys.argv[1]).p_touch
estimate = (load("touch_rule", sys.argv[2]).estimate if len(sys.argv) > 2
            else lambda raw, mid, row: raw)
for line in sys.stdin:
    spot, barrier, days, ann_vol, mid = json.loads(line)
    raw = p_touch(spot, barrier, days, ann_vol, 365.0)
    row = {"spot": spot, "barrier": barrier, "days": days, "ann_vol": ann_vol}
    print(json.dumps([raw, estimate(raw, mid, row)]), flush=True)
"""


def check_rule(path):
    """Refuse a rule that could reach past its arguments: it may import only
    math, read attributes only of math, and not name the builtins that open
    files or reach objects' internals. The operator widens these lists."""
    tree = ast.parse(pathlib.Path(path).read_text(), str(path))
    for node in ast.walk(tree):
        bad = None
        if isinstance(node, ast.Import):
            if any(a.name not in RULE_IMPORTS or a.asname for a in node.names):
                bad = "imports " + ", ".join(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level or node.module not in RULE_IMPORTS:
                bad = f"imports from {node.module}"
        elif isinstance(node, ast.Attribute):
            if not (isinstance(node.value, ast.Name) and node.value.id in RULE_IMPORTS) \
                    or node.attr.startswith("_"):
                bad = f"reads attribute .{node.attr}"
        elif isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in RULE_BANNED_NAMES:
                bad = f"uses {node.id}"
            elif node.id in RULE_IMPORTS and not isinstance(node.ctx, ast.Load):
                bad = f"rebinds {node.id}"
        elif isinstance(node, ast.arg) and node.arg in RULE_IMPORTS:
            bad = f"rebinds {node.arg}"
        elif isinstance(node, ast.MatchClass):
            bad = "matches a class pattern"
        if bad:
            raise ValueError(f"{pathlib.Path(path).name} line {node.lineno} {bad}: a rule may use "
                             f"only its arguments and {', '.join(sorted(RULE_IMPORTS))}")


def load_side(tool_path, rule_path):
    """(tool, rule) paths for one side, the rule checked; no rule file means
    raw is recorded."""
    if rule_path:
        check_rule(rule_path)
    return tool_path, rule_path


def git_file(ref, relpath, outdir):
    try:
        text = subprocess.run(["git", "show", f"{ref}:{relpath}"], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout
    except subprocess.CalledProcessError:
        return None
    out = pathlib.Path(outdir) / pathlib.Path(relpath).name
    out.write_text(text)
    return out


def git_out(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True,
                          text=True).stdout.strip()


def evaluate(rows, side):
    """(raw, recorded) per row, from a separate process fed one row at a time
    in forecast-time order: the side never holds an outcome, the market's
    identity, or a row from after the one it is pricing."""
    tool, rule = side
    cmd = [sys.executable, "-I", "-c", SIDE_CHILD, str(tool)] + ([str(rule)] if rule else [])
    out = [None] * len(rows)
    with tempfile.TemporaryFile("w+") as err, \
            subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                             text=True) as proc:
        try:
            for i in sorted(range(len(rows)), key=lambda i: rows[i]["t"]):
                r = rows[i]
                proc.stdin.write(json.dumps([r[k] for k in SIDE_INPUTS]) + "\n")
                proc.stdin.flush()
                raw, p = json.loads(proc.stdout.readline())
                if not (isinstance(p, (int, float)) and 0.0 <= p <= 1.0):
                    raise ValueError(f"rule returned {p!r} for raw {raw:.4f}, mid {r['mid']}")
                out[i] = (raw, float(p))
            proc.stdin.close()
        except (OSError, ValueError, TypeError) as e:
            proc.kill()
            proc.wait()
            err.seek(0)
            name = pathlib.Path(rule or tool).name
            raise ValueError(f"{name}: {err.read().strip() or e}") from None
    return out


# ------------------------------------------------------------------- scoring

def cluster(r):
    return (r["asset"], r["window"], r["end"])


def boot(rows, d, draws=BOOT_DRAWS, seed=0):
    """Mean of d over rows with a 95% interval resampling price paths."""
    sums = {}
    for r, x in zip(rows, d):
        s = sums.setdefault(cluster(r), [0.0, 0])
        s[0] += x
        s[1] += 1
    if not sums:
        return {"mean": None, "lo": None, "hi": None}
    cs = [sums[c] for c in sorted(sums)]     # fixed order: same rows, same interval
    mean = sum(c[0] for c in cs) / sum(c[1] for c in cs)
    rng, k, stats = random.Random(seed), len(cs), []
    for _ in range(draws):
        pick = [cs[i] for i in rng.choices(range(k), k=k)]
        stats.append(sum(c[0] for c in pick) / sum(c[1] for c in pick))
    stats.sort()
    return {"mean": round(mean, 4), "lo": round(stats[int(0.025 * draws)], 4),
            "hi": round(stats[int(0.975 * draws) - 1], 4)}


def score(rows, base, cand, holdout_days=14, fetch_errors=0):
    """Slices, paired candidate - current, and the gate verdict. A failed
    price read fails the gate: a verdict on a partial dataset vouches for
    nothing."""
    for r, (braw, bp), (craw, cp) in zip(rows, base, cand):
        mid_b = (r["mid"] - r["y"]) ** 2
        r["d_raw"] = (craw - r["y"]) ** 2 - mid_b
        r["d_cur"] = (bp - r["y"]) ** 2 - mid_b
        r["d_cand"] = (cp - r["y"]) ** 2 - mid_b
        r["paired"] = (cp - r["y"]) ** 2 - (bp - r["y"]) ** 2
        r["changed"] = abs(cp - bp) > 1e-12
        r["above"] = braw > r["mid"]
    reasons = [f"{fetch_errors} price reads failed; rerun"] if fetch_errors else []
    if not rows:
        return {"slices": [], "verdict": "FAIL", "reasons": reasons + ["no replayed rows"]}
    t0, t1 = min(r["end"] for r in rows), max(r["end"] for r in rows) + 1
    hold = t1 - holdout_days * DAY
    span = (t1 - t0) / FOLDS
    slices = [("all", rows),
              ("current raw above mid", [r for r in rows if r["above"]]),
              ("current raw at or below mid", [r for r in rows if not r["above"]])]
    for i in range(FOLDS):
        a, b = t0 + i * span, t0 + (i + 1) * span
        slices.append((f"fold {i + 1} {iso(a)[:10]}..{iso(b - 1)[:10]}",
                       [r for r in rows if a <= r["end"] < b]))
    slices.append((f"holdout {iso(hold)[:10]}..{iso(t1 - 1)[:10]}",
                   [r for r in rows if r["end"] >= hold]))
    out = []
    for name, rs in slices:
        out.append({"slice": name, "rows": len(rs), "paths": len({cluster(r) for r in rs}),
                    **{m: boot(rs, [r[f"d_{m}" if m != "paired" else m] for r in rs])
                       for m in ("raw", "cur", "cand", "paired")}})

    changed = [r for r in rows if r["changed"]]
    changed_paths = len({cluster(r) for r in changed})
    res = {"slices": out, "changed_rows": len(changed), "changed_paths": changed_paths}
    if not changed:
        res.update(verdict="FAIL" if reasons else "NO CHANGE", reasons=reasons)
        return res
    whole, holdout, folds = out[0]["paired"], out[-1]["paired"], out[3:3 + FOLDS]
    folds_ok = sum(1 for f in folds if (f["paired"]["mean"] or 0.0) <= 0)
    if changed_paths < MIN_CHANGED_PATHS:
        reasons.append(f"differs on {changed_paths} paths, under {MIN_CHANGED_PATHS}")
    if whole["hi"] >= 0:
        reasons.append(f"whole-window interval upper bound {whole['hi']:+.4f} is not below zero")
    if (holdout["mean"] or 0.0) > 0:
        reasons.append(f"holdout mean {holdout['mean']:+.4f} is above zero")
    if folds_ok < FOLDS - 1:
        reasons.append(f"only {folds_ok} of {FOLDS} folds at or below zero")
    res.update(verdict="FAIL" if reasons else "PASS", reasons=reasons, folds_ok=folds_ok)
    return res


def gate_line(res, args, window, ids):
    s = res["slices"][0]["paired"] if res["slices"] else {}
    if res["verdict"] == "NO CHANGE":
        body = "candidate records what the current version records on every row"
    elif s:
        body = (f"candidate - current {s['mean']:+.4f} (95% {s['lo']:+.4f} to {s['hi']:+.4f}), "
                f"{res['changed_rows']} changed rows on {res['changed_paths']} paths, "
                f"holdout {res['slices'][-1]['paired']['mean'] or 0:+.4f}, "
                f"{res.get('folds_ok', 0)} of {FOLDS} folds at or below zero")
    else:
        body = "; ".join(res["reasons"])
    if res["verdict"] == "FAIL" and s:
        body += " - " + "; ".join(res["reasons"])
    return (f"touch-replay {res['verdict']}: {body}; window {window}, "
            f"max mid age {args.max_mid_age}s, baseline {ids['baseline'][:12]}, "
            f"candidate touch.py {ids['touch.py'][:12]} touch_rule.py {ids['touch_rule.py'][:12]}")


def fmt(m):
    if m["mean"] is None:
        return "-"
    return f"{m['mean']:+.4f} ({m['lo']:+.4f} to {m['hi']:+.4f})"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline", default="HEAD",
                    help="git ref holding the current touch.py and touch_rule.py (default HEAD)")
    ap.add_argument("--days", type=float, default=90.0, help="window length ending now")
    ap.add_argument("--start", help="ISO window start (overrides --days)")
    ap.add_argument("--end", help="ISO window end (default now)")
    ap.add_argument("--holdout-days", type=float, default=14.0)
    ap.add_argument("--max-mid-age", type=int, default=600,
                    help="seconds a mid may be older than its forecast time")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    end = parse_ts(args.end) if args.end else int(time.time())
    start = parse_ts(args.start) if args.start else int(end - args.days * DAY)
    rule = ROOT / RULE
    ids = {"baseline": git_out("rev-parse", "--verify", f"{args.baseline}^{{commit}}"),
           "touch.py": git_out("hash-object", TOOL),
           "touch_rule.py": git_out("hash-object", RULE) if rule.exists() else "none"}
    with tempfile.TemporaryDirectory() as tmp:
        base_tool = git_file(ids["baseline"], TOOL, tmp)
        if base_tool is None:
            sys.exit(f"{TOOL} is not in {args.baseline}")
        try:
            base = load_side(base_tool, git_file(ids["baseline"], RULE, tmp))
            cand = load_side(ROOT / TOOL, rule if rule.exists() else None)
        except ValueError as e:
            sys.exit(f"touch-replay FAIL: {e}")
        rows, funnel = build_rows(start, end, args.max_mid_age)
        res = score(rows, evaluate(rows, base), evaluate(rows, cand), args.holdout_days,
                    funnel.get("fetch_errors", 0))
    window = f"{iso(start)[:10]}..{iso(end)[:10]}"
    res["funnel"], res["gate"] = funnel, gate_line(res, args, window, ids)
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNS, "a") as f:
        f.write(json.dumps({"at": iso(int(time.time())), "verdict": res["verdict"],
                            "baseline_ref": args.baseline, **ids, "window": window,
                            "max_mid_age": args.max_mid_age, "funnel": funnel,
                            "gate": res["gate"]}) + "\n")
    if args.json:
        print(json.dumps(res, indent=2))
        return
    print("funnel: " + ", ".join(f"{k} {v}" for k, v in funnel.items()))
    print("dBrier vs the mid (negative beats the market); intervals over price paths\n")
    print(f"{'slice':<36} {'rows':>5} {'paths':>5}  {'raw touch.py':<27} {'current':<27} "
          f"{'candidate':<27} candidate - current")
    for s in res["slices"]:
        print(f"{s['slice']:<36} {s['rows']:>5} {s['paths']:>5}  {fmt(s['raw']):<27} "
              f"{fmt(s['cur']):<27} {fmt(s['cand']):<27} {fmt(s['paired'])}")
    print("\n" + res["gate"])


if __name__ == "__main__":
    main()
