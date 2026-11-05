#!/usr/bin/env python3
"""Variant and edge board: where the estimates beat the market, offline, each cycle.

PROTECTED CORE - the trading agent must not edit files under core/.

Replays settled forecasts from journal/forecasts.jsonl and prints three things:

  Variant table   Each variant re-prices the same recorded rows. It reports
                  walk-forward Brier against the market and against the raw
                  estimate, both time halves, taker ROI after fees, and the
                  paired test from core/score.py.
  Edge map        Per family, hours to resolution, liquidity, spread and 24-hour
                  move: Brier delta, gap slope, q-value, value after shrinking,
                  taker ROI and a verdict. Cells whose verdict changed in the
                  last 24 hours are flagged.
  Allocation      The cells to prefer and to skip when choosing what to research.
                  core/screen.py collect repeats this line.

The board is a report. It places nothing, moves no recorded probability, and
promotes no rule: only core/score.py's verdict on tagged rows binds a rule. It
makes no network calls and commits no state: the "changed" flag recomputes the
map as of 24 hours ago from the same files.

Variants. raw, shrink and stack are built in. The agent may add its own in
strategy/variants.py, which is optional:

  VARIANTS = {"my-slug": (fit, predict)}
  fit(history) -> state      history = earlier settled rows, with `won`.
  predict(row, state) -> p   row = the forecast as recorded, outcome fields
                             stripped (core/replay.py's contract). None means
                             no opinion and keeps the raw estimate.

Two guards keep the replay honest:

  Rule budget     Tagged rules in play plus agent variants share
                  forecast.RULE_BUDGET slots. Variants past it are not replayed.
                  The built-ins take no slot: they never touch a recorded row,
                  and using one means tagging a rule, which takes a slot.
  Reserved rows   Rows recorded in the last RESERVED_DAYS are reserved. They
                  reach the printed board only as a variant's verdict word: the
                  edge map, the allocation and every other number leave them out,
                  so tuning on this board cannot use the rows that judge it. The
                  boundary is a record time that only moves forward, so a row
                  already printed never becomes a reserved row. Older rows are
                  cut into FOLDS contiguous folds; fold 0 only trains. Each fold
                  trains only on earlier rows that had settled before it began.
                  The cost is that the map lags the newest rows by RESERVED_DAYS.
                  This guards against tuning by accident, not on purpose:
                  core/score.py still reports over every row, and an agent variant
                  is code that can read the journal or be swapped each cycle.
                  Variants run in this process with a timeout, and its git history
                  is the record of what was tried.

Intervals are 95% ratio-estimator intervals clustered by event, the method of
score.paired_rule_test. They replace a bootstrap so a verdict never flips on a
random draw. Forecast rows store no fee rate and no listing time, and reading
either needs the network, so ROI uses Polymarket's published rate per family on
every row, which overstates fees on fee-free markets and before fees started,
and there is no market-age table. The 24-hour move comes from the screener log's
mids, so rows the screener never saw a day earlier are in no move cell.

Usage: python3 core/edge_board.py [--json]
"""
import argparse
import contextlib
import datetime as dt
import importlib.util
import json
import math
import pathlib
import re
import signal
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import forecast  # noqa: E402
import replay  # noqa: E402
import score  # noqa: E402
import screen  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
VARIANTS_FILE = ROOT / "strategy" / "variants.py"
# Gitignored and rewritten by every run, so core/screen.py collect can read the
# line without a tracked file that two runners would conflict on.
ALLOCATION_FILE = screen.EDGE_BOARD_ALLOCATION

FOLDS = 5             # older than RESERVED_DAYS; fold 0 only trains
RESERVED_DAYS = 14
MIN_ROWS = FOLDS * 10
VARIANT_TIMEOUT_S = 30
MIN_CI_EVENTS = score.RULE_MIN_CI_EVENTS
MIN_TRADES = 15       # below this a cell's ROI prints as too few
TAKER_EDGE = 0.04     # a replayed taker bet needs this much edge over its fill
MOVE_MIN = 0.10       # a 24-hour move this large is a "moved" market
MOVE_WINDOW_H = (18, 30)  # a screener mid counts as "a day earlier" in this span
REAL_MAX_Q = 0.10
NEGATIVE_MAX_SLOPE = 0.15
CHANGE_WINDOW_H = 24
PROB_FLOOR = 0.001
Z95 = 1.96

