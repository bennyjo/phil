#!/usr/bin/env python3
"""Experiment ledger grader: the verdict on each self-improvement experiment.

PROTECTED CORE - the trading agent must not edit files under core/.

An experiment is the unit of self-improvement. The deep retro proposes one,
implements it in agent-owned files, and pre-registers in
strategy/experiments.jsonl the metric that judges it, the baseline, the window
and the bars. This tool computes that metric and prints the verdict, so no
experiment is kept or rolled back on a hand tally (the same rule as the paired
rule test in core/score.py).

Ledger (strategy/experiments.jsonl, agent-owned, append-only). One JSON
object per line, folded by id:

  {"event": "open", "id": "E-2026-11-17-a", "ts": "2026-11-17T05:50:00Z",
   "hypothesis": "...", "lever": ["strategy/playbook.md#research-floor"],
   "commit": "<sha of the experiment's change commit>",
   "metric": "nonsat_rows_per_full", "window": {"n": 14},
   "baseline": 7.0, "baseline_asof": "2026-11-17T05:49:00Z",
   "keep_if": ">= 9.0", "rollback_if": "< 6.0 or min_rows_per_full < 8",
   "prior": [], "blocked_by_core": null}
  {"event": "verdict", "id": "...", "ts": "...", "verdict": "KEEP",
   "value": 9.6, "n": 14, "source": "core/experiments.py grade"}
  {"event": "close", "id": "...", "ts": "...",
   "outcome": "kept" | "rolled_back" | "inconclusive" | "withdrawn",
   "lesson": "one line that goes in the playbook"}

  A row with "commit": null and a "blocked_by_core" text records a lever in
  a protected file the agent cannot change. It is not an experiment: it is
  graded as BLOCKED and does not count toward the open cap.

  The experiment's change is its own commit, pushed before the open row is
  written, so `commit` is final and a later `git revert` of it never touches
  this append-only file.

Windows run forward from the commit's committer time. {"days": D} ends D days
later; {"n": K} ends at the K-th unit of the metric (FULL cycles, settled
rows, bets: `propose` prints the unit); with both, whichever comes first.
Rate and snapshot metrics take days only. The baseline is the same window
immediately before the commit, computed with only the data known at
baseline_asof, so it is reproducible and the validator re-checks it.

A paired metric whose zero means "no effect" (rule_verdict, screener_delta,
replay_cw_return) can have no data before the commit: a new rule slug, a
new prompt_rev or a new policy. For those `propose` prints "baseline": null
instead of refusing, the bars are absolute (keep_if "< -0.01" on
rule_verdict means the rule beats raw by 0.01), and the validator accepts
the null only while the window before the commit is still empty. Every
other metric needs a numeric baseline.

Conditions (keep_if, rollback_if): clauses "<op> <number>" on the
experiment's metric or "<metric> <op> <number>" on another catalog metric
over the same span, ops >= <= > <, joined with "and" (binds tighter) and
"or".

Verdicts (grade):
  COLLECTING n=<k>/<needed>  window not over, no rollback trigger yet
  ROLL BACK     rollback_if holds after at least half the window, or at its end
  KEEP          keep_if holds at window end
  DOUBLE DOWN   KEEP with the effect at least twice the bar (value - baseline
                against threshold - baseline; a null baseline counts as 0),
                or the interval entirely past the threshold
  INCONCLUSIVE  window over, neither bar reached
  BLOCKED       a blocked_by_core row; waits on an operator PR

Event floor. The metrics over forecast rows (tight_dbrier, rule_verdict)
count independent events, keyed (category, end date) as core/score.py
clusters them, and get no verdict on fewer than EVENT_FLOOR (10): grade
reads COLLECTING while the window runs and INCONCLUSIVE at its end. Rows of
one event share one outcome, so a window of 40 box-office rows on 7 film
weekends holds 7 observations; a KEEP or ROLL BACK on them would record
noise as a lesson.

Subcommands:
  propose --metric NAME --window SPEC --commit SHA   prints the open row's
          computed fields (baseline, baseline_asof, window); copy them as-is.
          It also prints what the window can detect, from the same window
          before the commit: baseline_events, and mde, the smallest effect a
          two-sided 5% test finds with 80% power (2.8 standard errors,
          clustered by event; times sqrt(2) for a numeric baseline, because
          the forward window is compared with the baseline window). Set the
          bars at least mde from the baseline (from 0 for a null baseline).
  grade [--json] [--asof TS]                         one line per open row
  status [--lever PATH] [--json]                     the folded ledger
  scoreboard [--since TS] [--json] [--asof TS]       the primary metric and
          its target, and the guard metrics a change must not worsen. The
          primary metric is set by the operator: mean dBrier against the
          price on tight books (spread <= 0.06, no placeholder books; superseded
          rows count) over the rows settled in the last PRIMARY_DAYS (30) days,
          with a 95% interval clustered by event; the target is met when the
          interval sits below zero. --since adds the same metric since that
          time (the last deep retro).

check_ledger() is the ledger half of core/validate.py.

Offline; reads the journals and git only.
"""
import argparse
import collections
import datetime as dt
import importlib.util
import json
import math
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import replay  # noqa: E402
import score  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER_REL = "strategy/experiments.jsonl"

MAX_OPEN = 3
MAX_FILES_PER_COMMIT = 2
FAILED_LEVER_DAYS = 30
# DEEP-2026-11-15: a cell (category) is saturated at the book when it has at
# least 35 settled forecasts and |dBrier| <= 0.005.
SATURATED_MIN_N = 35
SATURATED_MAX_ABS_DBRIER = 0.005
# A tight book, as the deep retros slice it: spread at most 6 cents.
TIGHT_SPREAD = 0.06
BASELINE_TOLERANCE = 1e-4
# Paired metrics whose zero means "no effect": the only ones that may open
# with "baseline": null when the window before the commit has no data.
NULL_BASELINE_METRICS = ("rule_verdict", "screener_delta", "replay_cw_return")
# A metric over forecast rows (tight_dbrier, rule_verdict) gets no verdict on
# fewer independent events than this: the count below which core/score.py
# shows no interval. Rows of one event share one outcome driver, so 40 rows
# on 7 film weekends are 7 observations, not 40.
EVENT_FLOOR = score.RULE_MIN_CI_EVENTS
# propose's smallest detectable effect: a two-sided 5% test with 80% power
# is 1.96 + 0.84 standard errors from no effect.
MDE_Z = 2.80
# The scoreboard's primary metric: forecast skill against the price on tight
# books, over the rows that settled in the trailing PRIMARY_DAYS. The target
# is met when the 95% interval sits below zero. Set by the operator.
PRIMARY_DAYS = 30

