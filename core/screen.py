#!/usr/bin/env python3
"""Screening tier: rank scanned markets by price-vs-estimate gap.

PROTECTED CORE - the trading agent must not edit files under core/.

Why this exists (operator, 2026-08-24): frontier-model research reached ~3 of
~1,000 scanned markets per cycle, picked by intuition. Coverage, not depth, is
the binding constraint. This screens a stratified slice of EVERY scanned
candidate and hands the agent a ranked shortlist. It ranks; it does not gate -
the agent may still research anything it likes.

Why there is no API path (operator constraint, 2026-08-24): the operator will
not spend outside the Claude subscription, so this file NEVER calls the
Anthropic API and holds no API key. The screening judgment is produced by
Haiku subagents that the cycle agent fans out with its own Task tool - they
ride the session's plan, and their usage is subscription-billed. Anything that
reintroduces a metered call belongs in journal/proposals.md, not here.

Split of responsibilities, now three-way:
  * THE MACHINERY is here: the stratified pre-filter, the strata bounds, the
    batch files, the exact subagent prompt, the output schema, the daily batch
    quota and the journal contract. None of it is reachable from a prompt edit.
  * THE JUDGMENT is the agent's: `strategy/screener-prompt.md` is the brief
    each subagent reads, and `strategy/screener-strata.json` tunes the strata
    sizes within the code bounds below. Both are the agent's to rewrite from
    the screener's own record.
  * THE TRANSPORT is the cycle agent's Task fan-out: `prepare` writes what the
    subagents read, the subagents write out-NN.json, `collect` reads it back.
    This file is the two deterministic bookends and nothing in between.

If `strategy/screener-strata.json` is missing or malformed this uses the
built-in defaults and says so loudly on stderr - same rule as scan.py's
discovery fallback. A broken tuning file degrades coverage, it never silently
stops the screen.

Two things this deliberately does NOT do:
  * It NEVER writes journal/forecasts.jsonl. Screener probabilities are cheap
    triage guesses, not honest researched beliefs; letting them near the
    forecast ledger would corrupt brier_delta and violate CYCLE.md's
    "never invent an estimate" rule. Screener output lives only in
    journal/screener.jsonl, which nothing else writes.
  * It never places, sizes or vetoes anything. It emits a reading list.

Divergence caveat: `outcome_prices` come from gamma's market record - they are
STALE MIDS, not fillable prices. A large divergence means "worth a look", not
"tradeable edge"; the live book (spread, depth) is still checked downstream by
the normal research path before any bet.

Row cost columns: `input_tokens`, `output_tokens` and `cost_usd` are always 0.
Subagent usage is subscription-billed and is not metered here - the fields stay
in the schema so the journal's shape is stable across the 2026-08-24 switch
away from the metered API tier, and so a future metered path could fill them.

Usage:
  python3 core/scan.py --hours 336 --limit 800 | python3 core/screen.py prepare
  python3 core/screen.py prepare --file candidates.jsonl
  python3 core/screen.py prepare --dry-run     # header only, writes nothing
  python3 core/screen.py collect --dir reports/screener-work/<stamp>
Input:  scan.py candidate JSON lines on stdin or --file (prepare).
Output: prepare prints a JSON header (work_dir, batches, screened_pool,
        dropped_by_reason, subagent_prompt_template) on stdout and writes the
        batch files under reports/screener-work/<UTCstamp>/ (gitignored).
        collect prints the top-N rows by divergence as JSON lines on stdout,
        appends one row per market to journal/screener.jsonl, and summarises
        on stderr.

Pre-filter (operator, 2026-09-04, from gnhf run 3's journal/screener-rank-
decision.md): before the strata see anything, `prepare` drops the shapes in
`strategy/screener-filters.json` - the title regexes for line-constructed and
sub-daily crypto markets, mids of exactly 0.500, and non-binary outcome sets.
These are the rules of screener-prompt.md that a model is not needed for, and
the Haiku tier's worst habit (a lazy 0.50/0.50 answer that manufactures the
largest divergence on the markets the price is surest about) landed three
quarters of the time on exactly these shapes. The filter file is the agent's
to tune; a broken file degrades to no title filters and says so on stderr.
Every filter reports its count in the header's dropped_by_reason as
`filter:<name>`, so the footprint of each rule stays public.

Quota: the day's cost is counted in BATCHES, not dollars, under
journal/screener-quota/<runner>.json - one file per runner, committed, so
subagent load is public and survives container churn. Two runners (the cloud
routine and the operator machine's loop.sh) cycle on the same hours, and a
single shared counter was a read-modify-write race that lost updates on every
interleaved push (2026-09-04). Each runner writes only its own file and the
cap applies to the SUM across today's files, so the day's usage merges
without conflict. The runner name is $PHIL_RUNNER, else "operator" when
loop.sh's PHIL_PUSH_BY_LOOP is set, else "cloud". `prepare` reserves the
batches it writes before any subagent runs, so a cycle that crashes
mid-fan-out still consumed its reservation; over-counting is the safe
direction. Once the day's batches reach `max_batches_per_day` this exits 0
with an empty stdout: an exhausted quota must degrade the cycle, never kill
it.

The agent may call this freely but may not edit it; if the strata, the row
schema or the quota guard are wrong, that is a journal/proposals.md entry.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTECTED = json.loads((ROOT / "config" / "protected.json").read_text())
PROMPT_FILE = ROOT / "strategy" / "screener-prompt.md"
STRATA_FILE = ROOT / "strategy" / "screener-strata.json"
FILTERS_FILE = ROOT / "strategy" / "screener-filters.json"
LOG_FILE = ROOT / "journal" / "screener.jsonl"
QUOTA_DIR = ROOT / "journal" / "screener-quota"
WORK_ROOT = ROOT / "reports" / "screener-work"

# Deterministic pre-filter defaults; strategy/screener-filters.json overrides
# them within these types. See load_filters.
FILTER_DEFAULTS = {"exclude_mids_exactly_half": True, "min_outcomes": 2,
                   "max_outcomes": 2}
HALF_EPS = 1e-9

SCREENER_DEFAULTS = {"batch_size": 20, "top_n": 15, "max_batches_per_day": 150,
                     "max_pool_after_strata": 400}

# Hard ceilings on the config tunables. Raising either is a protected-core
# edit, by design - same story as REAL_HARD_CEILINGS in core/validate.py.
MAX_POOL_CEILING = 400
MAX_BATCHES_PER_DAY_CEILING = 300

# The four strata, in the order they claim markets (a market lands in the
# first stratum that takes it; later strata see only the remainder).
#   closing_48h    - anything resolving inside CLOSING_WINDOW_H. Short fuse,
#                    highest information turnover.
#   top_liquidity  - deepest books. A gap here is a real disagreement.
#   top_volume_24h - what is actually being traded right now.
#   random_tail    - the long-tail audit lane. Without it the screen only ever
#                    sees the markets the other three strata already like, and
#                    can never learn that its own selection is the problem.
# `min` is the floor a strategy/screener-strata.json edit may not go under and
# `max` the default it may not go over: the agent can shrink a lane, and can
# close every lane except the audit lane.
CLOSING_WINDOW_H = 48
STRATA_BOUNDS = {
    "closing_48h": {"default": 80, "min": 0, "max": 80},
    "top_liquidity": {"default": 120, "min": 0, "max": 120},
    "top_volume_24h": {"default": 60, "min": 0, "max": 60},
    "random_tail": {"default": 40, "min": 20, "max": 40},
}
STRATA_ORDER = ("closing_48h", "top_liquidity", "top_volume_24h", "random_tail")

CONFIDENCES = {"low", "medium", "high"}

REQUIRED_INPUT_FIELDS = ("market_id", "question", "outcomes", "outcome_prices")

DEFAULT_MODEL_LABEL = "subagent:haiku"

COLLECTED_MARKER = ".collected"

# The exact text the cycle agent hands each Task subagent, one per batch file,
# with {work_dir} already filled in and the literal NN left for the agent to
# substitute. It carries the rules that used to be the API system preamble:
# honest calibration, stale mids, no browsing, exact outcome names.
SUBAGENT_PROMPT_TEMPLATE = """\
You are the screening tier of a prediction-market research pipeline. Work from \
the repository root. Do these three things, in order, and nothing else.

