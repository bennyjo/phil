#!/usr/bin/env python3
"""Dormant research-value prior: where has research beaten the price before?

PROTECTED CORE - the trading agent must not edit files under core/.

DORMANT. Nothing calls this. CYCLE.md, core/screen.py prepare and
core/screen.py collect are untouched, the Haiku tier still screens and the
escalation list is still the divergence top 15. This exists so the operator
can switch the escalation list over in one step once the evidence is read,
and switch it back by not running it.

Why it exists (gnhf run 5, 2026-09-08). The research tier is the scarce
resource: about 950 markets researched over 258 cycles for 654 forecasts,
582 settled, 16 bets. Escalation ranks by divergence, and the 2026-09-04
evaluator (core/screen_replay.py, journal/screener-rank-decision.md) showed
that divergence carries no information the price does not already carry - it
is in effect "the markets priced nearest 50/50". A ranking that reads nothing
spends the scarce slot at random within the pool it is handed. So this asks a
different question, off a different journal: not "where does the screen
disagree with the price", which is unreadable, but "where has THIS agent's
own research beaten the price before", which journal/forecasts.jsonl records
directly, one row per researched (market, outcome) with est_prob and the
market price it was handed.

The statistic is brier_delta, the same one core/score.py and
core/counterfactual.py use:

    brier_delta = (est_prob - won)^2 - (market_prob_at_record - won)^2

NEGATIVE means research beat the price it was handed. It is averaged over
cells of features a ranking can read BEFORE spending the slot - family, price
band, hours to resolution, market age, and whether the cycle was TRIGGERED -
because a feature only readable after research cannot rank anything.

Three things this deliberately does NOT do:

  * It never writes a journal. Not journal/forecasts.jsonl, not
    journal/screener.jsonl, not the quota. `fit` reads and prints; that is
    all it does.
  * It never places, sizes or vetoes anything - same prohibition as
    core/screen.py and core/screen_rank.py. It re-orders a reading list.
  * It does not re-derive a standard error. The event-clustered estimator is
    screen_replay.mean_se, the fill model and the walk-forward folds are
    counterfactual.py's, and the settled-row loader is replay.py's rule.

Where the numbers can and cannot be read. The label exists only on markets
that WERE researched, and those were picked by the agent's own escalation and
watch tiers, so every cell here is conditioned on that selection. This
measures where research beat the price among markets research reached; it
cannot measure a market research never saw. `fit` prints n and an
event-clustered interval on every cell so a thin cell is visible as thin.

THE JUDGMENT IS THE AGENT'S, in strategy/screener-value.json: the family
mapper (ordered title and slug regexes, first match wins) and the band edges
on the numeric features. The FITTING is here and stays here - a prior is
estimated from the journal, never hand-written into a tuning file. If that
file is missing or malformed this uses the built-in defaults below and says
so loudly on stderr, the same rule core/screen.py has for the strata and the
filters: a broken tuning file degrades the ranking, it never stops it.

What `fit` measures, as of the 2026-09-08 run. The prior does NOT order
held-out rows better than chance. On five walk-forward folds, with ties
averaged over rather than broken and the null drawn by permuting each fold's
own scores 4,000 times, the top quartile's lift is +0.0196 for a family-only
prior at p 0.996 - worse than random - and -0.0083 for the age-only prior at
p 0.087, which moves in one fold of four because the shrinkage collapses to
zero in the three earlier training windows. Price band and hours to
resolution shrink to tau2 = 0 and produce no ordering at all. So this stays
dormant on the evidence, not merely on the operator's schedule; see
journal/screener-value-decision.md for the bar that would change it.

Usage:
  python3 core/screen_value.py fit               # the prior table
  python3 core/screen_value.py fit --json
  python3 core/screen_value.py fit --folds 5
  python3 core/screen_value.py rank              # re-rank the latest collect run
  python3 core/screen_value.py rank --run 20260908T213047
  python3 core/screen_value.py rank --work-root ~/Code/phil/reports/screener-work
Input:  journal/forecasts.jsonl, journal/screener.jsonl (the screened pools and
        the market-age proxy), journal/screener-outcomes.jsonl (end_date only),
        journal/screener-events.jsonl (clustering), strategy/funnel.jsonl
        (TRIGGERED or FULL), strategy/screener-value.json (the tuning file),
        and --work-root's batch briefs for the end_date the caches miss.
Output: fit prints one table per feature on stdout; rank prints its header on
        stderr and its top 15 on stdout as JSON lines, the shape collect
        prints, plus value_prior and value_features on each row.
Writes: nothing. Neither subcommand opens a file for writing.
"""