VERDICTS = ("COLLECTING", "KEEP", "ROLL BACK", "DOUBLE DOWN", "INCONCLUSIVE",
            "BLOCKED")
OUTCOMES = ("kept", "rolled_back", "inconclusive", "withdrawn")
DAY = dt.timedelta(days=1)


# ---------------------------------------------------------------- time, git

def parse_ts(value):
    """YYYY-MM-DDTHH:MM:SS[.fff]Z (or an offset) -> aware UTC datetime."""
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    t = dt.datetime.fromisoformat(text)
    return t.replace(tzinfo=dt.timezone.utc) if t.tzinfo is None \
        else t.astimezone(dt.timezone.utc)


def iso(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def git(root, *args, check=True):
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                       text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p


def resolve_commit(root, sha):
    p = git(root, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}",
            check=False)
    return p.stdout.strip() if p.returncode == 0 else None


def commit_time(root, sha):
    return parse_ts(git(root, "show", "-s", "--format=%cI", sha).stdout.strip())


def is_ancestor(root, sha, head="HEAD"):
    return git(root, "merge-base", "--is-ancestor", sha, head,
               check=False).returncode == 0


def commit_files(root, sha):
    out = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r",
              "--root", sha).stdout
    return [f for f in out.splitlines() if f]


def show_file(root, rev, path):
    p = git(root, "show", f"{rev}:{path}", check=False)
    return p.stdout if p.returncode == 0 else None


# ---------------------------------------------------------------- journals

def _jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]


class Journal:
    """The journals as they were known at `asof`.

    A row exists once its ts is past; an outcome counts once its settled_ts
    is past; a supersede counts once its superseded_ts is past. Rows carry
    the derived booleans `_settled` and `_superseded` and the datetimes `_ts`
    and `_sts`.
    """

    def __init__(self, root, asof):
        self.root = pathlib.Path(root)
        self.asof = asof
        self._cache = {}

    def _load(self, rel):
        if rel not in self._cache:
            self._cache[rel] = _jsonl(self.root / rel)
        return self._cache[rel]

    def forecasts(self):
        out = []
        for r in self._load("journal/forecasts.jsonl"):
            t = parse_ts(r["ts"])
            if t > self.asof:
                continue
            row = dict(r, _ts=t, _settled=False, _superseded=False, _sts=None)
            if r.get("status") in ("won", "lost"):
                sts = parse_ts(r.get("settled_ts") or r["end_date"])
                if sts <= self.asof:
                    row["_settled"], row["_sts"] = True, sts
            if r.get("superseded_by"):
                sup = r.get("superseded_ts")
                row["_superseded"] = sup is None or parse_ts(sup) <= self.asof
            out.append(row)
        return out

    def fulls(self):
        out = []
        for r in self._load("strategy/funnel.jsonl"):
            if r.get("tick_type") != "FULL" or not r.get("cycle"):
                continue
            t = parse_ts(r["cycle"])
            if t <= self.asof:
                out.append(dict(r, _ts=t))
        return out

    def bets(self):
        out = []
        for r in self._load("journal/ledger.jsonl"):
            t = parse_ts(r["ts"])
            if t <= self.asof:
                out.append(dict(r, _ts=t))
        return out

    def screener(self):
        rel = ["journal/screener.jsonl"] + sorted(
            p.relative_to(self.root).as_posix()
            for p in (self.root / "journal" / "screener").glob("*.jsonl"))
        out = []
        for path in rel:
            for r in self._load(path):
                if r.get("ts") and parse_ts(r["ts"]) <= self.asof:
                    out.append(r)
        return out

    def screener_outcomes(self):
        """market_id -> latest outcome row checked by asof."""
        cache = {}
        for r in self._load("journal/screener-outcomes.jsonl"):
            if r.get("market_id") is None or not r.get("checked_ts"):
                continue
            if parse_ts(r["checked_ts"]) > self.asof:
                continue
            row = dict(r)
            try:
                row["end_date"] = iso(parse_ts(r.get("end_date")))
            except (TypeError, ValueError):
                row["end_date"] = None
            cache[str(r["market_id"])] = row
        return cache


# ---------------------------------------------------------------- metrics

Unit = collections.namedtuple("Unit", "rec at sample event", defaults=(None,))
# rec: when the unit entered the record (a forward window counts units
# recorded at or after the commit); at: when the unit became known (windows
# are ordered and cut on it); sample: the per-unit value, if any; event: the
# (category, end date) key core/score.py clusters forecast rows by, for the
# metrics whose units are forecast rows.


def _event(r):
    return (r["category"], (r.get("end_date") or "")[:10])


def _y(r):
    return 1.0 if r["status"] == "won" else 0.0


def _dbrier(r):
    y = _y(r)
    return (r["est_prob"] - y) ** 2 - (r["market_prob_at_record"] - y) ** 2


def _scored_forecasts(j):
    """Settled, live, non-placeholder forecasts: score.py's headline set."""
    return [r for r in j.forecasts() if r["_settled"] and not r["_superseded"]
            and not score.placeholder_book(r)]


def saturated_categories(j, anchor):
    by_cat = collections.defaultdict(list)
    for r in _scored_forecasts(j):
        if r["_sts"] < anchor:
            by_cat[r["category"]].append(_dbrier(r))
    return {c for c, ds in by_cat.items()
            if len(ds) >= SATURATED_MIN_N
            and abs(sum(ds) / len(ds)) <= SATURATED_MAX_ABS_DBRIER}


def _full_rows(r):
    return [x for x in r.get("researched") or [] if x.get("forecast_id")]


def u_rows_per_full(j, arg, anchor):
    return [Unit(r["_ts"], r["_ts"], float(len(_full_rows(r))))
            for r in j.fulls()]


def u_nonsat_rows_per_full(j, arg, anchor):
    sat = saturated_categories(j, anchor)
    cat_of = {r["id"]: r["category"] for r in j.forecasts()}
    out = []
    for r in j.fulls():
        n = sum(1 for x in _full_rows(r)
                if (x.get("category") or cat_of.get(x["forecast_id"])) not in sat)
        out.append(Unit(r["_ts"], r["_ts"], float(n)))
    return out