1. Read {work_dir}/batch-NN.json. It holds {{"batch_id", "markets", "mids"}}; \
"markets" is the batch, one object per market.
2. Read strategy/screener-prompt.md. That is the judgment brief - what counts \
as worth a researcher's next hour. Follow it.
3. Use the Write tool to write a JSON array to {work_dir}/out-NN.json, one \
object per market in "markets", every market exactly once:
[{{"market_id": "<id exactly as given>", "prob": {{"<outcome name>": <0-1>, \
...}}, "confidence": "low"|"medium"|"high", "reason": "<one short line>"}}]

Rules:
- Use the exact outcome names given for that market. Probabilities must be \
non-negative and sum to about 1.
- You are NOT deciding trades. A downstream researcher spends real effort on \
the markets whose probabilities differ most from the market price, so be \
honestly calibrated and honestly uncertain - both a falsely confident number \
and a lazy echo of the market price waste that effort.
- The prices in the file are stale mids. Do not copy them. If after thinking \
you genuinely agree with the price, say so with your own number and let the \
divergence be small.
- Use only what you already know plus the market text. Do not browse, search \
or fetch. If resolving the question needs information you do not have, that is \
exactly what confidence "low" is for - say so in the reason.
- confidence "high" means you would defend the number without further research.
- Write the file. Do not print the array, do not summarise it, do not explain \
your reasoning. Your final message is one line: "wrote out-NN.json, <n> \
markets"."""


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def iso(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp(ts):
    return ts.strftime("%Y%m%dT%H%M%SZ")


def today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def screener_config():
    cfg = PROTECTED.get("screener")
    if not isinstance(cfg, dict):
        print("screen: config/protected.json has no 'screener' block; "
              "using built-in defaults", file=sys.stderr)
        cfg = {}
    out = dict(SCREENER_DEFAULTS)
    for k, v in SCREENER_DEFAULTS.items():
        got = cfg.get(k)
        if isinstance(got, int) and not isinstance(got, bool) and got > 0:
            out[k] = got
        elif got is not None:
            print(f"screen: config screener.{k} = {got!r} is not a positive "
                  f"integer; using the default {v}", file=sys.stderr)
    if out["max_pool_after_strata"] > MAX_POOL_CEILING:
        print(f"screen: max_pool_after_strata {out['max_pool_after_strata']} "
              f"exceeds the protected ceiling {MAX_POOL_CEILING}; clamping",
              file=sys.stderr)
        out["max_pool_after_strata"] = MAX_POOL_CEILING
    if out["max_batches_per_day"] > MAX_BATCHES_PER_DAY_CEILING:
        print(f"screen: max_batches_per_day {out['max_batches_per_day']} "
              f"exceeds the protected ceiling {MAX_BATCHES_PER_DAY_CEILING}; "
              f"clamping", file=sys.stderr)
        out["max_batches_per_day"] = MAX_BATCHES_PER_DAY_CEILING
    return out


def strata_sizes():
    """Agent-tuned stratum sizes, clamped into the code bounds. Never raises."""
    sizes = {k: b["default"] for k, b in STRATA_BOUNDS.items()}
    try:
        raw = json.loads(STRATA_FILE.read_text())
        if not isinstance(raw, dict):
            raise ValueError(f"top level is {type(raw).__name__}, not an object")
    except Exception as e:  # noqa: BLE001 - any failure falls back, loudly
        print(f"screen: strategy/screener-strata.json unusable "
              f"({type(e).__name__}: {e}); using the built-in strata sizes - "
              f"coverage tuning is ignored until it is fixed", file=sys.stderr)
        return sizes
    for name, bounds in STRATA_BOUNDS.items():
        got = raw.get(name)
        if got is None:
            continue
        if not isinstance(got, int) or isinstance(got, bool):
            print(f"screen: screener-strata.json {name} = {got!r} is not an "
                  f"integer; keeping {sizes[name]}", file=sys.stderr)
            continue
        clamped = max(bounds["min"], min(bounds["max"], got))
        if clamped != got:
            print(f"screen: screener-strata.json {name} = {got} outside the "
                  f"code bounds [{bounds['min']}, {bounds['max']}]; using "
                  f"{clamped}", file=sys.stderr)
        sizes[name] = clamped
    return sizes


def blob_rev(path):
    """Git blob hash of the bytes actually used, or 'unknown' outside a repo.

    `git hash-object` rather than `git rev-parse HEAD:<path>` on purpose: this
    log is the future training set, so the revision recorded must identify the
    exact text used, including an agent edit that has not been committed yet.
    For a clean working tree the two are the same hash.
    """
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "hash-object", "--", str(path)],
                             capture_output=True, text=True, timeout=10, check=True)
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001 - provenance is nice-to-have, never fatal
        return "unknown"


def runner_id():
    """Which runner this is, for the per-runner quota file. See the docstring."""
    name = (os.environ.get("PHIL_RUNNER") or "").strip()
    if not name:
        name = "operator" if os.environ.get("PHIL_PUSH_BY_LOOP") else "cloud"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)[:40]


def _empty_quota():
    return {"day": today(), "batches": 0, "markets_screened": 0,
            "last_prepare_utc": None}


def load_quota():
    """Today's usage across every runner file.

    Returns (own, by_runner, total_batches): `own` is this runner's record for
    today (fresh if absent or stale), `by_runner` maps runner -> today's
    batches for every file under journal/screener-quota/, and total_batches is
    their sum, which is what the cap applies to. A file from another day or
    an unreadable file counts as zero for today, loudly.
    """
    me = runner_id()
    own, by_runner = _empty_quota(), {}
    if QUOTA_DIR.is_dir():
        for path in sorted(QUOTA_DIR.glob("*.json")):
            try:
                q = json.loads(path.read_text())
                batches = int(q.get("batches") or 0) if q.get("day") == today() else 0
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"screen: {path.relative_to(ROOT)} unreadable ({e}); "
                      f"counting it as zero for today", file=sys.stderr)
                continue
            by_runner[path.stem] = batches
            if path.stem == me and q.get("day") == today():
                own = q
    return own, by_runner, sum(by_runner.values())


def save_quota(own):
    QUOTA_DIR.mkdir(parents=True, exist_ok=True)
    (QUOTA_DIR / f"{runner_id()}.json").write_text(json.dumps(own, indent=2) + "\n")


def load_filters():
    """Agent-tuned deterministic pre-filters. Never raises; degrades loudly.

    Returns (compiled, spec) where compiled is [(name, regex)] and spec is the
    validated scalar settings. Same discipline as strata_sizes: a broken tuning
    file costs list quality, it never stops the screen.
    """
    spec = dict(FILTER_DEFAULTS)
    try:
        raw = json.loads(FILTERS_FILE.read_text())
        if not isinstance(raw, dict):
            raise ValueError(f"top level is {type(raw).__name__}, not an object")
    except Exception as e:  # noqa: BLE001 - any failure falls back, loudly
        print(f"screen: strategy/screener-filters.json unusable "
              f"({type(e).__name__}: {e}); screening with NO title filters - "
              f"expect line-constructed markets back in the pool",
              file=sys.stderr)
        return [], spec
    got = raw.get("exclude_mids_exactly_half")
    if isinstance(got, bool):
        spec["exclude_mids_exactly_half"] = got
    elif got is not None:
        print(f"screen: screener-filters.json exclude_mids_exactly_half = "
              f"{got!r} is not true or false; keeping "
              f"{spec['exclude_mids_exactly_half']}", file=sys.stderr)
    for key in ("min_outcomes", "max_outcomes"):
        got = raw.get(key)
        if isinstance(got, int) and not isinstance(got, bool) and got >= 2:
            spec[key] = got
        elif got is not None:
            print(f"screen: screener-filters.json {key} = {got!r} is not an "
                  f"integer >= 2; keeping {spec[key]}", file=sys.stderr)
    compiled = []
    pats = raw.get("exclude_title_patterns")
    if pats is None:
        pats = []
    if not isinstance(pats, list):
        print(f"screen: screener-filters.json exclude_title_patterns is "
              f"{type(pats).__name__}, not a list; no title filters applied",
              file=sys.stderr)
        pats = []
    for i, item in enumerate(pats):
        if not isinstance(item, dict):
            print(f"screen: exclude_title_patterns[{i}] is not an object; "
                  f"skipped", file=sys.stderr)
            continue
        name = str(item.get("name") or f"pattern_{i}")
        pattern = item.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            print(f"screen: exclude_title_patterns[{i}] ({name}) has no "
                  f"pattern string; skipped", file=sys.stderr)
            continue
        try:
            compiled.append((name, re.compile(pattern, re.IGNORECASE)))
        except re.error as e:
            print(f"screen: exclude_title_patterns[{i}] ({name}) does not "
                  f"compile ({e}); skipped - the other filters still apply",
                  file=sys.stderr)
    return compiled, spec


def filters_fired(candidate, mids, compiled, spec):
    """Names of every deterministic filter that fires on this market."""
    fired = []
    question = str(candidate.get("question") or "")
    for name, rx in compiled:
        if rx.search(question):
            fired.append(name)
    n_out = len(mids)
    if n_out < spec["min_outcomes"] or n_out > spec["max_outcomes"]:
        fired.append("non_binary_outcomes")
    if spec["exclude_mids_exactly_half"] and mids \
            and all(abs(v - 0.5) <= HALF_EPS for v in mids.values()):
        fired.append("mids_exactly_half")
    return fired


def prefilter(candidates, compiled, spec):
    """Drop the shapes no model is needed for. Returns (kept, dropped_by_filter).

    A market that trips several filters is dropped once and counted under
    each, so the per-filter footprints stay comparable with the journal
    measurements in screener-filters.json.
    """
    kept, by_filter = [], {}
    for c in candidates:
        fired = filters_fired(c, mids_of(c), compiled, spec)
        if not fired:
            kept.append(c)
            continue
        for name in fired:
            by_filter[name] = by_filter.get(name, 0) + 1
    return kept, by_filter


def read_candidates(path):
    """Parse scan.py JSON lines. Returns (valid, n_bad); never raises on input."""
    if path:
        raw = pathlib.Path(path).read_text()
    else:
        raw = sys.stdin.read()
    valid, bad = [], 0
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            c = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"screen: input line {lineno}: invalid JSON ({e}); skipped",
                  file=sys.stderr)
            bad += 1
            continue
        missing = [f for f in REQUIRED_INPUT_FIELDS if c.get(f) in (None, "", [])]
        if missing or not isinstance(c.get("outcomes"), list) \
                or not isinstance(c.get("outcome_prices"), list):
            print(f"screen: input line {lineno}: not a scan candidate "
                  f"(missing/!list {missing or 'outcomes/outcome_prices'}); skipped",
                  file=sys.stderr)
            bad += 1
            continue
        valid.append(c)
    return valid, bad


def mids_of(c):
    """outcome name -> stale gamma mid, for the outcomes that have a price."""
    out = {}
    for name, price in zip(c.get("outcomes") or [], c.get("outcome_prices") or []):
        try:
            out[str(name)] = float(price)
        except (TypeError, ValueError):
            continue
    return out


def brief_of(c):
    """The per-market payload a subagent reads. Kept small - hundreds of these."""
    return {
        "market_id": str(c.get("market_id")),
        "question": c.get("question"),
        "outcomes": [str(o) for o in (c.get("outcomes") or [])],
        "market_prices": mids_of(c),
        "end_date": c.get("end_date"),
        "volume_24h": round(float(c.get("volume_24h") or 0)),
        "liquidity": round(float(c.get("liquidity") or 0)),
        "description": (c.get("description") or "")[:400],
    }


def chunk(seq, size):
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def parse_end_date(value):
    """Gamma endDate -> aware datetime, or None. Never raises."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        ts = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=dt.timezone.utc)