# First match wins, on the lowercased category. The category is free text, so a
# few rows are surely misfiled. The rate is docs.polymarket.com/trading/fees for
# the Polymarket category the family mostly lands in.
FAMILIES = [
    ("say-the-word", r"say-the-word|mention", 0.04),
    ("social-count", r"postcount|post-count|social-media|video-views|youtube|views", 0.05),
    ("sports-moneyline",
     r"moneyline|outright|set-winner|preseason|marathon"
     r"|^(soccer|tennis|ufc|mma|cricket|darts|motorsport|golf|esports|esports-lol)$", 0.05),
    ("sports-line", r"spreads|totals|props", 0.05),
    ("econ-print", r"^econ|housing", 0.05),
    ("earnings", r"earnings", 0.04),
    ("commodities/fx/rates", r"commodit|^fx|^rates", 0.04),
    ("crypto", r"crypto", 0.07),
    ("equities", r"equit|stock", 0.04),
    ("politics/geopolitics", r"politic|geopol|war-|chokepoint", 0.04),
    ("news", r"^news", 0.05),
    ("weather/quake", r"weather|earthquake", 0.05),
    ("ai/tech", r"^ai-|tech|product-release|app-store", 0.04),
    ("box-office/awards", r"box-office|awards|music", 0.05),
    ("countable-metric", r"countable|corporate|net-worth", 0.05),
]
FAMILY_RES = [(name, re.compile(pattern), rate) for name, pattern, rate in FAMILIES]
OTHER_FAMILY, OTHER_RATE = "other", 0.05

HOURS_BANDS = ["past-end", "<6h", "6-24h", "1-3d", "3-7d", ">7d"]
LIQUIDITY_BANDS = ["<$500", "$500-2k", "$2k-10k", "$10k-50k", ">$50k"]
SPREAD_BANDS = ["<=1c", "1-2c", "2-5c", "5-10c", ">10c"]
MOVE_BANDS = ["moved>=10c", "moved<10c"]
# The mid is a poor baseline on these books and a taker cannot trade them, so a
# good verdict here is partly mechanical. They print, but are never preferred.
THIN_CELLS = {("liquidity", "<$500"), ("spread", ">10c")}


def won(r):
    return 1.0 if r["status"] == "won" else 0.0


def family_of(r):
    category = (r.get("category") or "").lower()
    for name, pattern, _rate in FAMILY_RES:
        if pattern.search(category):
            return name
    return OTHER_FAMILY


def fee_rate(r):
    name = family_of(r)
    return next((rate for fam, _p, rate in FAMILY_RES if fam == name), OTHER_RATE)


def band(value, edges, labels):
    """labels[i] for the first edges[i] that value is at or under, else the last."""
    for edge, label in zip(edges, labels):
        if value <= edge:
            return label
    return labels[-1]


def hours_band(r):
    try:
        hours = (replay._parse_ts(r["end_date"]) - replay._parse_ts(r["ts"])).total_seconds() / 3600
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    return "past-end" if hours < 0 else band(hours, [6, 24, 72, 168], HOURS_BANDS[1:])


def liquidity_band(r):
    liq = r.get("liquidity_at_record")
    return None if liq is None else band(liq, [500, 2000, 10000, 50000], LIQUIDITY_BANDS)


def spread_band(r):
    spread = round(r["best_ask_at_record"] - r["best_bid_at_record"], 4)
    return band(spread, [0.01, 0.02, 0.05, 0.10], SPREAD_BANDS)


def settled_rows(frows):
    """(live, revised): settled real-book forecasts in record-time order. Revised
    rows were superseded later. Only the paired verdict counts them, as
    score.rule_verdicts does, so post-record news cannot pick its evidence."""
    rows = [r for r in frows if r.get("status") in ("won", "lost") and r.get("settled_ts")
            and not score.placeholder_book(r)]
    rows.sort(key=lambda r: (r["ts"], r["id"]))
    return ([r for r in rows if not r.get("superseded_by")],
            [r for r in rows if r.get("superseded_by")])