def u_fulls(j, arg, anchor):
    return [Unit(r["_ts"], r["_ts"], None) for r in j.fulls()]


def u_forecast_rows(j, arg, anchor):
    return [Unit(r["_ts"], r["_ts"], None) for r in j.forecasts()]


def u_bets(j, arg, anchor):
    return [Unit(r["_ts"], r["_ts"], None) for r in j.bets()]


def u_tight_dbrier(j, arg, anchor):
    out = []
    for r in _scored_forecasts(j):
        bid, ask = r.get("best_bid_at_record"), r.get("best_ask_at_record")
        if round(ask - bid, 4) > TIGHT_SPREAD:
            continue
        if arg and r["category"] != arg:
            continue
        out.append(Unit(r["_ts"], r["_sts"], _dbrier(r), _event(r)))
    return out


def u_rule(j, arg, anchor):
    # Superseded rows count, as in score.rule_verdicts.
    return [Unit(r["_ts"], r["_sts"], r, _event(r)) for r in j.forecasts()
            if r.get("rule") == arg and r["_settled"]]


def a_rule(units):
    v = score.paired_rule_test([u.sample for u in units])
    if not v["n"]:
        return None, None, v["verdict"]
    return v["mean_delta"], v.get("ci"), v["verdict"]


def _load_policy(root, commit, path):
    """The policy file as committed in the experiment's commit."""
    src = show_file(root, commit, path) if commit else None
    if src is None:
        src = (pathlib.Path(root) / path).read_text()
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(src)
    spec = importlib.util.spec_from_file_location("experiment_policy", fh.name)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    finally:
        pathlib.Path(fh.name).unlink()
    return mod


def u_replay(j, arg, anchor, commit=None):
    """The bets the policy places on rows whose outcome was unknown at the
    anchor (core/replay.py --after), fitted on rows settled before it."""
    policy = _load_policy(j.root, commit, arg)
    rows = [r for r in j.forecasts() if r["_settled"] and not r["_superseded"]
            and r.get("best_ask_at_record") is not None]
    rows.sort(key=lambda r: (r["ts"], r["id"]))
    fit = getattr(policy, "fit", None)
    state = fit([replay.history_row({k: v for k, v in r.items()
                                     if not k.startswith("_")})
                 for r in rows if r["_sts"] < anchor]) if fit else None
    out = []
    for r in rows:
        clean = {k: v for k, v in r.items() if not k.startswith("_")}
        for bet in replay.score_rows(policy, [clean], state):
            out.append(Unit(r["_sts"], r["_sts"], bet))
    return out


def a_replay(units):
    if not units:
        return None, None, None
    s = replay.summarize([u.sample for u in units])
    return s["cw_return"], None, f"pnl {s['pnl']:+.2f} roi {s['roi']:+.4f}"


def u_screener(j, arg, anchor):
    import screen_replay  # deferred: heavier import, only this metric needs it
    rows = [r for r in j.screener()
            if (r.get("prompt_rev") or "").startswith(arg)]
    cache = j.screener_outcomes()
    scored, _, _ = screen_replay.select(rows, cache, None, None, None)
    out = []
    for s in scored:
        t = parse_ts(s["ts"])
        checked = parse_ts(cache[s["market_id"]]["checked_ts"])
        out.append(Unit(t, max(t, checked), s))
    return out


def a_screener(units):
    import screen_replay
    if not units:
        return None, None, None
    s = screen_replay.summarize([u.sample for u in units])
    ci = None
    if s.get("delta_ci95") is not None:
        ci = [round(s["delta"] - s["delta_ci95"], 4),
              round(s["delta"] + s["delta_ci95"], 4)]
    return s["delta"], ci, f"excess {s['excess']}"


def playbook_lines_at(root, t):
    p = git(root, "rev-list", "-1", "--first-parent", f"--before={iso(t)}",
            "HEAD", check=False)
    rev = p.stdout.strip()
    if not rev:
        return None
    text = show_file(root, rev, "strategy/playbook.md")
    return None if text is None else float(len(text.splitlines()))


Metric = collections.namedtuple("Metric", "kind unit units agg arg scale doc")
# kind: rate (units per day * scale, days windows only), mean (mean of unit
# samples with a 95% interval), min (smallest unit sample), custom (agg over
# the units), snapshot (a value at a time, days windows only).

CATALOG = {
    "forecast_rows_per_day": Metric(
        "rate", "day", u_forecast_rows, None, False, 1,
        "forecast rows recorded per day"),
    "fulls_per_day": Metric(
        "rate", "day", u_fulls, None, False, 1, "FULL cycles per day"),
    "bets_per_week": Metric(
        "rate", "day", u_bets, None, False, 7, "paper bets placed per week"),
    "rows_per_full": Metric(
        "mean", "FULL", u_rows_per_full, None, False, 1,
        "forecast rows per FULL cycle (funnel researched entries)"),
    "min_rows_per_full": Metric(
        "min", "FULL", u_rows_per_full, None, False, 1,
        "fewest forecast rows in any FULL cycle of the window"),
    "nonsat_rows_per_full": Metric(
        "mean", "FULL", u_nonsat_rows_per_full, None, False, 1,
        "forecast rows per FULL outside saturated cells (n >= 35 settled, "
        "|dBrier| <= 0.005, as of the commit)"),
    "tight_dbrier": Metric(
        "mean", "settled row", u_tight_dbrier, None, "optional", 1,
        "mean dBrier of settled tight-book (spread <= 0.06) forecasts "
        "recorded in the window; tight_dbrier:<category> for one cell"),
    "rule_verdict": Metric(
        "custom", "settled row", u_rule, a_rule, "required", 1,
        "rule_verdict:<slug>: paired rule-minus-raw Brier (core/score.py "
        "paired_rule_test) over the rule's rows recorded in the window"),
    "replay_cw_return": Metric(
        "custom", "bet", u_replay, a_replay, "required", 1,
        "replay_cw_return:<policy path>: core/replay.py forward cw_return of "
        "the policy as committed, on rows settled in the window"),
    "screener_delta": Metric(
        "custom", "screened market", u_screener, a_screener, "required", 1,
        "screener_delta:<prompt_rev prefix>: core/screen_replay.py Brier "
        "delta (screen minus mids) on markets screened in the window"),
    "playbook_lines": Metric(
        "snapshot", "day", None, None, False, 1,
        "lines in strategy/playbook.md at the end of the window"),
}
# Metrics whose units are forecast rows: they count independent events, and
# grade gives no verdict on fewer than EVENT_FLOOR of them.
EVENT_METRICS = (u_tight_dbrier, u_rule)