def num_of(c, field):
    try:
        return float(c.get(field) or 0)
    except (TypeError, ValueError):
        return 0.0


def sample_key(seed, market_id):
    """Deterministic per-run shuffle key, seeded on the prepare stamp.

    Per-run (not per-day) on purpose: each FULL cycle draws a fresh random
    tail, so the audit lane covers 4-6 x 40 distinct thin markets per day
    instead of re-screening one draw of 40 all day.
    """
    return hashlib.sha256(f"{seed}:{market_id}".encode()).hexdigest()


def stratify(candidates, sizes, pool_cap, now, seed):
    """Pick the screened pool. Returns (pool, lane_of, strata_counts, dropped).

    Strata claim markets in STRATA_ORDER; each sees only what earlier strata
    left, so the pool is deduped by construction.
    """
    remaining = {str(c.get("market_id")): c for c in candidates}
    horizon = now + dt.timedelta(hours=CLOSING_WINDOW_H)
    picked, counts, dropped = {}, {}, {}

    def take(name, ordered):
        cap = sizes[name]
        chosen = ordered[:cap]
        counts[name] = {"eligible": len(ordered), "selected": len(chosen)}
        if len(ordered) > len(chosen):
            dropped[f"{name}_beyond_stratum_size"] = len(ordered) - len(chosen)
        for c in chosen:
            mid = str(c.get("market_id"))
            picked[mid] = (c, name)
            remaining.pop(mid, None)

    closing = [c for c in remaining.values()
               if (parse_end_date(c.get("end_date")) or horizon + dt.timedelta(1)) <= horizon]
    closing.sort(key=lambda c: (parse_end_date(c.get("end_date")) or horizon,
                                str(c.get("market_id"))))
    take("closing_48h", closing)

    by_liq = sorted(remaining.values(),
                    key=lambda c: (-num_of(c, "liquidity"), str(c.get("market_id"))))
    take("top_liquidity", by_liq)

    by_vol = sorted(remaining.values(),
                    key=lambda c: (-num_of(c, "volume_24h"), str(c.get("market_id"))))
    take("top_volume_24h", by_vol)

    tail = sorted(remaining.values(),
                  key=lambda c: sample_key(seed, str(c.get("market_id"))))
    take("random_tail", tail)

    # Pool ceiling. Trim the biggest lane first and never below its floor, so a
    # tight cap eats the bulk strata before it touches the audit lane.
    trimmed = 0
    selected = {n: [mid for mid, (_c, s) in picked.items() if s == n]
                for n in STRATA_ORDER}
    while sum(len(v) for v in selected.values()) > pool_cap:
        lane = max(STRATA_ORDER,
                   key=lambda n: (len(selected[n]) - STRATA_BOUNDS[n]["min"], n))
        if len(selected[lane]) <= STRATA_BOUNDS[lane]["min"]:
            break  # everything left is floor; the cap cannot close the lanes
        dropped_mid = selected[lane].pop()
        picked.pop(dropped_mid, None)
        counts[lane]["selected"] -= 1
        trimmed += 1
    if trimmed:
        dropped["pool_cap_trim"] = trimmed

    # Interleave the lanes round-robin, each keeping its own rank order. Two
    # reasons, both about failure modes: a batch trimmed off the end by the
    # daily quota then costs every lane a little instead of closing the audit
    # lane outright, and one subagent that dies takes a slice of each lane
    # rather than all of one.
    lanes = {n: [picked[mid][0] for mid in selected[n]] for n in STRATA_ORDER}
    pool = []
    for i in range(max((len(v) for v in lanes.values()), default=0)):
        for name in STRATA_ORDER:
            if i < len(lanes[name]):
                pool.append(lanes[name][i])
    lane_of = {str(c.get("market_id")): s for c, s in picked.values()}
    return pool, lane_of, counts, dropped