def load_moves(rows, screener_rows=None):
    """{forecast id: |24-hour move|}: the record price against the screener mid
    nearest 24 hours earlier, for the rows the screener saw in that window."""
    wanted = {r["market_id"] for r in rows}
    seen = defaultdict(list)
    for s in (screen.log_rows() if screener_rows is None else screener_rows):
        if s.get("market_id") in wanted and s.get("mids") and s.get("ts"):
            seen[s["market_id"]].append((replay._parse_ts(s["ts"]), s["mids"]))
    moves = {}
    for r in rows:
        at = replay._parse_ts(r["ts"])
        best = None
        for ts, mids in seen.get(r["market_id"], ()):
            age = (at - ts).total_seconds() / 3600
            mid = mids.get(r["outcome"])
            if isinstance(mid, (int, float)) and MOVE_WINDOW_H[0] <= age <= MOVE_WINDOW_H[1]:
                if best is None or abs(age - 24) < best[0]:
                    best = (abs(age - 24), mid)
        if best:
            moves[r["id"]] = abs(r["market_prob_at_record"] - best[1])
    return moves


# --- statistics -------------------------------------------------------------

def _t95(df):
    """Two-sided 95% Student-t critical value, Cornish-Fisher expansion."""
    z = Z95
    return z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)


def cluster_ratio(items):
    """Sum(a) / Sum(b) over (event key, a, b) items, with a 95% interval
    clustered by event. Returns {est, events, lo, hi, p}; est is None when
    Sum(b) is 0, and the interval needs MIN_CI_EVENTS events."""
    clusters = defaultdict(lambda: [0.0, 0.0])
    for key, a, b in items:
        clusters[key][0] += a
        clusters[key][1] += b
    total_a = sum(c[0] for c in clusters.values())
    total_b = sum(c[1] for c in clusters.values())
    g = len(clusters)
    out = {"est": None, "events": g, "lo": None, "hi": None, "p": None}
    if total_b <= 0:
        return out
    est = total_a / total_b
    out["est"] = est
    if g >= MIN_CI_EVENTS:
        se = math.sqrt(g / (g - 1) * sum((a - est * b) ** 2
                                         for a, b in clusters.values())) / total_b
        t = _t95(g - 1)
        out.update(lo=est - t * se, hi=est + t * se,
                   p=math.erfc(abs(est) / se / math.sqrt(2)) if se > 0 else 1.0)
    return out


def benjamini_hochberg(ps):
    """q-values for a list of p-values (None stays None)."""
    known = sorted((p, i) for i, p in enumerate(ps) if p is not None)
    qs = [None] * len(ps)
    running = 1.0
    for rank in range(len(known), 0, -1):
        p, i = known[rank - 1]
        running = min(running, p * len(known) / rank)
        qs[i] = running
    return qs


def event_key(r):
    return (family_of(r), (r.get("end_date") or "")[:10])


def brier_delta(rows, probs=None):
    """Mean (p - y)^2 - (mid - y)^2; p is the row's estimate unless probs has it."""
    return cluster_ratio([
        (event_key(r),
         ((probs[r["id"]] if probs else r["est_prob"]) - won(r)) ** 2
         - (r["market_prob_at_record"] - won(r)) ** 2, 1.0) for r in rows])


def gap_slope(rows):
    """Regression of (y - mid) on (est - mid) through the origin: 1 means the gap
    is fully right, 0 that it holds no information."""
    items = []
    for r in rows:
        gap = r["est_prob"] - r["market_prob_at_record"]
        items.append((event_key(r), gap * (won(r) - r["market_prob_at_record"]), gap * gap))
    return cluster_ratio(items)


def taker_pnl(r, p):
    """Net result of $1 at the recorded book if p shows at least TAKER_EDGE over
    the fill, else None. The fill and the protected caps are core/replay.py's."""
    bid, ask = r["best_bid_at_record"], r["best_ask_at_record"]
    if round(p - ask, 4) >= TAKER_EDGE:
        side = "yes"
    elif round(bid - p, 4) >= TAKER_EDGE:
        side = "no"
    else:
        return None
    filled = replay.fill(r, {"side": side, "stake_usd": 1.0})
    if not filled:
        return None
    price, _stake, gross = filled
    shares = 1.0 / (price + fee_rate(r) * price * (1 - price))
    return shares - 1.0 if gross > 0 else -1.0


def taker_roi(rows, probs=None):
    items = []
    for r in rows:
        pnl = taker_pnl(r, probs[r["id"]] if probs else r["est_prob"])
        if pnl is not None:
            items.append((event_key(r), pnl, 1.0))
    out = cluster_ratio(items)
    out["trades"] = len(items)
    if out["lo"] is not None:
        out["lo"] = max(out["lo"], -1.0)  # a normal interval can pass a total loss
    return out