def parse_metric(name):
    """'tight_dbrier:soccer' -> (Metric, 'soccer'). Raises ValueError."""
    base, _, arg = name.partition(":")
    m = CATALOG.get(base)
    if m is None:
        raise ValueError(f"metric {base!r} is not in the catalog "
                         f"({', '.join(sorted(CATALOG))})")
    if m.arg is False and arg:
        raise ValueError(f"metric {base} takes no argument")
    if m.arg == "required" and not arg:
        raise ValueError(f"metric {base} needs an argument: {m.doc}")
    if base == "replay_cw_return" and not arg.startswith("strategy/"):
        raise ValueError("replay_cw_return needs a policy path under strategy/")
    return m, arg or None


def parse_window(window, metric):
    """{'days': D, 'n': K} -> (days or None, n or None). Raises ValueError."""
    if not isinstance(window, dict) or not window or \
            set(window) - {"days", "n"}:
        raise ValueError("window must be an object with 'days' and/or 'n'")
    days, n = window.get("days"), window.get("n")
    for name, v in (("days", days), ("n", n)):
        if v is not None and (isinstance(v, bool)
                              or not isinstance(v, (int, float)) or v <= 0):
            raise ValueError(f"window {name} must be a positive number")
    if n is not None and int(n) != n:
        raise ValueError("window n must be a whole number")
    if metric.kind in ("rate", "snapshot") and (n is not None or days is None):
        raise ValueError(f"a {metric.kind} metric takes a days window only")
    return days, (int(n) if n is not None else None)


def parse_window_spec(text):
    out = {}
    for part in text.split(","):
        key, _, val = part.strip().partition("=")
        if key not in ("days", "n") or not val:
            raise ValueError(f"window spec {text!r}: use days=D, n=K or both")
        out[key] = float(val) if key == "days" else int(val)
        if key == "days" and out[key] == int(out[key]):
            out[key] = int(out[key])
    return out


CLAUSE = re.compile(r"^(?:(?P<metric>[a-z_]+(?::\S+)?)\s+)?"
                    r"(?P<op>>=|<=|>|<)\s*(?P<num>[-+]?\d+(?:\.\d+)?)$")
OPS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
       ">": lambda a, b: a > b, "<": lambda a, b: a < b}


def parse_condition(text):
    """'< 6 or min_rows_per_full < 8' -> [[(None, '<', 6.0)], [(m, '<', 8.0)]]
    (a list of and-groups joined by or). Raises ValueError."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("condition must be a non-empty string")
    groups = []
    for part in re.split(r"\s+or\s+", text.strip()):
        group = []
        for clause in re.split(r"\s+and\s+", part.strip()):
            m = CLAUSE.match(clause.strip())
            if not m:
                raise ValueError(f"cannot parse clause {clause!r}: use "
                                 f"'<op> <number>' or '<metric> <op> <number>'")
            if m["metric"]:
                parse_metric(m["metric"])
            group.append((m["metric"], m["op"], float(m["num"])))
        groups.append(group)
    return groups


# ---------------------------------------------------------------- windows

def _aggregate(metric, units, span_days):
    """(value, ci, detail) for a window's units."""
    if metric.kind == "rate":
        if span_days is None or span_days <= 0:
            return None, None, None
        return len(units) / span_days * metric.scale, None, None
    if metric.kind in ("mean", "min"):
        xs = [u.sample for u in units]
        if not xs:
            return None, None, None
        if metric.kind == "min":
            return min(xs), None, None
        mean = sum(xs) / len(xs)
        ci = None
        if len(xs) >= 2:
            sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))
            half = 1.96 * sd / math.sqrt(len(xs))
            ci = [mean - half, mean + half]
        return mean, ci, None
    return metric.agg(units)


def _units(metric, j, arg, anchor, commit):
    if metric.units is u_replay:
        return u_replay(j, arg, anchor, commit)
    return metric.units(j, arg, anchor)


def measure(root, metric_name, window, anchor, asof, forward, commit=None,
            span=None):
    """The metric over one window.

    forward=True: the window that starts at the anchor (the commit time);
    False: the baseline window that ends at it. span=(lo, hi) evaluates a
    secondary metric over a fixed time span instead of a window.
    Returns a dict: value, n, ci, lo, hi, complete, half, detail.
    """
    metric, arg = parse_metric(metric_name)
    days, k = parse_window(window, metric) if span is None else (None, None)
    cap = anchor + days * DAY if forward and days else None

    if span is not None:
        lo, hi = span
    elif forward:
        lo, hi = anchor, min(asof, cap) if cap else asof
    else:
        lo, hi = (anchor - days * DAY if days else None), anchor

    if metric.kind == "snapshot":
        value = playbook_lines_at(root, hi - dt.timedelta(seconds=1))
        elapsed = (hi - lo).total_seconds() / 86400
        return {"value": value, "n": round(elapsed, 1), "ci": None, "lo": lo,
                "hi": hi, "complete": bool(cap and asof >= cap),
                "half": bool(cap and elapsed >= days / 2), "detail": None}

    units = _units(metric, Journal(root, asof), arg, anchor, commit)
    if span is not None:
        us = [u for u in units if lo <= u.rec and u.at < hi]
    elif forward:
        us = [u for u in units if lo <= u.rec and u.at <= asof
              and (cap is None or u.at < cap)]
    else:
        us = [u for u in units if u.at < hi and (lo is None or lo <= u.rec)]
    us.sort(key=lambda u: u.at)
    if k and forward:
        us = us[:k]
        if len(us) >= k:
            hi = us[-1].at + dt.timedelta(microseconds=1)
    elif k:
        us = us[-k:]
        if lo is None:
            lo = us[0].rec if us else hi

    span_days = (hi - lo).total_seconds() / 86400
    value, ci, detail = _aggregate(metric, us, span_days)
    complete = half = False
    if forward and span is None:
        elapsed = (hi - lo).total_seconds() / 86400
        complete = bool((k and len(us) >= k) or (cap and asof >= cap))
        half = bool((k and len(us) >= k / 2) or (days and elapsed >= days / 2))
    n = round(span_days, 1) if metric.kind == "rate" else len(us)
    events = (len({u.event for u in us})
              if metric.units in EVENT_METRICS else None)
    return {"value": value, "n": n, "ci": ci, "lo": lo, "hi": hi,
            "complete": complete, "half": half, "detail": detail,
            "events": events, "units": us}