import argparse
import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import counterfactual  # noqa: E402  (protected sibling: fill model, folds)
import replay  # noqa: E402  (protected sibling: loaders, ts parsing)
import screen_replay  # noqa: E402  (protected sibling: clustering, SEs)

ROOT = replay.ROOT
VALUE_FILE = ROOT / "strategy" / "screener-value.json"
SCREENER = ROOT / "journal" / "screener.jsonl"
FUNNEL = ROOT / "strategy" / "funnel.jsonl"

# The family set is CODE, not tuning. The prior table's shape has to survive
# an edit to strategy/screener-value.json, and a rule naming a family outside
# this set is dropped loudly rather than silently growing a tenth column.
FAMILIES = ("sports moneyline", "sports line", "econ print", "politics",
            "ai and tech", "entertainment", "weather", "crypto", "other")
FALLBACK_FAMILY = "other"

# Bounds the tuning file may not pass. Edges must be strictly increasing;
# a price edge outside (0, 1) or a non-positive hour edge is not a band.
MIN_EDGES, MAX_EDGES = 2, 8
DEFAULT_PRICE_EDGES = [0.05, 0.20, 0.40, 0.60, 0.80, 0.95]
DEFAULT_HOURS_EDGES = [6, 24, 72, 168]
DEFAULT_AGE_EDGES = [6, 24, 72]
# Built-in mapper, used only when the tuning file is unusable: the two shapes
# with a measured footprint in strategy/screener-filters.json, and nothing
# else. A loud fallback should be visibly worse than the real file, not a
# silent second copy of it.
DEFAULT_FAMILY_RULES = [
    ("sports line", "title",
     r"\bspread\b|\bo\s*/\s*u\b|\bover\s*/\s*under\b|\bhandicap\b"),
    ("crypto", "title", r"\b(?:bitcoin|btc|ethereum|eth|solana)\b"),
    ("sports moneyline", "title", r"\bvs\.?\s|\bend\s+in\s+a\s+draw\b"),
]

UNBANDED = "(no reading)"


# ------------------------------------------------------------ tuning file

def _edges(raw, key, default, lo=None, hi=None):
    """One validated band-edge list. Never raises; degrades loudly."""
    got = raw.get(key)
    if got is None:
        return list(default)
    why = None
    if not isinstance(got, list) or not all(
            isinstance(x, (int, float)) and not isinstance(x, bool) for x in got):
        why = "not a list of numbers"
    elif not MIN_EDGES <= len(got) <= MAX_EDGES:
        why = f"{len(got)} edges, outside [{MIN_EDGES}, {MAX_EDGES}]"
    elif any(b <= a for a, b in zip(got, got[1:])):
        why = "not strictly increasing"
    elif lo is not None and (got[0] <= lo or got[-1] >= hi):
        why = f"edges outside ({lo}, {hi})"
    elif lo is None and got[0] <= 0:
        why = "a band edge is not positive"
    if why:
        print(f"screen_value: screener-value.json {key} {why}; using the "
              f"built-in {default}", file=sys.stderr)
        return list(default)
    return [float(x) for x in got]