# --- variants ---------------------------------------------------------------

def _clip(p):
    return min(max(p, PROB_FLOOR), 1 - PROB_FLOOR)


def _logit(p):
    p = _clip(p)
    return math.log(p / (1 - p))


def fit_shrink(history):
    """The k minimizing Brier on p = mid + k * (est - mid), clipped to [0, 1]."""
    num = den = 0.0
    for h in history:
        gap = h["est_prob"] - h["market_prob_at_record"]
        num += gap * (float(h["won"]) - h["market_prob_at_record"])
        den += gap * gap
    return min(max(num / den, 0.0), 1.0) if den > 0 else 1.0


def predict_shrink(row, k):
    mid = row["market_prob_at_record"]
    return mid + k * (row["est_prob"] - mid)


def fit_stack(history):
    """Logistic regression of the outcome on logit(mid) and logit(est), no
    intercept, by Newton's method. Starts from the market alone."""
    data = [(_logit(h["market_prob_at_record"]), _logit(h["est_prob"]), float(h["won"]))
            for h in history]
    a, b = 1.0, 0.0
    for _ in range(25):
        ga = gb = haa = hab = hbb = 0.0
        for xm, xe, y in data:
            p = 1 / (1 + math.exp(-(a * xm + b * xe)))
            w = p * (1 - p)
            ga += (y - p) * xm
            gb += (y - p) * xe
            haa += w * xm * xm
            hab += w * xm * xe
            hbb += w * xe * xe
        # A little ridge keeps the step defined when an input is constant.
        haa, hbb = haa + 1e-6, hbb + 1e-6
        det = haa * hbb - hab * hab
        da, db = (hbb * ga - hab * gb) / det, (haa * gb - hab * ga) / det
        a, b = a + da, b + db
        if abs(da) + abs(db) < 1e-6:
            break
    return a, b


def predict_stack(row, weights):
    z = weights[0] * _logit(row["market_prob_at_record"]) + weights[1] * _logit(row["est_prob"])
    return 1 / (1 + math.exp(-z))


BUILTINS = {
    "raw": (None, lambda row, _state: row["est_prob"]),
    "shrink": (fit_shrink, predict_shrink),
    "stack": (fit_stack, predict_stack),
}


@contextlib.contextmanager
def contained():
    """Agent code gets a timeout and cannot write to the board's stdout."""
    def expire(_signum, _frame):
        raise TimeoutError(f"over {VARIANT_TIMEOUT_S}s")
    previous = signal.signal(signal.SIGALRM, expire)
    signal.alarm(VARIANT_TIMEOUT_S)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def load_agent_variants(path=None):
    """(variants, notes). A broken file costs its variants, never the board."""
    path = pathlib.Path(path or VARIANTS_FILE)
    if not path.exists():
        return {}, []
    try:
        spec = importlib.util.spec_from_file_location("edge_board_variants", path)
        mod = importlib.util.module_from_spec(spec)
        with contained():
            spec.loader.exec_module(mod)
        declared = mod.VARIANTS
        variants, notes = {}, []
        for name, pair in declared.items():
            if not isinstance(name, str) or name in BUILTINS or not forecast.RULE_ID.match(name):
                notes.append(f"variant {name!r} skipped: not a free lowercase slug")
                continue
            fit, predict = pair
            variants[name] = (fit, predict)
    except (Exception, SystemExit) as e:  # noqa: BLE001 - the agent owns this file
        return {}, [f"{path.name} unusable, no agent variants this run: "
                    f"{type(e).__name__}: {e}"]
    return variants, notes