def _needed(window, metric):
    days, k = parse_window(window, metric)
    if not k:
        return f"{days:g} days"
    return f"{k}" + (f" or {days:g} days" if days else "")


# ---------------------------------------------------------------- verdicts

def _eval(groups, main_value, secondary):
    """True when any and-group holds; a clause on a missing value is False."""
    def clause(metric, op, num):
        v = main_value if metric is None else secondary(metric)
        return v is not None and OPS[op](v, num)
    return any(all(clause(*c) for c in g) for g in groups)


def _double_down(groups, value, baseline, ci):
    """KEEP with the effect at least twice the bar, or the interval past it."""
    bars = [c for g in groups for c in g if c[0] is None]
    if not bars:
        return False
    _, op, threshold = bars[0]
    up = op in (">=", ">")
    if baseline is None:
        baseline = 0.0  # a null baseline: the metric's zero is "no effect"
    bar = threshold - baseline
    if bar != 0 and (bar > 0) == up:
        effect = value - baseline
        if (effect >= 2 * bar) if up else (effect <= 2 * bar):
            return True
    if ci:
        return ci[0] >= threshold if up else ci[1] <= threshold
    return False


def grade_one(root, row, asof):
    """Grade one open experiment row. Returns a dict with verdict and line."""
    if row.get("commit") is None:
        return {"id": row["id"], "verdict": "BLOCKED", "value": None, "n": 0,
                "line": f"{row['id']} BLOCKED by core: {row.get('blocked_by_core')}"}
    commit = row["commit"]
    anchor = commit_time(root, commit)
    metric, _ = parse_metric(row["metric"])
    m = measure(root, row["metric"], row["window"], anchor, asof, True,
                commit=commit)
    keep, back = parse_condition(row["keep_if"]), parse_condition(row["rollback_if"])
    sec_cache = {}

    def secondary(name):
        if name not in sec_cache:
            sec_cache[name] = measure(root, name, None, anchor, asof, True,
                                      commit=commit,
                                      span=(m["lo"], m["hi"]))["value"]
        return sec_cache[name]

    value, needed = m["value"], _needed(row["window"], metric)
    progress = f"n={m['n']}/{needed}"
    events = m.get("events")
    short = events is not None and events < EVENT_FLOOR
    if events is not None:
        progress += f" events={events}" + (f"/{EVENT_FLOOR}" if short else "")
    if value is None or short:
        verdict = "INCONCLUSIVE" if m["complete"] else "COLLECTING"
    else:
        rollback = _eval(back, value, secondary)
        if m["complete"]:
            if rollback:
                verdict = "ROLL BACK"
            elif _eval(keep, value, secondary):
                verdict = "DOUBLE DOWN" if _double_down(
                    keep, value, row["baseline"], m["ci"]) else "KEEP"
            else:
                verdict = "INCONCLUSIVE"
        elif m["half"] and rollback:
            verdict = "ROLL BACK"
        else:
            verdict = "COLLECTING"
    shown = "n/a" if value is None else f"{value:.4f}"
    base = "null" if row["baseline"] is None else row["baseline"]
    line = (f"{row['id']} {verdict} {progress} {row['metric']}={shown} "
            f"baseline={base} keep_if '{row['keep_if']}' "
            f"rollback_if '{row['rollback_if']}'"
            + (f" ({m['detail']})" if m["detail"] else ""))
    return {"id": row["id"], "verdict": verdict,
            "value": None if value is None else round(value, 4),
            "n": m["n"], "needed": needed, "events": events,
            "ci": None if not m["ci"] else [round(x, 4) for x in m["ci"]],
            "window_end": iso(m["hi"]) if m["complete"] else None,
            "line": line}


def propose(root, metric_name, window, commit, asof):
    sha = resolve_commit(root, commit)
    if sha is None:
        raise ValueError(f"commit {commit!r} does not resolve")
    metric, _ = parse_metric(metric_name)
    parse_window(window, metric)
    anchor = commit_time(root, sha)
    m = measure(root, metric_name, window, anchor, asof, False, commit=sha)
    if m["value"] is None and not _null_baseline_ok(metric_name):
        raise ValueError(f"no baseline: {metric_name} has no data in the "
                         f"window before {iso(anchor)} (only "
                         f"{', '.join(NULL_BASELINE_METRICS)} may open with "
                         f"a null baseline)")
    se = (_standard_error(m.get("units") or [])
          if metric.kind == "mean" or metric.units is u_rule else None)
    # A null baseline is judged against zero; a numeric one compares the
    # forward window with the baseline window, two samples of about one size.
    mde = None if se is None else MDE_Z * se * (1 if m["value"] is None
                                                 else math.sqrt(2))
    return {"commit": sha, "metric": metric_name, "window": window,
            "baseline": None if m["value"] is None else round(m["value"], 4),
            "baseline_asof": iso(asof), "baseline_n": m["n"],
            "baseline_events": m.get("events"),
            "mde": None if mde is None else round(mde, 4),
            "unit": metric.unit}


def power_note(out):
    """One line on what the proposed window can detect, from the same window
    before the commit."""
    parts = []
    events = out.get("baseline_events")
    if events is not None and events < EVENT_FLOOR:
        parts.append(f"the same window before the commit held {events} events, "
                     f"and grade gives no verdict below {EVENT_FLOOR}: widen it")
    if out.get("mde") is None:
        parts.append("no standard error from history for this metric; size the "
                     "window from the cell's rows (events) on core/edge_board.py")
    else:
        zero = out["baseline"] if out["baseline"] is not None else 0
        parts.append(f"smallest effect this window detects at 80% power: "
                     f"{out['mde']:g}; set keep_if at least that far from {zero:g}")
    return "; ".join(parts)


def _unit_value(u):
    """A unit's number for the standard error: its sample, or the paired
    rule-minus-raw Brier of a rule-tagged row."""
    s = u.sample
    if isinstance(s, bool):
        return None
    if isinstance(s, (int, float)):
        return float(s)
    if isinstance(s, dict) and "rule_prob" in s and "raw_prob" in s:
        y = _y(s)
        return (s["rule_prob"] - y) ** 2 - (s["raw_prob"] - y) ** 2
    return None