def load_value_config():
    """The agent's family mapper and band edges, clamped into code bounds.

    Returns (rules, bands) where rules is [(family, field, compiled regex)]
    in file order and bands is the three validated edge lists. Same
    discipline as core/screen.py load_strata/load_filters: a broken tuning
    file costs ranking quality, it never stops the run.
    """
    bands = {"price": list(DEFAULT_PRICE_EDGES),
             "hours": list(DEFAULT_HOURS_EDGES),
             "age": list(DEFAULT_AGE_EDGES)}
    try:
        raw = json.loads(VALUE_FILE.read_text())
        if not isinstance(raw, dict):
            raise ValueError(f"top level is {type(raw).__name__}, not an object")
    except Exception as e:  # noqa: BLE001 - any failure falls back, loudly
        print(f"screen_value: strategy/screener-value.json unusable "
              f"({type(e).__name__}: {e}); ranking with the BUILT-IN mapper "
              f"({len(DEFAULT_FAMILY_RULES)} rules, not the agent's) and the "
              f"built-in bands - expect most markets in 'other'",
              file=sys.stderr)
        return _compile(DEFAULT_FAMILY_RULES), bands
    bands["price"] = _edges(raw, "price_band_edges", DEFAULT_PRICE_EDGES, 0.0, 1.0)
    bands["hours"] = _edges(raw, "hours_to_resolution_edges", DEFAULT_HOURS_EDGES)
    bands["age"] = _edges(raw, "market_age_hours_edges", DEFAULT_AGE_EDGES)
    spec = raw.get("families")
    if not isinstance(spec, list) or not spec:
        print(f"screen_value: screener-value.json families is "
              f"{type(spec).__name__}, not a non-empty list; using the "
              f"built-in mapper", file=sys.stderr)
        return _compile(DEFAULT_FAMILY_RULES), bands
    triples = []
    for i, rule in enumerate(spec):
        if not isinstance(rule, dict):
            print(f"screen_value: families[{i}] is not an object; skipped",
                  file=sys.stderr)
            continue
        fam, on, pat = rule.get("family"), rule.get("on", "title"), rule.get("pattern")
        if fam not in FAMILIES:
            print(f"screen_value: families[{i}] family {fam!r} is not one of "
                  f"{list(FAMILIES)}; skipped", file=sys.stderr)
            continue
        if on not in ("title", "slug"):
            print(f"screen_value: families[{i}] on={on!r} is not 'title' or "
                  f"'slug'; skipped", file=sys.stderr)
            continue
        if not isinstance(pat, str) or not pat:
            print(f"screen_value: families[{i}] pattern is missing or not a "
                  f"string; skipped", file=sys.stderr)
            continue
        triples.append((fam, on, pat))
    compiled = _compile(triples)
    if not compiled:
        print("screen_value: screener-value.json left no usable family rule; "
              "using the built-in mapper", file=sys.stderr)
        return _compile(DEFAULT_FAMILY_RULES), bands
    return compiled, bands


def _compile(triples):
    """Compile (family, field, pattern) triples; a bad regex is skipped loudly."""
    out = []
    for fam, on, pat in triples:
        try:
            out.append((fam, on, re.compile(pat, re.I)))
        except re.error as e:
            print(f"screen_value: family rule {fam!r} pattern {pat!r} does not "
                  f"compile ({e}); skipped, the rest still apply",
                  file=sys.stderr)
    return out


# ---------------------------------------------------------------- features

def family_of(question, slug, rules):
    """First matching rule wins; anything unmatched is 'other'."""
    text = {"title": question or "", "slug": slug or ""}
    for fam, on, rx in rules:
        if rx.search(text[on]):
            return fam
    return FALLBACK_FAMILY


def band_of(value, edges, fmt="{:g}"):
    """Half-open band label for `value` against `edges`, or None if unreadable."""
    if value is None:
        return None
    lo = None
    for e in edges:
        if value < e:
            return f"under {fmt.format(e)}" if lo is None else \
                   f"{fmt.format(lo)}-{fmt.format(e)}"
        lo = e
    return f"{fmt.format(edges[-1])} and over"


def hours_between(a, b):
    """Hours from ISO timestamp a to ISO timestamp b, or None if unparseable."""
    try:
        return (replay._parse_ts(b) - replay._parse_ts(a)).total_seconds() / 3600
    except (AttributeError, TypeError, ValueError):
        return None


def first_screened():
    """market_id -> earliest ts it appears in journal/screener.jsonl.

    The only market-age proxy this repo can compute offline. It is missing
    for a market the screener never saw, and it runs BACKWARDS for a market
    researched before 2026-08-25, when the screener journal starts: those
    rows get no age rather than a young one.
    """
    first = {}
    try:
        with open(SCREENER) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                mid, ts = str(r.get("market_id")), r.get("ts")
                if ts and (mid not in first or ts < first[mid]):
                    first[mid] = ts
    except OSError as e:
        print(f"screen_value: journal/screener.jsonl unreadable ({e}); no "
              f"market-age feature", file=sys.stderr)
    return first


def triggered_markets():
    """(market_id, cycle date) pairs researched inside a TRIGGERED cycle.

    strategy/funnel.jsonl carries tick_type on 101 of 258 cycles - the field
    starts 2026-08-25, the same day the watch tier does. Absence of the field
    is therefore absence of a trigger, not an unknown, so a row is TRIGGERED
    only when a TRIGGERED funnel line names its market on the same UTC day.
    """
    hits = set()
    try:
        with open(FUNNEL) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("tick_type") != "TRIGGERED":
                    continue
                day = (r.get("cycle") or "")[:10]
                for e in (r.get("researched") or []):
                    hits.add((str(e.get("market_id")), day))
    except OSError as e:
        print(f"screen_value: strategy/funnel.jsonl unreadable ({e}); every "
              f"row reads as FULL", file=sys.stderr)
    return hits