def rules_in_play(frows, now):
    """Tagged rules holding a budget slot, by core/forecast.py's definition."""
    cutoff = (now - dt.timedelta(days=forecast.RULE_IDLE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return sorted(k for k, v in score.rule_verdicts(frows).items()
                  if v["verdict"] != "fail" and v["last_ts"] >= cutoff)


def apply_budget(variants, in_play):
    """(variants inside the budget, names refused, slots used). A variant named
    after a tagged rule shares that rule's slot."""
    slots = set(in_play)
    kept, refused = {}, []
    for name, pair in variants.items():
        if name in slots or len(slots) < forecast.RULE_BUDGET:
            slots.add(name)
            kept[name] = pair
        else:
            refused.append(name)
    return kept, refused, sorted(slots)


def reserved_from(now):
    return (now - dt.timedelta(days=RESERVED_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")


def split_folds(rows, now):
    """(fold 0, development rows, reserved rows)."""
    cutoff = reserved_from(now)
    older = [r for r in rows if r["ts"] < cutoff]
    first = math.ceil(len(older) / FOLDS)
    return older[:first], older[first:], [r for r in rows if r["ts"] >= cutoff]


def walk_forward(variant, rows, now, revised=()):
    """{id: p} for every row past fold 0, and for revised rows in the reserved
    window. Each fold fits on earlier rows that had settled before the fold
    began, so no fit sees a later outcome."""
    fit, predict = variant
    fold0, dev, reserved = split_folds(rows, now)
    size = math.ceil(len(dev) / (FOLDS - 1)) if dev else 1
    tests = [dev[i:i + size] for i in range(0, len(dev), size)]
    cutoff = reserved_from(now)
    tests.append(sorted(reserved + [r for r in revised if r["ts"] >= cutoff],
                        key=lambda r: (r["ts"], r["id"])))
    probs, earlier = {}, list(fold0)
    for test in tests:
        if test:
            train = [replay.history_row(r) for r in earlier if r["settled_ts"] <= test[0]["ts"]]
            with contained():
                state = fit(train) if fit else None
                for r in test:
                    p = predict(replay.visible(r), state)
                    p = r["est_prob"] if p is None else float(p)
                    if not 0 <= p <= 1:
                        raise ValueError(f"predicted {p} on row {r['id']}")
                    probs[r["id"]] = p
        earlier += test
    return probs


def variant_row(name, variant, rows, now, revised=()):
    _train, dev, reserved = split_folds(rows, now)
    probs = walk_forward(variant, rows, now, revised)
    half = len(dev) // 2
    cutoff = reserved_from(now)
    judged = reserved + [r for r in revised if r["ts"] >= cutoff]
    moved = [{**r, "rule_prob": probs[r["id"]], "raw_prob": r["est_prob"]} for r in judged
             if round(probs[r["id"]] - r["est_prob"], 6) != 0]
    paired = score.paired_rule_test(moved)
    raw_gap = cluster_ratio([
        (event_key(r), (probs[r["id"]] - won(r)) ** 2 - (r["est_prob"] - won(r)) ** 2, 1.0)
        for r in dev])
    return {
        "variant": name, "rows": len(dev), "vs_market": brier_delta(dev, probs),
        "vs_raw": raw_gap, "h1": brier_delta(dev[:half], probs)["est"],
        "h2": brier_delta(dev[half:], probs)["est"], "roi": taker_roi(dev, probs),
        "reserved": {"rows": len(judged), "n": paired["n"], "events": paired["events"],
                     "verdict": paired["verdict"]},
    }


# --- edge map ---------------------------------------------------------------

def cell_verdict(slope, h1, h2, q, brier, value):
    """Information, not profit.

    Real: slope interval above 0, positive in both halves, q at or below 0.10.
    Plausible: positive in both halves, and the slope or the shrink value clears 0.
    Negative: slope interval below 0, or Brier interval above 0 on a slope under 0.15.
    Noise: everything else, including cells too small for an interval.
    """
    est, lo, hi = slope["est"], slope["lo"], slope["hi"]
    if lo is None:
        return "Noise"
    both = h1 is not None and h2 is not None and h1 > 0 and h2 > 0
    if lo > 0 and both and q is not None and q <= REAL_MAX_Q:
        return "Real"
    if both and (lo > 0 or (value["hi"] is not None and value["hi"] < 0)):
        return "Plausible"
    if hi < 0 or (brier["lo"] is not None and brier["lo"] > 0 and est < NEGATIVE_MAX_SLOPE):
        return "Negative"
    return "Noise"


def edge_map(rows, moves, now):
    """{table: [cell, ...]} over every row except the reserved ones."""
    fold0, dev, _reserved = split_folds(rows, now)
    sample = fold0 + dev
    probs = walk_forward(BUILTINS["shrink"], rows, now)
    h2_from = sample[len(sample) // 2]["ts"] if sample else ""

    def move_band(r):
        move = moves.get(r["id"])
        return None if move is None else MOVE_BANDS[0 if round(move, 4) >= MOVE_MIN else 1]

    tables = [("family", family_of, None), ("hours", hours_band, HOURS_BANDS),
              ("liquidity", liquidity_band, LIQUIDITY_BANDS),
              ("spread", spread_band, SPREAD_BANDS), ("move24h", move_band, MOVE_BANDS)]
    out = {}
    for table, band_of, order in tables:
        groups = defaultdict(list)
        for r in sample:
            label = band_of(r)
            if label is not None:
                groups[label].append(r)
        labels = order if order else sorted(groups)
        labels = [label for label in labels if groups[label]]
        slopes = [gap_slope(groups[label]) for label in labels]
        qs = benjamini_hochberg([s["p"] for s in slopes])
        cells = []
        for label, slope, q in zip(labels, slopes, qs):
            rs = groups[label]
            h1 = gap_slope([r for r in rs if r["ts"] < h2_from])["est"]
            h2 = gap_slope([r for r in rs if r["ts"] >= h2_from])["est"]
            brier = brier_delta(rs)
            scored = [r for r in rs if r["id"] in probs]
            value = brier_delta(scored, probs) if scored else {"est": None, "lo": None, "hi": None}
            cells.append({
                "table": table, "cell": label, "rows": len(rs), "events": slope["events"],
                "brier": brier, "slope": slope, "h1": h1, "h2": h2, "q": q,
                "value": value, "roi": taker_roi(rs),
                "verdict": cell_verdict(slope, h1, h2, q, brier, value),
            })
        out[table] = cells
    return out


def allocation(cells_by_table):
    """Cells to prefer (Real or Plausible, not thin) and to skip (Negative)."""
    prefer, skip = [], []
    for table, cells in cells_by_table.items():
        for c in cells:
            label = f"{table}={c['cell']}"
            if c["verdict"] in ("Real", "Plausible") and (table, c["cell"]) not in THIN_CELLS:
                prefer.append(label)
            elif c["verdict"] == "Negative":
                skip.append(label)
    return {"prefer": prefer, "skip": skip}


def allocation_line(alloc):
    return ("allocation: prefer " + (", ".join(alloc["prefer"]) or "none")
            + "; skip " + (", ".join(alloc["skip"]) or "none"))


def flag_changes(cells_by_table, rows, moves, now):
    """Set `was` on each cell whose verdict differs from the same board run
    CHANGE_WINDOW_H ago, on the rows settled by then."""
    then = now - dt.timedelta(hours=CHANGE_WINDOW_H)
    cutoff = then.strftime("%Y-%m-%dT%H:%M:%SZ")
    earlier = [r for r in rows if r["settled_ts"] <= cutoff]
    fold0, dev, _reserved = split_folds(earlier, then)
    if len(fold0) + len(dev) < MIN_ROWS:
        return
    before = {(c["table"], c["cell"]): c["verdict"]
              for cells in edge_map(earlier, moves, then).values() for c in cells}
    for cells in cells_by_table.values():
        for c in cells:
            was = before.get((c["table"], c["cell"]))
            if was is not None and was != c["verdict"]:
                c["was"] = was


def build(rows, frows, moves, agent_variants, notes, now, revised=()):
    in_play = rules_in_play(frows, now)
    kept, refused, slots = apply_budget(agent_variants, in_play)
    report = {"rows": len(rows), "notes": list(notes), "budget": {
        "limit": forecast.RULE_BUDGET, "rules_in_play": in_play,
        "agent_variants": sorted(kept), "refused": refused, "used": len(slots)}}
    fold0, dev, reserved = split_folds(rows, now)
    if len(fold0) + len(dev) < MIN_ROWS:
        report["notes"].append(f"only {len(fold0) + len(dev)} settled rows before the reserved "
                               f"window; the board needs {MIN_ROWS}")
        report.update(variants=[], edge_map={}, allocation={"prefer": [], "skip": []})
        return report
    report["folds"] = {"train_only": len(fold0), "development": len(dev), "reserved": len(reserved),
                       "reserved_from": reserved_from(now)}
    report["variants"] = []
    for name, variant in {**BUILTINS, **kept}.items():
        try:
            report["variants"].append(variant_row(name, variant, rows, now, revised))
        except (Exception, SystemExit) as e:  # noqa: BLE001 - the agent owns its variants
            report["notes"].append(f"variant {name} failed: {type(e).__name__}: {e}")
    cells = edge_map(rows, moves, now)
    flag_changes(cells, rows, moves, now)
    report["edge_map"] = cells
    report["allocation"] = allocation(cells)
    report["moves"] = {"rows_with_move": sum(1 for r in fold0 + dev if r["id"] in moves)}
    return report


# --- text -------------------------------------------------------------------

def _num(v, fmt="+.4f"):
    return "n/a" if v is None else format(v, fmt)


def _ci(stat, fmt="+.4f"):
    if stat.get("est") is None:
        return "n/a"
    if stat.get("lo") is None:
        return _num(stat["est"], fmt)
    return f"{stat['est']:{fmt}} [{stat['lo']:{fmt}},{stat['hi']:{fmt}}]"


def _roi(stat):
    if stat["trades"] < MIN_TRADES:
        return f"{stat['trades']} too few"
    return f"{stat['trades']} {_ci(stat, '+.0%')}"


def _table(header, lines):
    widths = [max(len(str(x[i])) for x in [header] + lines) for i in range(len(header))]
    for x in [header] + lines:
        print("  " + "  ".join(str(v).ljust(w) for v, w in zip(x, widths)).rstrip())


def render(report):
    b = report["budget"]
    print(f"edge board: {report['rows']} settled rows"
          + (" ({train_only} train-only, {development} development, {reserved} reserved "
             "from {reserved_from})".format(**report["folds"]) if "folds" in report else ""))
    print(f"rule budget: {b['used']}/{b['limit']} in play ({len(b['rules_in_play'])} tagged, "
          f"{len(b['agent_variants'])} agent variants)"
          + (f"; NOT replayed, over budget: {', '.join(b['refused'])}" if b["refused"] else ""))
    for note in report["notes"]:
        print(f"note: {note}")
    if not report["variants"] and not report["edge_map"]:
        return
    print("\nvariants (walk-forward on development rows; the verdict uses the reserved rows only)")
    lines = []
    for v in report["variants"]:
        res = v["reserved"]
        verdict = ("baseline" if v["variant"] == "raw" else
                   f"{res['verdict'].upper()} n={res['n']} events={res['events']}")
        lines.append([v["variant"], v["rows"], _ci(v["vs_market"]),
                      "-" if v["variant"] == "raw" else _ci(v["vs_raw"]),
                      _num(v["h1"]), _num(v["h2"]), _roi(v["roi"]), verdict])
    _table(["variant", "rows", "vs market", "vs raw", "H1", "H2", "taker trades, ROI",
            "reserved verdict"], lines)
    print("\nedge map (every row before the reserved window; intervals 95%, clustered by event; "
          f"{report['moves']['rows_with_move']} rows have a 24-hour move)")
    for table, cells in report["edge_map"].items():
        print(f"\n{table}")
        lines = []
        for c in cells:
            mark = "thin " if (table, c["cell"]) in THIN_CELLS else ""
            changed = f" (was {c['was']})" if c.get("was") else ""
            lines.append([c["cell"], f"{c['rows']} ({c['events']})", _ci(c["brier"]), _ci(c["slope"], "+.2f"),
                          f"{_num(c['h1'], '+.2f')}, {_num(c['h2'], '+.2f')}", _num(c["q"], ".2f"),
                          _ci(c["value"]), _roi(c["roi"]), f"{mark}{c['verdict']}{changed}"])
        _table(["cell", "rows (events)", "Brier delta", "gap slope", "H1, H2", "q",
                "value after shrink", "taker trades, ROI", "verdict"], lines)
    print(f"\n{allocation_line(report['allocation'])}")


def main(argv=None, now=None):
    ap = argparse.ArgumentParser(description="Offline variant and edge board.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    now = now or dt.datetime.now(dt.timezone.utc)
    # A failed run must leave no line behind for collect to repeat as current.
    ALLOCATION_FILE.unlink(missing_ok=True)
    frows = forecast.read_forecasts()
    rows, revised = settled_rows(frows)
    moves = load_moves(rows)
    variants, notes = load_agent_variants()
    report = build(rows, frows, moves, variants, notes, now, revised)
    ALLOCATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALLOCATION_FILE.write_text(allocation_line(report["allocation"]) + "\n")
    if args.json:
        print(json.dumps(report, indent=1, default=str))
    else:
        render(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