def _standard_error(units):
    """Standard error of the mean unit value, clustered by event when the units
    carry one (core/score.py paired_rule_test's estimator); None when fewer
    than two units or events."""
    vals = [(u.event, _unit_value(u)) for u in units]
    vals = [(e, v) for e, v in vals if v is not None]
    n = len(vals)
    if n < 2:
        return None
    mean = sum(v for _, v in vals) / n
    if vals[0][0] is None:
        return math.sqrt(sum((v - mean) ** 2 for _, v in vals) / (n - 1) / n)
    clusters = collections.defaultdict(lambda: [0.0, 0])
    for e, v in vals:
        clusters[e][0] += v
        clusters[e][1] += 1
    g = len(clusters)
    if g < 2:
        return None
    return math.sqrt(g / (g - 1) * sum((s - mean * k) ** 2
                                       for s, k in clusters.values())) / n


def _null_baseline_ok(metric_name):
    return str(metric_name).partition(":")[0] in NULL_BASELINE_METRICS


# ---------------------------------------------------------------- ledger

def load_ledger(root):
    path = pathlib.Path(root) / LEDGER_REL
    if not path.exists():
        return []
    rows = []
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            rows.append((lineno, line))
    return rows


def fold(root):
    """id -> {'open': row, 'verdicts': [...], 'close': row|None}. Assumes a
    valid ledger (check_ledger)."""
    out = {}
    for _, line in load_ledger(root):
        r = json.loads(line)
        if r["event"] == "open":
            out[r["id"]] = {"open": r, "verdicts": [], "close": None}
        elif r["id"] in out:
            if r["event"] == "verdict":
                out[r["id"]]["verdicts"].append(r)
            elif r["event"] == "close":
                out[r["id"]]["close"] = r
    return out


def _lever_path(lever):
    return lever.split("#", 1)[0]


def _risk_loosening(root, sha):
    """Fields of strategy/risk.json the commit loosens (empty if none)."""
    before = show_file(root, f"{sha}^", "strategy/risk.json")
    after = show_file(root, sha, "strategy/risk.json")
    if before is None or after is None or before == after:
        return []
    try:
        b, a = json.loads(before), json.loads(after)
    except json.JSONDecodeError:
        return ["risk.json does not parse"]
    out = []
    for field, old in b.items():
        if isinstance(old, bool) or not isinstance(old, (int, float)):
            continue
        new = a.get(field)
        if isinstance(new, bool) or not isinstance(new, (int, float)):
            out.append(f"{field} removed")
        elif field.startswith("min_") and new < old:
            out.append(f"{field} {old} -> {new}")
        elif (field.startswith("max_") or "stake" in field) and new > old:
            out.append(f"{field} {old} -> {new}")
    return out


def check_ledger(root=ROOT, recompute=True):
    """Integrity errors in strategy/experiments.jsonl (empty when sane)."""
    errors = []
    rows = load_ledger(root)
    if not rows:
        return errors
    head_ok = resolve_commit(root, "HEAD") is not None
    # Baselines are re-checked while an experiment is live; a closed one's
    # data may since have been rotated out of the journals.
    closed_ids = set()
    for _, line in rows:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict) and r.get("event") == "close":
            closed_ids.add(r.get("id"))
    state = {}           # id -> 'open' | 'blocked' | 'closed'
    opens = {}           # id -> open row
    closes = {}          # id -> close row
    for lineno, line in rows:
        def err(msg, lineno=lineno):
            errors.append(f"{LEDGER_REL}:{lineno}: {msg}")
        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            err(f"invalid JSON - {e}")
            continue
        if not isinstance(r, dict):
            err("not a JSON object")
            continue
        event, rid = r.get("event"), r.get("id")
        if event not in ("open", "verdict", "close"):
            err(f"unknown event {event!r}")
            continue
        if not isinstance(rid, str) or not rid:
            err("id missing")
            continue
        try:
            ts = parse_ts(r["ts"])
        except (KeyError, TypeError, ValueError):
            err(f"ts missing or not a timestamp: {r.get('ts')!r}")
            continue

        if event == "open":
            if rid in state:
                err(f"{rid} opened twice")
                continue
            if not isinstance(r.get("hypothesis"), str) or not r["hypothesis"].strip():
                err(f"{rid}: hypothesis missing")
            levers = r.get("lever")
            if not (isinstance(levers, list) and levers
                    and all(isinstance(x, str) and x for x in levers)):
                err(f"{rid}: lever must be a non-empty list of paths")
                levers = []
            if r.get("commit") is None:
                if not isinstance(r.get("blocked_by_core"), str) or \
                        not r["blocked_by_core"].strip():
                    err(f"{rid}: no commit and no blocked_by_core - an open row "
                        f"is an experiment (with its commit) or a blocked lever")
                state[rid], opens[rid] = "blocked", r
                continue
            ok = _check_experiment_open(root, r, rid, levers, ts, head_ok,
                                        recompute and rid not in closed_ids,
                                        err, state, opens, closes)
            state[rid], opens[rid] = "open", r
            if not ok:
                continue
            n_open = sum(1 for s in state.values() if s == "open")
            if n_open > MAX_OPEN:
                err(f"{rid}: {n_open} experiments open, the cap is {MAX_OPEN}")
        elif event == "verdict":
            if state.get(rid) not in ("open", "blocked"):
                err(f"verdict for {rid}, which is not open")
                continue
            if r.get("verdict") not in VERDICTS:
                err(f"{rid}: verdict {r.get('verdict')!r} not one of {VERDICTS}")
        else:
            if state.get(rid) not in ("open", "blocked"):
                err(f"close for {rid}, which is not open")
                continue
            if r.get("outcome") not in OUTCOMES:
                err(f"{rid}: outcome {r.get('outcome')!r} not one of {OUTCOMES}")
            if not isinstance(r.get("lesson"), str) or not r["lesson"].strip():
                err(f"{rid}: close row needs a one-line lesson")
            state[rid], closes[rid] = "closed", r
    return errors