def settled_rows():
    """Settled, non-superseded forecast rows in record-time order.

    replay.load_rows()'s rule minus its fillability filter: a row with no ask
    at record time could not have been traded, but its belief was still
    recorded against a market price and still grades.
    """
    rows = []
    with open(replay.FORECASTS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("status") not in ("won", "lost"):
                continue
            if r.get("superseded_by"):
                continue
            if r.get("market_prob_at_record") is None:
                continue
            rows.append(r)
    rows.sort(key=lambda r: (r["ts"], r["id"]))
    return rows


def observations(rules, bands):
    """One scored observation per settled row, with its pre-research features."""
    first, triggered = first_screened(), triggered_markets()
    out = []
    for r in settled_rows():
        mid = str(r.get("market_id"))
        won = 1 if r["status"] == "won" else 0
        mkt = r["market_prob_at_record"]
        age = None
        if mid in first:
            h = hours_between(first[mid], r["ts"])
            age = h if h is not None and h >= 0 else None
        hours = max(0.0, hours_between(r["ts"], r["end_date"]) or 0.0)
        out.append({
            "id": r["id"], "ts": r["ts"], "market_id": mid,
            "settled_ts": r.get("settled_ts") or r["ts"],
            "cluster": screen_replay.cluster_of(mid, counterfactual.EVENT_OF),
            "question": r["question"], "slug": r.get("slug"),
            "agent_category": r.get("category"), "skip_reason": r.get("skip_reason"),
            "market_prob": mkt, "hours_raw": hours, "age_raw": age,
            "family": family_of(r["question"], r.get("slug"), rules),
            "price_band": band_of(mkt, bands["price"], "{:.2f}"),
            "hours_band": band_of(hours, bands["hours"], "{:.0f}h"),
            "age_band": band_of(age, bands["age"], "{:.0f}h"),
            "tick": "TRIGGERED" if (mid, r["ts"][:10]) in triggered else "FULL",
            "brier_delta": (r["est_prob"] - won) ** 2 - (mkt - won) ** 2,
        })
    return out


# ------------------------------------------------------------------- prior

# The features the prior reads. Every one of them is legible on a screener row
# BEFORE the slot is spent - a feature only readable after research cannot
# rank anything. Liquidity and 24h volume are deliberately absent: they exist
# at record time only inside the 16 local collect-run briefs, 103 of the 542
# settled rows, so the prior would be fitted on a fifth of its own evidence.
PRIOR_FEATURES = ("family", "price_band", "hours_band", "age_band")


def eb_offsets(items, feature):
    """Empirical-Bayes shrinkage of one feature's per-level brier_delta.

    The raw per-level means in `fit`'s tables are what a ranking would like
    to use and exactly what it must not: with 15 to 173 rows a level, most of
    the spread between them is sampling noise, and ranking on noise spends
    the scarce slot worse than ranking on nothing. So each level is pulled
    back toward the global mean by

        offset = B * (level_mean - global),  B = tau2 / (tau2 + se^2)

    with se the event-clustered standard error the rest of this module uses
    and tau2 the between-level variance left after subtracting the sampling
    variance (method of moments, floored at zero). A level whose interval is
    wide next to the spread between levels gets B near 0 and contributes
    nothing; tau2 = 0 collapses every offset to zero, which is the honest
    answer when the levels are indistinguishable.

    Returns {level: {n, events, raw, se, b, offset}} plus the global mean
    under the key None. Levels with no reading are excluded, not lumped: a
    market whose age cannot be read gets no age term rather than a made-up one.
    """
    groups = collections.defaultdict(list)
    for s in items:
        lvl = s.get(feature)
        if lvl is not None:
            groups[lvl].append(s)
    n_all = len(items)
    mu = sum(s["brier_delta"] for s in items) / n_all if n_all else 0.0
    stats = {}
    for lvl, rows in groups.items():
        m = sum(s["brier_delta"] for s in rows) / len(rows)
        se = screen_replay.mean_se(rows, lambda s: s["brier_delta"])
        stats[lvl] = {"n": len(rows), "events": len({s["cluster"] for s in rows}),
                      "raw": m, "se": se}
    usable = [v for v in stats.values() if v["se"]]
    tau2 = 0.0
    if len(usable) > 1:
        tau2 = max(0.0, sum((v["raw"] - mu) ** 2 - v["se"] ** 2
                            for v in usable) / len(usable))
    for v in stats.values():
        b = 0.0 if not v["se"] else tau2 / (tau2 + v["se"] ** 2)
        v["b"] = round(b, 4)
        v["offset"] = screen_replay.rounded(b * (v["raw"] - mu), 5)
        v["raw"] = screen_replay.rounded(v["raw"])
        v["ci95"] = None if v["se"] is None else round(1.96 * v["se"], 4)
        v["se"] = None if v["se"] is None else round(v["se"], 5)
    return {"global": screen_replay.rounded(mu, 5), "tau2": round(tau2, 8),
            "levels": stats}


def fit_prior(items, features=PRIOR_FEATURES):
    """The whole prior: a global mean plus one shrunk offset table per feature.

    Additive by construction. A market's expected research edge is the global
    mean plus the offset of every feature it can read, so a market missing a
    feature falls back toward the global mean instead of dropping out of the
    ranking. Additive because the evidence does not support a cross: the
    smallest family-by-price cell in this journal holds one row.
    """
    n = len(items)
    mu = sum(s["brier_delta"] for s in items) / n if n else 0.0
    return {"n": n, "events": len({s["cluster"] for s in items}),
            "global": screen_replay.rounded(mu, 5),
            "features": {f: eb_offsets(items, f) for f in features}}


def prior_score(prior, feats):
    """Expected research edge for one market, and the features it could not read.

    NEGATIVE is good: it is a brier_delta, so a market whose prior is below
    zero is one where this agent's research has beaten the price it was handed
    on markets that look like it. Returns (score, [unreadable feature names]).

    A feature value may be a list of levels rather than one, and then the
    offsets are averaged. That is not a convenience, it is the price band:
    the fit reads the band of the side research actually took, and a market
    nobody has researched yet offers both sides at once. Averaging scores a
    30/70 market as the mean of the 0.20-0.40 and 0.60-0.80 offsets, which is
    the expected offset when the side is still unchosen.
    """
    score, missing = prior["global"], []
    for f, table in prior["features"].items():
        val = feats.get(f)
        levels = val if isinstance(val, (list, tuple)) else [val]
        hits = [table["levels"][x]["offset"] for x in levels
                if x is not None and x in table["levels"]]
        if not hits:
            missing.append(f)
        else:
            score += sum(hits) / len(hits)
    return score, missing


# ------------------------------------------------------------------- cells

def cell(items, pnl_of, folds):
    """n, events, brier_delta with an event-clustered interval, held-out pnl.

    The interval is screen_replay.mean_se, the sandwich estimator every
    number in that module carries: a market re-forecast across cycles and a
    gamma event sold as many markets are ONE observation, and treating them
    as several would shrink the interval by roughly the square root of the
    repeat count. The pnl is counterfactual.py's own walk-forward cut of the
    cell's rows, so a cell whose edge lives entirely in its last fold reads
    as such.
    """
    n = len(items)
    if not n:
        return {"n": 0, "events": 0, "brier_delta": None, "ci95": None,
                "z": None, "n_pnl": 0, "pnl": 0.0, "held_out_pnl": 0.0,
                "fold_pnl": []}
    mean = sum(s["brier_delta"] for s in items) / n
    se = screen_replay.mean_se(items, lambda s: s["brier_delta"])
    led = sorted((pnl_of[s["id"]] for s in items if s["id"] in pnl_of),
                 key=lambda r: (r["ts"], r["id"]))
    per, held = counterfactual.fold_pnl(led, folds) if led else ([], 0.0)
    return {
        "n": n, "events": len({s["cluster"] for s in items}),
        "brier_delta": screen_replay.rounded(mean),
        "ci95": None if se is None else round(1.96 * se, 4),
        "z": None if not se else screen_replay.rounded(mean / se, 2),
        "n_pnl": len(led),
        "pnl": round(sum(r["pnl"] or 0.0 for r in led), 2),
        "held_out_pnl": held, "fold_pnl": per,
    }


def by(items, key, pnl_of, folds, order=None):
    """Ordered [{group, ...cell}] over one feature, biggest group first."""
    buckets = collections.defaultdict(list)
    for s in items:
        buckets[key(s) if key(s) is not None else UNBANDED].append(s)
    rows = [dict(group=k, **cell(v, pnl_of, folds)) for k, v in buckets.items()]
    if order:
        rows.sort(key=lambda r: (order.index(r["group"]) if r["group"] in order
                                 else len(order), r["group"]))
    else:
        rows.sort(key=lambda r: -r["n"])
    return rows


def fit_report(folds):
    """Every per-cell table the prior is fitted from, plus the global mean."""
    rules, bands = load_value_config()
    items = observations(rules, bands)
    pnl_of = {r["id"]: r for r in counterfactual.build()}
    price_order = [band_of(e - 1e-9, bands["price"], "{:.2f}") for e in bands["price"]]
    price_order.append(band_of(1.0, bands["price"], "{:.2f}"))
    return {
        "rows": len(items),
        "window": {"from": items[0]["ts"], "to": items[-1]["ts"]} if items else {},
        "folds": folds,
        "clustering": screen_replay.clustering_note(items),
        "bands": bands,
        "family_rules": len(rules),
        "prior": fit_prior(items),
        "overall": cell(items, pnl_of, folds),
        "groups": {
            "family": by(items, lambda s: s["family"], pnl_of, folds, list(FAMILIES)),
            "price_band": by(items, lambda s: s["price_band"], pnl_of, folds, price_order),
            "hours_band": by(items, lambda s: s["hours_band"], pnl_of, folds),
            "age_band": by(items, lambda s: s["age_band"], pnl_of, folds),
            "tick": by(items, lambda s: s["tick"], pnl_of, folds),
        },
    }


def print_fit(rep):
    print(f"screen_value fit: {rep['rows']} settled non-superseded forecast rows, "
          f"{rep['clustering']['clusters']} independent events, "
          f"{rep['folds']} walk-forward folds")
    if rep["window"]:
        print(f"  window {rep['window']['from']} .. {rep['window']['to']}   "
              f"family rules {rep['family_rules']}   "
              f"markets clustered {rep['clustering']['in_events']}, "
              f"alone {rep['clustering']['alone']}")
    o = rep["overall"]
    print(f"  overall brier_delta {o['brier_delta']:+.4f} "
          f"+/- {o['ci95']:.4f} (n {o['n']}, events {o['events']}); "
          f"counterfactual pnl {o['pnl']:+.2f}, held out {o['held_out_pnl']:+.2f}")
    print("  negative brier_delta = research beat the price it was handed")
    pr = rep["prior"]
    print(f"\nPRIOR (empirical-Bayes shrinkage toward the global mean "
          f"{pr['global']:+.5f}); this is what `rank` orders on")
    for f, table in pr["features"].items():
        if not table["levels"]:
            continue
        note = ("no usable spread between levels, every offset is zero"
                if not table["tau2"] else f"tau2 {table['tau2']:.2e}")
        print(f"\n  {f}  ({note})")
        print(f"    {'level':<22} {'n':>5} {'evts':>5} {'raw':>9} {'+/-':>8} "
              f"{'B':>6} {'offset':>9}")
        for lvl, v in sorted(table["levels"].items(), key=lambda kv: kv[1]["offset"]):
            ci = "       -" if v["ci95"] is None else f"{v['ci95']:>8.4f}"
            print(f"    {lvl:<22} {v['n']:>5} {v['events']:>5} "
                  f"{v['raw']:>+9.4f} {ci} {v['b']:>6.3f} {v['offset']:>+9.5f}")
    print("\n  a market's prior is the global mean plus the offset of every "
          "feature it can read")

    for name, rows in rep["groups"].items():
        print(f"\n{name:<22} {'n':>5} {'evts':>5} {'dBrier':>9} {'+/-':>8} "
              f"{'z':>6} {'n_pnl':>6} {'pnl':>9} {'held':>9}")
        print("  " + "-" * 84)
        for r in rows:
            ci = "       -" if r["ci95"] is None else f"{r['ci95']:>8.4f}"
            z = "     -" if r["z"] is None else f"{r['z']:>6.2f}"
            print(f"  {r['group']:<20} {r['n']:>5} {r['events']:>5} "
                  f"{r['brier_delta']:>+9.4f} {ci} {z} {r['n_pnl']:>6} "
                  f"{r['pnl']:>+9.2f} {r['held_out_pnl']:>+9.2f}")


# -------------------------------------------------------------------- rank

WORK_ROOT = ROOT / "reports" / "screener-work"
OUTCOMES = ROOT / "journal" / "screener-outcomes.jsonl"
RANK_K = 15  # config/protected.json screen.top_n, the size of the morning list


def screener_runs():
    """collect ts -> that run's screener rows, oldest run first.

    Rows of one collect run share the ts screen.py stamps on them, the same
    re-keying journal/screener-rank-decision.md calls "pooled": it is the list
    the cycle actually researches from, not the per-batch cut.
    """
    runs = {}
    with open(SCREENER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            runs.setdefault(r["ts"], []).append(r)
    return dict(sorted(runs.items()))


def end_dates(work_root):
    """market_id -> end_date, from the outcomes cache then the batch briefs.

    end_date is a market ATTRIBUTE that existed when the market was screened,
    so reading it from a cache filled later leaks no outcome. Nothing else is
    taken from that file - not status, not winner.

    The briefs are the only other source and they are gitignored, so a
    worktree sees none of them unless --work-root points at a checkout that
    has them. Coverage is reported in rank's header rather than assumed.
    """
    out = {}
    try:
        with open(OUTCOMES) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("end_date"):
                    out[str(r["market_id"])] = r["end_date"]
    except OSError as e:
        print(f"screen_value: journal/screener-outcomes.jsonl unreadable ({e})",
              file=sys.stderr)
    root = pathlib.Path(work_root)
    if root.is_dir():
        for brief in sorted(root.glob("*/batch-*.json")):
            try:
                data = json.loads(brief.read_text())
            except (OSError, ValueError):
                continue
            for m in (data.get("markets") or []) if isinstance(data, dict) else []:
                if isinstance(m, dict) and m.get("end_date"):
                    out.setdefault(str(m.get("market_id")), m["end_date"])
    return out


def screened_features(row, run_ts, rules, bands, end_of, first_seen):
    """The pre-research features of a SCREENED row, same bands as the fit.

    Two of them read differently here than in `observations`, and both
    differences are in the header rather than buried:

      * family has no slug to match on - journal/screener.jsonl carries the
        question and not the slug - so only the title rules can fire.
      * price_band is a list, one band per outcome, because no side has been
        chosen yet. See prior_score.
    """
    mid = str(row.get("market_id"))
    mids = row.get("mids") if isinstance(row.get("mids"), dict) else {}
    prices = [p for p in mids.values() if isinstance(p, (int, float))]
    end = end_of.get(mid)
    hours = hours_between(run_ts, end) if end else None
    first = first_seen.get(mid)
    age = hours_between(first, run_ts) if first else None
    return {
        "family": family_of(row.get("question"), None, rules),
        "price_band": [band_of(p, bands["price"], "{:.2f}") for p in prices] or None,
        "hours_band": band_of(max(0.0, hours), bands["hours"], "{:.0f}h")
                      if hours is not None else None,
        "age_band": band_of(age, bands["age"], "{:.0f}h")
                    if age is not None and age > 0 else None,
    }


def rank_report(run, work_root, k=RANK_K):
    """Re-rank one collect run's screened pool by the prior. Writes nothing."""
    runs = screener_runs()
    if not runs:
        return {"error": "journal/screener.jsonl holds no collect run"}
    if run:
        hits = [t for t in runs if t == run or t.replace("-", "").replace(":", "")
                .startswith(run.replace("-", "").replace(":", ""))]
        if not hits:
            return {"error": f"no collect run matches {run!r}; the latest is "
                             f"{list(runs)[-1]}"}
        if len(hits) > 1:
            return {"error": f"{run!r} matches {len(hits)} runs: {hits[:5]}"}
        run_ts = hits[0]
    else:
        run_ts = list(runs)[-1]
    rows = runs[run_ts]

    rules, bands = load_value_config()
    # Walk-forward by construction: the prior may only see rows that had
    # SETTLED before this run was collected. A prior fitted on the whole
    # journal would rank a run of 2026-08-25 using outcomes from September.
    train = [s for s in observations(rules, bands) if s["settled_ts"] < run_ts]
    if len(train) < 2:
        return {"error": f"only {len(train)} forecast rows had settled before "
                         f"{run_ts}; nothing to fit a prior on"}
    prior = fit_prior(train)

    first_seen = first_screened()
    end_of = end_dates(work_root)
    scored, missing = [], collections.Counter()
    for r in rows:
        feats = screened_features(r, run_ts, rules, bands, end_of, first_seen)
        score, miss = prior_score(prior, feats)
        for f in miss:
            missing[f] += 1
        if len(miss) == len(PRIOR_FEATURES):
            missing["(nothing readable)"] += 1
        scored.append((score, r, feats, miss))
    # The prior takes at most families x age bands distinct values, so the
    # k/k+1 cut lands inside a tie group nearly always and SOMETHING has to
    # order it. Divergence, the incumbent, does - never the market_id, which
    # screen_replay.top_k_weights records as biased rather than merely
    # arbitrary. How many slots the prior itself decided is in the header.
    scored.sort(key=lambda t: (t[0], -(t[1].get("divergence") or 0.0),
                               str(t[1].get("market_id"))))
    top = scored[:k]
    cut = top[-1][0] if top else None
    decided = sum(1 for sc, _, _, _ in scored if sc < cut) if top else 0
    tied = sum(1 for sc, _, _, _ in scored if sc == cut) if top else 0

    div = sorted((r for r in rows if r.get("divergence") is not None),
                 key=lambda r: r["divergence"], reverse=True)[:k]
    div_ids = {str(r["market_id"]) for r in div}
    return {
        "run": run_ts, "pool": len(rows), "k": k,
        "slots_decided_by_prior": decided, "tie_group_at_cut": tied,
        "distinct_priors": len({sc for sc, _, _, _ in scored}),
        "fit": {"from": train[0]["ts"], "to": train[-1]["ts"],
                "rows": prior["n"], "events": prior["events"],
                "global": prior["global"],
                "tau2": {f: t["tau2"] for f, t in prior["features"].items()}},
        "unscored": dict(missing),
        "overlap_with_divergence_top": len(
            {str(r.get("market_id")) for _, r, _, _ in top} & div_ids),
        "families": dict(collections.Counter(f["family"] for _, _, f, _ in top)),
        "mean_prior": screen_replay.rounded(
            sum(sc for sc, _, _, _ in top) / len(top), 5) if top else None,
        "rows": [dict(r, value_prior=screen_replay.rounded(sc, 5),
                      value_features={kk: vv for kk, vv in f.items()})
                 for sc, r, f, _ in top],
    }


def print_rank(rep):
    """Header to stderr, the top k to stdout as collect prints them."""
    print(f"screen_value rank: {rep['run']}, pool {rep['pool']}, "
          f"top {rep['k']} by prior (most negative first)", file=sys.stderr)
    fit = rep["fit"]
    print(f"  prior fitted on {fit['rows']} rows / {fit['events']} events that "
          f"settled before this run (record ts {fit['from']} .. "
          f"{fit['to']}), "
          f"global {fit['global']:+.5f}", file=sys.stderr)
    flat = [f for f, t in fit["tau2"].items() if not t]
    if flat:
        print(f"  no usable spread, contributing nothing: {', '.join(flat)}",
              file=sys.stderr)
    if rep["unscored"]:
        parts = ", ".join(f"{f} {n}" for f, n in sorted(rep["unscored"].items()))
        print(f"  rows the prior could not read, of {rep['pool']}: {parts}",
              file=sys.stderr)
    else:
        print(f"  every row of the pool was readable on all "
              f"{len(PRIOR_FEATURES)} features", file=sys.stderr)
    print(f"  mean prior of the list {rep['mean_prior']:+.5f}; families "
          f"{rep['families']}", file=sys.stderr)
    print(f"  markets also in the divergence top {rep['k']}: "
          f"{rep['overlap_with_divergence_top']}", file=sys.stderr)
    print(f"  the prior takes {rep['distinct_priors']} distinct values on this "
          f"pool and decided {rep['slots_decided_by_prior']} of {rep['k']} "
          f"slots outright; the other "
          f"{rep['k'] - rep['slots_decided_by_prior']} sit in one tie group of "
          f"{rep['tie_group_at_cut']} and were ordered by divergence",
          file=sys.stderr)
    print("  wrote nothing: no journal, no quota, no marker", file=sys.stderr)
    for row in rep["rows"]:
        print(json.dumps(row))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit", help="the per-cell research-edge table this "
                                   "journal supports")
    f.add_argument("--folds", type=int, default=5)
    f.add_argument("--json", action="store_true")
    r = sub.add_parser("rank", help="re-rank one collect run's screened pool "
                                    "by the prior; writes nothing")
    r.add_argument("--run", default=None,
                   help="collect ts, or a prefix of it; default the latest run")
    r.add_argument("--work-root", default=str(WORK_ROOT),
                   help="where the batch briefs live, for end_date; default "
                        "this repo's reports/screener-work")
    r.add_argument("--top", type=int, default=RANK_K)
    r.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "fit":
        if a.folds < 2:
            sys.exit("--folds must be >= 2")
        rep = fit_report(a.folds)
        if a.json:
            print(json.dumps(rep, indent=1))
        else:
            print_fit(rep)
        return
    if a.top < 1:
        sys.exit("--top must be >= 1")
    rep = rank_report(a.run, a.work_root, a.top)
    if rep.get("error"):
        sys.exit(f"screen_value rank: {rep['error']}")
    if a.json:
        print(json.dumps(rep, indent=1))
    else:
        print_rank(rep)


if __name__ == "__main__":
    main()