def recount_selected(pool, lane_of, counts):
    """Re-derive each stratum's selected count from the pool that survived."""
    for name in STRATA_ORDER:
        counts.setdefault(name, {"eligible": 0, "selected": 0})["selected"] = 0
    for c in pool:
        lane = lane_of.get(str(c.get("market_id")))
        if lane:
            counts[lane]["selected"] += 1
    return counts


def write_work_dir(work_dir, batches, sizes, counts, dropped, cfg, prompt_rev, ts):
    work_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for i, batch in enumerate(batches, 1):
        nn = f"{i:02d}"
        payload = {
            "batch_id": f"{work_dir.name}-{nn}",
            "markets": [brief_of(c) for c in batch],
            "mids": {str(c.get("market_id")): mids_of(c) for c in batch},
        }
        (work_dir / f"batch-{nn}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        written.append({"nn": nn, "batch_file": f"batch-{nn}.json",
                        "out_file": f"out-{nn}.json", "markets": len(batch)})
    manifest = {
        "created_utc": iso(ts), "work_dir": str(work_dir.relative_to(ROOT)),
        "batch_size": cfg["batch_size"], "top_n": cfg["top_n"],
        "prompt_rev": prompt_rev, "strata_sizes": sizes, "strata": counts,
        "dropped_by_reason": dropped, "batches": written,
    }
    (work_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return written


def cmd_prepare(args):
    cfg = screener_config()
    if args.batch_size is not None:
        cfg["batch_size"] = max(1, args.batch_size)
    if args.top_n is not None:
        cfg["top_n"] = max(1, args.top_n)

    candidates, n_bad = read_candidates(args.file)
    if n_bad:
        print(f"screen: {n_bad} input line(s) failed the candidate contract",
              file=sys.stderr)
    if not candidates:
        print("screen: no valid candidates on input; nothing to screen",
              file=sys.stderr)
        return 0

    quota, by_runner, used = load_quota()
    cap = cfg["max_batches_per_day"]
    if used >= cap:
        print(f"screen: daily screener batch quota exhausted ({used} / {cap} "
              f"batches, UTC day {quota['day']}, by runner {by_runner}) - "
              f"screening skipped, no subagents to spawn. Research unscreened "
              f"candidates as before and log 'screener quota exhausted'; do "
              f"not work around.", file=sys.stderr)
        return 0

    n_in = len(candidates)
    compiled, spec = load_filters()
    filters_rev = blob_rev(FILTERS_FILE) if FILTERS_FILE.is_file() else None
    candidates, by_filter = prefilter(candidates, compiled, spec)
    if not candidates:
        print("screen: the pre-filter left no candidates to screen "
              f"({by_filter}); nothing to do", file=sys.stderr)
        return 0

    sizes = strata_sizes()
    now = utcnow()
    pool, lane_of, counts, dropped = stratify(
        candidates, sizes, cfg["max_pool_after_strata"], now, stamp(now))
    for name, n in sorted(by_filter.items()):
        dropped[f"filter:{name}"] = n
    if n_bad:
        dropped["unparseable_input_line"] = n_bad
    filters = {"file": str(FILTERS_FILE.relative_to(ROOT)), "rev": filters_rev,
               "loaded": [n for n, _ in compiled], "dropped_by_filter": by_filter}

    batches = chunk(pool, cfg["batch_size"])
    if len(batches) > cap - used:
        cut = batches[cap - used:]
        batches = batches[:cap - used]
        dropped["daily_batch_quota"] = sum(len(b) for b in cut)
        print(f"screen: only {cap - used} of {cap} daily batches left; "
              f"dropping {dropped['daily_batch_quota']} market(s) from this "
              f"screen", file=sys.stderr)
    pool = [c for b in batches for c in b]
    counts = recount_selected(pool, lane_of, counts)

    prompt_rev = blob_rev(PROMPT_FILE)
    work_dir = WORK_ROOT / stamp(now)
    rel_dir = str(work_dir.relative_to(ROOT))
    template = SUBAGENT_PROMPT_TEMPLATE.format(work_dir=rel_dir)

    if args.dry_run:
        header = {"dry_run": True, "work_dir": rel_dir, "batch_count": len(batches),
                  "batches": [{"nn": f"{i:02d}", "batch_file": f"batch-{i:02d}.json",
                               "out_file": f"out-{i:02d}.json", "markets": len(b)}
                              for i, b in enumerate(batches, 1)],
                  "screened_pool": len(pool), "candidates_in": n_in,
                  "strata": counts, "dropped_by_reason": dropped,
                  "filters": filters,
                  "day_batches_used": used, "day_batches_by_runner": by_runner,
                  "runner": runner_id(), "max_batches_per_day": cap,
                  "prompt_rev": prompt_rev,
                  "subagent_prompt_template": template}
        print(json.dumps(header, indent=2))
        print(f"screen: dry run - would screen {len(pool)} of {len(candidates)} "
              f"candidates in {len(batches)} batches; nothing written, no quota "
              f"reserved", file=sys.stderr)
        return 0

    if not batches:
        print("screen: stratification left no markets to screen", file=sys.stderr)
        return 0

    written = write_work_dir(work_dir, batches, sizes, counts, dropped, cfg,
                             prompt_rev, now)

    # Reserve before any subagent runs: a cycle that dies mid-fan-out has still
    # spent the reservation. Over-counting is the safe direction.
    quota["batches"] = int(quota.get("batches") or 0) + len(batches)
    quota["markets_screened"] = int(quota.get("markets_screened") or 0) + len(pool)
    quota["last_prepare_utc"] = iso(now)
    save_quota(quota)
    by_runner[runner_id()] = quota["batches"]
    day_used = used + len(batches)

    header = {"work_dir": rel_dir, "batch_count": len(written), "batches": written,
              "screened_pool": len(pool), "candidates_in": n_in,
              "strata": counts, "dropped_by_reason": dropped, "filters": filters,
              "day_batches_used": day_used, "day_batches_by_runner": by_runner,
              "runner": runner_id(), "max_batches_per_day": cap,
              "prompt_rev": prompt_rev, "subagent_prompt_template": template}
    print(json.dumps(header, indent=2))
    print(f"screen: prepared {len(pool)} markets in {len(written)} batches under "
          f"{rel_dir}; day batches {day_used}/{cap} ({by_runner}). Spawn one Task "
          f"subagent per batch with subagent_prompt_template, then run: "
          f"python3 core/screen.py collect --dir {rel_dir}", file=sys.stderr)
    return 0


def parse_answers(text):
    """Subagent out file -> {market_id: answer}. Raises ValueError if unusable."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
        t = t.strip()
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        start, end = t.find("["), t.rfind("]")
        if start < 0 or end <= start:
            raise ValueError("no JSON array in the out file") from None
        data = json.loads(t[start:end + 1])
    if isinstance(data, dict):
        # Haiku subagents intermittently wrap the required top-level array as
        # {"batch_id": ..., "scores": [...]} (7/30 day-1 batches, 140 markets
        # lost — proposals.md 2026-08-25 04:16Z). A real answer object carries
        # market_id, a wrapper never does.
        if data.get("market_id") is None and isinstance(data.get("scores"), list):
            data = data["scores"]
        else:
            data = [data]
    if not isinstance(data, list):
        raise ValueError(f"out file holds {type(data).__name__}, not a list")
    out = {}
    for item in data:
        if isinstance(item, dict) and item.get("market_id") is not None:
            out[str(item["market_id"])] = item
    return out


def row_base(market, mids, ts, model, prompt_rev, batch_id):
    return {"ts": ts, "market_id": str(market.get("market_id")),
            "question": market.get("question"), "model": model,
            "prompt_rev": prompt_rev, "probs": None, "mids": mids,
            "divergence": None, "confidence": None, "reason": None,
            "batch_id": batch_id, "input_tokens": 0, "output_tokens": 0,
            "cost_usd": 0.0}


def grade_answer(row, answer):
    """Fill probs/divergence/confidence/reason, or set screen_error. No raises."""
    if not isinstance(answer, dict):
        row["screen_error"] = "no answer for this market in the batch out file"
        return row
    probs, mids = {}, row["mids"]
    raw = answer.get("prob")
    if not isinstance(raw, dict) or not raw:
        row["screen_error"] = f"prob is not a non-empty object ({type(raw).__name__})"
        return row
    for name, p in raw.items():
        try:
            p = float(p)
        except (TypeError, ValueError):
            continue
        if 0.0 <= p <= 1.0:
            probs[str(name)] = p
    if not probs:
        row["screen_error"] = "no outcome probability in [0, 1]"
        return row
    row["probs"] = probs
    shared = set(probs) & set(mids)
    if not shared:
        row["screen_error"] = ("subagent outcome names match none of the market's "
                               f"outcomes ({sorted(probs)} vs {sorted(mids)})")
        return row
    row["divergence"] = round(max(abs(probs[o] - mids[o]) for o in shared), 4)
    conf = answer.get("confidence")
    row["confidence"] = conf if conf in CONFIDENCES else "unknown"
    reason = answer.get("reason")
    row["reason"] = str(reason)[:300] if reason is not None else None
    return row


def load_batch_file(path):
    """Read one batch-NN.json. Returns (batch_id, markets, mids) or None."""
    try:
        data = json.loads(path.read_text())
        markets = data.get("markets")
        if not isinstance(markets, list):
            raise ValueError("'markets' is not a list")
    except Exception as e:  # noqa: BLE001 - a corrupt batch file is skipped, loudly
        print(f"screen: {path.name} unreadable ({type(e).__name__}: {e}); "
              f"batch skipped", file=sys.stderr)
        return None
    mids = data.get("mids") if isinstance(data.get("mids"), dict) else {}
    return str(data.get("batch_id") or path.stem), markets, mids


def cmd_collect(args):
    cfg = screener_config()
    if args.top_n is not None:
        cfg["top_n"] = max(1, args.top_n)

    work_dir = pathlib.Path(args.dir)
    if not work_dir.is_absolute():
        work_dir = ROOT / work_dir
    if not work_dir.is_dir():
        print(f"screen: {args.dir} is not a directory - nothing to collect",
              file=sys.stderr)
        return 1
    marker = work_dir / COLLECTED_MARKER
    if marker.is_file():
        print(f"screen: {args.dir} was already collected "
              f"({marker.read_text().strip()}) - refusing to append "
              f"journal/screener.jsonl twice. Re-run prepare for a fresh "
              f"screen; do not delete the marker.", file=sys.stderr)
        return 1

    batch_files = sorted(work_dir.glob("batch-*.json"))
    if not batch_files:
        print(f"screen: no batch-NN.json under {args.dir}", file=sys.stderr)
        return 1

    ts = iso(utcnow())
    prompt_rev = blob_rev(PROMPT_FILE)
    rows, n_batches, expected = [], 0, 0
    for bf in batch_files:
        loaded = load_batch_file(bf)
        if loaded is None:
            continue
        batch_id, markets, mids_map = loaded
        n_batches += 1
        expected += len(markets)
        out_path = work_dir / bf.name.replace("batch-", "out-", 1)
        answers, out_err = {}, None
        if not out_path.is_file():
            out_err = f"subagent wrote no {out_path.name}"
        else:
            try:
                answers = parse_answers(out_path.read_text())
            except Exception as e:  # noqa: BLE001 - a bad out file is per-row error
                out_err = f"unparseable {out_path.name}: {type(e).__name__}: {e}"
        if out_err:
            print(f"screen: {out_err}", file=sys.stderr)
        for m in markets:
            if not isinstance(m, dict):
                continue
            mid = str(m.get("market_id"))
            mids = mids_map.get(mid)
            if not isinstance(mids, dict):
                mids = m.get("market_prices") if isinstance(
                    m.get("market_prices"), dict) else {}
            row = row_base(m, mids, ts, args.model_label, prompt_rev, batch_id)
            if out_err:
                row["screen_error"] = out_err
                rows.append(row)
            else:
                rows.append(grade_answer(row, answers.get(mid)))

    if not rows:
        print(f"screen: {args.dir} held no readable markets; nothing logged",
              file=sys.stderr)
        return 1

    with LOG_FILE.open("a") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    marker.write_text(f"collected {ts} - {len(rows)} rows appended to "
                      f"journal/screener.jsonl\n")

    ranked = sorted((r for r in rows if r.get("divergence") is not None),
                    key=lambda r: r["divergence"], reverse=True)
    escalated = ranked[:cfg["top_n"]]
    for row in escalated:
        print(json.dumps(row))

    n_err = sum(1 for r in rows if r.get("screen_error"))
    if n_err:
        print(f"screen: {n_err} market(s) came back malformed (see screen_error "
              f"in journal/screener.jsonl)", file=sys.stderr)
    _own, by_runner, used = load_quota()
    print(f"screen: collected {len(ranked)}/{expected} markets from {n_batches} "
          f"batches, escalated {len(escalated)}, day batches "
          f"{used}/{cfg['max_batches_per_day']} (by runner {by_runner})",
          file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare", help="stratify, write batch files and the "
                                       "subagent prompt; reserve the quota")
    p.add_argument("--file", default=None,
                   help="read scan candidates from this file instead of stdin")
    p.add_argument("--dry-run", action="store_true",
                   help="print the header only; nothing written, no quota reserved")
    p.add_argument("--batch-size", type=int, default=None,
                   help="override config screener.batch_size")
    p.add_argument("--top-n", type=int, default=None,
                   help="override config screener.top_n")
    p.set_defaults(func=cmd_prepare)

    c = sub.add_parser("collect", help="read the subagents' out files, log rows "
                                       "and rank by divergence")
    c.add_argument("--dir", required=True,
                   help="the work dir prepare printed (reports/screener-work/<stamp>)")
    c.add_argument("--model-label", default=DEFAULT_MODEL_LABEL,
                   help=f"value for the row's model field (default "
                        f"{DEFAULT_MODEL_LABEL})")
    c.add_argument("--top-n", type=int, default=None,
                   help="override config screener.top_n")
    c.set_defaults(func=cmd_collect)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