def _check_experiment_open(root, r, rid, levers, ts, head_ok, recompute, err,
                           state, opens, closes):
    """Checks for an experiment's open row; False if it cannot be graded."""
    ok = True
    for lever in levers:
        path = _lever_path(lever)
        if not path.startswith("strategy/") or path == LEDGER_REL:
            err(f"{rid}: lever {lever!r} is not an agent-owned strategy/ file "
                f"(a protected lever is a blocked_by_core row)")
    for lever in levers:
        for oid, s in state.items():
            if s == "open" and lever in opens[oid].get("lever", []):
                err(f"{rid}: lever {lever!r} is already held by open "
                    f"experiment {oid}")
    prior = r.get("prior")
    if not isinstance(prior, list):
        err(f"{rid}: prior must be a list (cite failed ids, or [])")
        prior = []
    for oid, close in closes.items():
        if close.get("outcome") != "rolled_back":
            continue
        try:
            age = ts - parse_ts(close["ts"])
        except (KeyError, TypeError, ValueError):
            continue
        shared = set(levers) & set(opens[oid].get("lever", []))
        if shared and age <= dt.timedelta(days=FAILED_LEVER_DAYS) and oid not in prior:
            err(f"{rid}: lever {sorted(shared)[0]!r} was rolled back in {oid} "
                f"within {FAILED_LEVER_DAYS} days; cite {oid} in prior")
    try:
        metric, _ = parse_metric(r.get("metric") or "")
        parse_window(r.get("window"), metric)
        parse_condition(r.get("keep_if"))
        parse_condition(r.get("rollback_if"))
    except ValueError as e:
        err(f"{rid}: {e}")
        return False
    baseline = r.get("baseline")
    if baseline is None and "baseline" in r:
        if not _null_baseline_ok(r["metric"]):
            err(f"{rid}: baseline null is allowed only for "
                f"{', '.join(NULL_BASELINE_METRICS)}; {r['metric']} needs the "
                f"number propose prints")
            ok = False
    elif isinstance(baseline, bool) or not isinstance(baseline, (int, float)):
        err(f"{rid}: baseline missing or not a number")
        ok = False
    try:
        asof = parse_ts(r["baseline_asof"])
    except (KeyError, TypeError, ValueError):
        err(f"{rid}: baseline_asof missing (copy it from propose)")
        return False
    if not head_ok:
        err(f"{rid}: no git history to check commit {r.get('commit')!r} "
            f"against (a shallow clone? fetch full history)")
        return False
    sha = resolve_commit(root, str(r.get("commit")))
    if sha is None:
        err(f"{rid}: commit {r.get('commit')!r} does not resolve")
        return False
    if not is_ancestor(root, sha):
        err(f"{rid}: commit {sha[:12]} is not an ancestor of HEAD")
        return False
    files = commit_files(root, sha)
    bad = [f for f in files if not f.startswith("strategy/") or f == LEDGER_REL]
    if bad:
        err(f"{rid}: commit {sha[:12]} touches {bad}: an experiment commit "
            f"changes only strategy/ files, never the ledger itself")
    if len(files) > MAX_FILES_PER_COMMIT:
        err(f"{rid}: commit {sha[:12]} touches {len(files)} files, the cap is "
            f"{MAX_FILES_PER_COMMIT}")
    loosened = _risk_loosening(root, sha)
    if loosened:
        err(f"{rid}: commit {sha[:12]} loosens strategy/risk.json "
            f"({', '.join(loosened)}); loosening is an operator act")
    if recompute and ok:
        try:
            m = measure(root, r["metric"], r["window"], commit_time(root, sha),
                        asof, False, commit=sha)
        except Exception as e:  # noqa: BLE001 - report, never crash validate
            err(f"{rid}: baseline could not be recomputed: {e}")
            return False
        if baseline is None:
            if m["value"] is not None:
                err(f"{rid}: baseline null, but propose computes "
                    f"{round(m['value'], 4)} for the window before the commit; "
                    f"copy it from core/experiments.py propose")
        elif m["value"] is None or \
                abs(m["value"] - baseline) > BASELINE_TOLERANCE * max(1.0, abs(baseline)):
            err(f"{rid}: baseline {baseline} is not what propose computes "
                f"({None if m['value'] is None else round(m['value'], 4)}); "
                f"copy it from core/experiments.py propose")
    return ok


# ---------------------------------------------------------------- scoreboard

def _tight(r):
    return round(r["best_ask_at_record"] - r["best_bid_at_record"], 4) <= TIGHT_SPREAD


def _skill(rows):
    """Mean dBrier against the price, with a 95% interval clustered by event
    (core/edge_board.py cluster_ratio; no interval under 10 events)."""
    import edge_board  # deferred: only the scoreboard needs the board's maths
    c = edge_board.cluster_ratio([(_event(r), _dbrier(r), 1.0) for r in rows])
    return {"value": c["est"], "lo": c["lo"], "hi": c["hi"], "n": len(rows),
            "events": c["events"]}


def scoreboard(root, asof, since=None):
    """The primary metric, its target, and the guard metrics a change must not
    worsen, as known at asof. since: also the primary over rows settled after
    that time (the last deep retro)."""
    import edge_board
    j = Journal(root, asof)
    # Superseded rows count, as in core/score.py rule_verdicts: each was the
    # estimate at its own record price, and dropping it would let a revision
    # made on later news remove a bad early read from the score.
    scored = [r for r in j.forecasts() if r["_settled"] and not score.placeholder_book(r)]
    window = [r for r in scored if r["_sts"] > asof - PRIMARY_DAYS * DAY]
    primary = _skill([r for r in window if _tight(r)])
    primary["met"] = primary["hi"] is not None and primary["hi"] < 0
    out = {"asof": iso(asof), "days": PRIMARY_DAYS, "primary": primary}
    if since is not None:
        out["since"] = dict(_skill([r for r in scored if _tight(r)
                                    and r["_sts"] > since]), start=iso(since))
    recorded = [r["_ts"] for r in j.forecasts()]
    # validate and grade report a broken ledger; here it only blanks the count.
    ledger_ok = not check_ledger(root, recompute=False)
    folded = fold(root) if ledger_ok else {}
    trials = edge_board.read_trials(pathlib.Path(root) / edge_board.TRIALS_REL)
    out["guards"] = {
        "forecast_rows_per_day": {
            "last_7d": round(sum(t > asof - 7 * DAY for t in recorded) / 7, 1),
            "prior_7d": round(sum(asof - 14 * DAY < t <= asof - 7 * DAY
                                  for t in recorded) / 7, 1)},
        "all_books": _skill(window),
        "open_experiments": sum(1 for e in folded.values()
                                if e["close"] is None and e["open"].get("commit"))
        if ledger_ok else None,
        "open_cap": MAX_OPEN,
        "reserved_checks": {"used": edge_board.reserved_checks_used(trials, asof),
                            "limit": edge_board.RESERVED_CHECKS_PER_WEEK}}
    return out


def _fmt_skill(s):
    if s["value"] is None:
        return f"n/a n={s['n']}"
    ci = "" if s["lo"] is None else f" [{s['lo']:+.4f}, {s['hi']:+.4f}]"
    return f"{s['value']:+.4f}{ci} n={s['n']} events={s['events']}"


def render_scoreboard(sb):
    p, g = sb["primary"], sb["guards"]
    print(f"scoreboard as of {sb['asof']}")
    print(f"primary: tight-book dBrier against the price (spread <= "
          f"{TIGHT_SPREAD}, no placeholder books, superseded rows count), rows "
          f"settled in the last {sb['days']} days; target: the 95% interval below 0")
    print(f"  {_fmt_skill(p)}  "
          + ("MET" if p["met"] else
             "MISSED" + (f" (upper end {p['hi']:+.4f})" if p["hi"] is not None else "")))
    if "since" in sb:
        print(f"  since {sb['since']['start']}: {_fmt_skill(sb['since'])}")
    rows = g["forecast_rows_per_day"]
    print("guards (a change must not make these worse)")
    print(f"  forecast rows per day: {rows['last_7d']} in the last 7 days, "
          f"{rows['prior_7d']} in the 7 days before")
    print(f"  all-books dBrier, last {sb['days']} days: {_fmt_skill(g['all_books'])}")
    print(f"  open experiments: {g['open_experiments']} of {g['open_cap']}"
          if g["open_experiments"] is not None else
          "  open experiments: ledger errors, run core/experiments.py grade")
    rc = g["reserved_checks"]
    print(f"  reserved checks this week: {rc['used']} of {rc['limit']} new variant "
          f"versions (core/edge_board.py)")


# ---------------------------------------------------------------- CLI

def status(root, lever=None):
    folded = fold(root)
    out = []
    for rid, e in folded.items():
        o = e["open"]
        if lever and not any(_lever_path(x) == _lever_path(lever) or x == lever
                             for x in o.get("lever", [])):
            continue
        if e["close"]:
            st = f"closed:{e['close']['outcome']}"
        elif o.get("commit") is None:
            st = "blocked"
        else:
            st = "open"
        out.append({"id": rid, "state": st, "lever": o.get("lever"),
                    "metric": o.get("metric"), "window": o.get("window"),
                    "baseline": o.get("baseline"), "keep_if": o.get("keep_if"),
                    "rollback_if": o.get("rollback_if"),
                    "commit": o.get("commit"),
                    "blocked_by_core": o.get("blocked_by_core"),
                    "hypothesis": o.get("hypothesis"),
                    "last_verdict": e["verdicts"][-1]["verdict"] if e["verdicts"] else None,
                    "lesson": e["close"]["lesson"] if e["close"] else None})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("propose", help="compute the baseline for an open row")
    p.add_argument("--metric", required=True)
    p.add_argument("--window", required=True, help="days=D, n=K, or both")
    p.add_argument("--commit", required=True,
                   help="the experiment's pushed change commit")
    p.add_argument("--asof", help="knowledge cutoff (default: now)")
    g = sub.add_parser("grade", help="verdict for every open row")
    g.add_argument("--json", action="store_true")
    g.add_argument("--asof", help="grade as of this UTC time (default: now)")
    s = sub.add_parser("status", help="the folded ledger")
    s.add_argument("--lever", help="only rows naming this lever path")
    s.add_argument("--json", action="store_true")
    b = sub.add_parser("scoreboard",
                       help="the primary metric, its target, and the guard metrics")
    b.add_argument("--since", help="also the primary since this time: an ISO "
                                   "timestamp, a date, or 7d / 36h")
    b.add_argument("--json", action="store_true")
    b.add_argument("--asof", help="as of this UTC time (default: now)")
    a = ap.parse_args(argv)
    asof = parse_ts(a.asof) if getattr(a, "asof", None) else now_utc()

    if a.cmd == "propose":
        try:
            out = propose(ROOT, a.metric, parse_window_spec(a.window), a.commit,
                          asof)
        except ValueError as e:
            sys.exit(f"propose: {e}")
        print(json.dumps(out))
        what = ("no data before the commit: baseline null, so keep_if and "
                "rollback_if are absolute" if out["baseline"] is None else
                f"baseline over {out['baseline_n']} x {out['unit']} before the "
                f"commit")
        print(f"# {what}; copy commit, metric, window, baseline and "
              f"baseline_asof into the open row as printed", file=sys.stderr)
        print(f"# {power_note(out)}", file=sys.stderr)
        return 0

    if a.cmd == "scoreboard":
        since = parse_ts(score.since_cutoff(a.since, asof)) if a.since else None
        sb = scoreboard(ROOT, asof, since)
        if a.json:
            print(json.dumps(sb, indent=1))
        else:
            render_scoreboard(sb)
        return 0

    errors = check_ledger(ROOT, recompute=False)
    if errors:
        print("ledger errors (core/validate.py fails on these):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    if a.cmd == "status":
        rows = status(ROOT, a.lever)
        if a.json:
            print(json.dumps(rows, indent=1))
            return 0
        n_open = sum(1 for r in rows if r["state"] == "open")
        print(f"experiments: {len(rows)} rows, {n_open} open (cap {MAX_OPEN})")
        for r in rows:
            extra = (f" blocked_by_core: {r['blocked_by_core']}" if r["state"] == "blocked"
                     else f" {r['metric']} window={json.dumps(r['window'])}"
                          f" last={r['last_verdict'] or '-'}")
            print(f"  {r['id']} {r['state']} lever={','.join(r['lever'] or [])}{extra}")
            if r["lesson"]:
                print(f"      lesson: {r['lesson']}")
        return 0

    graded = [grade_one(ROOT, e["open"], asof)
              for e in fold(ROOT).values() if e["close"] is None]
    if a.json:
        print(json.dumps({"asof": iso(asof), "experiments": graded}, indent=1))
    elif not graded:
        print("no open experiments")
    else:
        for g_ in graded:
            print(g_["line"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
