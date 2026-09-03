#!/usr/bin/env python3
"""Offline evaluator for the screening tier: did the screen beat the mids?

PROTECTED CORE - the trading agent must not edit files under core/.

journal/screener.jsonl is a frozen record of what the screening subagents
believed: one row per (market, screening run) with the Haiku probabilities,
the market mids at screen time, the divergence the pipeline ranked on, the
confidence and the prompt_rev (the git blob hash of the exact
strategy/screener-prompt.md text that produced it). Nothing in that record
says whether the read was any good. This tool supplies the missing half -
the realized outcome - and scores the screen against the price it was
handed, so a prompt edit can be argued from resolutions instead of taste.

Four subcommands, in the order you use them:

  events    Fill journal/screener-events.jsonl, the market -> event map:
            gamma sells one event as many markets, and the interval every
            other number here carries is only honest if those markets are
            counted as one observation. Pages gamma's /events list endpoint
            over the end-date spans that still hold an unmapped market, so
            the work shrinks as coverage fills; --limit bounds a run. Until
            it has run, every market clusters alone, which is what every
            report did before this cache existed. See cluster_of.

  outcomes  Fill journal/screener-outcomes.jsonl, the resolution cache: one
            row per market (market_id, checked_ts, status, winner,
            end_date). Append-only, later rows supersede earlier ones for
            the same market. Resumable: a market is fetched only if it has
            never been cached, or is cached "open" and is now past its end
            date. resolved/void are terminal. Fetches are sequential with a
            sleep between them and pmapi's own retries; --limit bounds a run.

  score     Join screener rows to resolved outcomes and report, per
            prompt_rev / per confidence / per divergence bucket: n, the
            mean Brier of the Haiku probabilities, the mean Brier of the
            recorded mids, and the delta. Negative delta = the screen beat
            the market at screen time, which is the only claim a prompt
            edit can honestly make. Every delta carries a 95% interval and
            a z, because a delta without one is a coin flip with a decimal
            point - and a `null` and an `excess`, because most of a delta
            is the price of disagreeing rather than the cost of being
            wrong.

  prepare   Rebuild a fixed sample of already-resolved, already-screened
            markets as screening batches, so a modified prompt can be
            re-run over the same markets and scored against the same
            answers. The mids are the RECORDED ones and the outcome
            resolutions are held back in answers.json. It also prints what
            the chosen --size can actually resolve; see size_note.
            --like DIR rebuilds an existing run's sample exactly, briefs and
            all, which is how the control arm is built.

  score --replay DIR [--control DIR]
            Close that loop: grade the out files of a re-screened prepared
            run against the answers it held back, PAIRED against what the
            recorded prompt said about the same markets from the same mids.
            --control is a second re-screen of the same sample under the old
            prompt, screened the same day, which is what makes the difference
            between the arms a difference between two prompts. See paired and
            control_block.

Brier here is the multi-outcome form, sum over outcomes of (p - 1[o wins])^2.
For a binary market (every market screened so far) that is twice the
familiar (p - y)^2. The model and the mids are scored with the same
definition, so the delta is unaffected by the convention.

A positive delta is not by itself evidence that the screen read a market
wrong. Per outcome the delta decomposes exactly into

    (p - m)^2  +  2 (p - m)(m - y)

- a term that never sees the outcome, paid for disagreeing at all, plus a
term whose mean is zero if the mids are calibrated. So the first term gets
its own column, `null`, and beside it `excess` = delta - null, the only
part of the loss that depends on which way the screen was wrong. On this
journal most of the delta is null, and the by-divergence table especially
so: its null is 2 * divergence^2 by construction, which is most of the rise
from +0.0003 in the lowest bucket to +0.33 in the highest. See delta_null.

Escalation quality answers a different question than calibration. The
pipeline does not act on probabilities, it acts on a RANKING: each batch of
20 hands its top 15 by divergence to a researcher. So within each batch we
rank the markets by divergence and, separately, by the realized surprise
the market itself got (|1[winner] - mid_winner| = 1 - mid_winner), and
report precision at 15 of the first ranking against the second. Alongside
it is the hypergeometric baseline k*k/n, the precision a coin-flip ranking
would score: with 20 resolved markets in a batch and k = 15 the baseline is
0.75, so only the lift over baseline is evidence of anything. That null has
a closed-form variance too, but it assumes batches are independent and they
are not, so the lift's z uses the larger of that variance and an
event-clustered one.

Precision at 15 alone is too blunt to settle the question. It moves in
steps of 1/15, ignores the order inside the top 15, and treats a market the
price missed by 0.02 the same as one it missed by 0.9 - so "no measurable
skill" from it could equally mean "no measurable test". Beside it the
report gives surprise_lift: the mean realized surprise of the 15 escalated
markets minus the mean over the whole batch, which is the same ranking read
in the units the researcher is actually spending time on.

Both readings beat a coin-flip ranking, and neither beats the mids. An even
market is more surprising than a 0.99 one however it resolves, and it also
leaves the screen more room to disagree, so ANY ranking correlated with
price uncertainty escalates surprising markets without reading anything. So
the report prices that null in too: surprise_lift_mids is the lift the same
ranking earns if every market resolves exactly as its own mid implied, and
the excess over it is the only part the screen can claim. See escalation.

"Did the screen beat the mids?" is the wrong question to stop on, because
the answer is no on every revision and that single word covers two opposite
situations. A screen that reads nothing and a screen that reads something
real but shouts it both lose to the price; only the second one is fixable
by editing a prompt, and the fix is about volume, not content. So the
report also fits the blend q = w*mid + (1-w)*screen and reports w_opt, the
market weight that fits the resolutions best: 1.00 says the screen adds
nothing on top of the price, below 1 says it adds something. The in-sample
Brier at w_opt is <= 0 against the mids for ANY data at all, so the honest
figure beside it is the held-out one, cross-validated with the folds cut by
market. See blend_slice.

Uncertainty is not decoration here. The deltas this tool reports are small
- hundredths of a Brier point - and the intervals around them are wide
enough to swallow most of the differences between prompt revisions, so the
report is mostly useful for ruling edits OUT. The interval is clustered:
the same market is screened again every cycle it survives in the universe,
and all those rows are graded against one outcome, so they are one
observation and not thirty-six. See delta_se.

Two markets can be one observation too, and on this journal most of them
share an event. Polymarket sells one EVENT as many markets - "highest
temperature in Munich will be X" bands of which exactly one can win, every
exact score of one football match, a ladder of "Bitcoin above $X"
thresholds that a single price settles - and one reading settles all of
them at once. So the cluster is the event, not the market, and `events`
fills the map that makes that possible. The `evts` column beside `mkts` is
what the intervals are actually taken over. See cluster_of.

Measured, it barely touches the Brier tables and it visibly deflates the
escalation one, which is worth knowing separately. 7,948 scored markets
fall into 3,105 events, 2.5 markets each and up to 15. In every delta,
excess and blend row above, no z moves by more than 0.2 and none changes
sign or significance - the markets of one event disagree with their price
in different enough directions that the pooling gains little. The
escalation table is the exception, and for a structural reason: it ranks
WITHIN a batch of 20, and a batch routinely holds several markets of one
event, which carry near-identical divergence and near-identical surprise
and therefore move as a block. f055b035's precision lift goes from z +4.6
to +3.6 and its surprise lift from +3.0 to +2.4 - still real, a quarter
weaker than the market-clustered reading said. Read any escalation z from
before this cache existed as that much too confident.

So the cache earns its place twice: it is the only honest reading of the
escalation ranking, and it turns the Brier tables' independence assumption
from an assumption into a checked fact that is re-checked every run as
coverage grows. Do not read the small Brier-side movement as licence to
drop it - that is a finding about this journal, not about clustering.

Comparing two prompts is not the same problem as scoring one. Every table
above measures one screen against the price, where the answer is always
"worse" and mostly for reasons - the null - that no edit can move. A prompt
edit is a difference between two screens, and the only honest way to read a
difference is to take it on the same markets, against the same outcomes,
from the same mids, one market at a time. That is what `prepare` sets up and
`score --replay` reads: d_excess, the paired directional residual, whose
mean is zero under calibrated mids for ANY pair of prompts, so unlike a
single arm's delta it can be read straight off with no apology attached. A
negative d_excess is the one claim this whole tool exists to let a prompt
edit make.

Pairing a re-screen against the JOURNAL does not isolate the prompt, and
saying otherwise would be the same mistake as reading a delta with no null.
The journal arm ran days or weeks ago under whatever "subagent:haiku"
resolved to then - the journal records the alias, not a version - and its
subagent was told a different date. The brief still carries the market's
end_date, so once a market has closed the re-screen is asked who won where
the live screen was asked who will win. So the honest comparison re-screens
the SAME prepared sample twice on the same day, once under each prompt
text: `prepare --like` builds the second run and `score --replay NEW
--control OLD` reads it. The three readings decompose exactly, per market,

    naive (new - journal) = prompt (new - control) + drift (control - journal)

so the control arm does not only give a cleaner number, it measures how much
of the old one was ever about the prompt. See control_block.

For that to be a comparison at all, the two arms have to be shown to have
read two different texts, and the live subagent prompt sends every arm to
one mutable file. Editing it between the two re-screens does not get there:
an arm fans out as many parallel subagents, so a late starter in the first
arm reads the second arm's text, and nothing afterwards records what any
subagent read. So `prepare` copies the brief into the run directory,
records the copy's blob hash in the manifest, and points that run's own
subagent prompt at the copy; `score --replay` re-hashes it and reports
which text each arm read. Two arms pinned to the SAME text is not a mistake
but a useful run: it is an A/A, and its paired reading is the subagents'
own run-to-run noise - the floor a claimed edit has to clear, and the
honest number to size the next A/B with. See prompt_bytes and excess_sd.

Leakage. A tuning run scores --before <its own start time>: every market it
can see already resolved, so no edit it makes can reach the markets scored
by the morning's --after <that same time>. That seal is structural, not a
promise. --since-rev SHA is the stricter test - it keeps only the live
screener's own reads under that prompt text (prompt_rev == SHA and ts after
the commit that introduced it), because re-screening old markets with a new
prompt measures the prompt on markets the prompt was written while looking
at.

Usage:
  python3 core/screen_replay.py outcomes [--limit N] [--sleep S]
  python3 core/screen_replay.py events [--limit N] [--sleep S] [--window H]
  python3 core/screen_replay.py score [--before TS] [--after TS]
                                      [--since-rev SHA] [--json]
  python3 core/screen_replay.py score --replay work/screen-replay/<new>
                                      [--control work/screen-replay/<old>]
                                      [--json]
  python3 core/screen_replay.py prepare --after TS --before TS
                                        [--seed S] [--size N] [--batch-size N]
                                        [--prompt PATH | --prompt-rev SHA]
  python3 core/screen_replay.py prepare --like work/screen-replay/<run>
                                        [--prompt PATH | --prompt-rev SHA]
"""
import argparse
import collections
import datetime as dt
import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402
import resolve  # noqa: E402
import screen  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCREENER = ROOT / "journal" / "screener.jsonl"
OUTCOMES = ROOT / "journal" / "screener-outcomes.jsonl"
EVENTS = ROOT / "journal" / "screener-events.jsonl"
PROMPT_FILE = ROOT / "strategy" / "screener-prompt.md"
REPLAY_ROOT = ROOT / "work" / "screen-replay"
STATIC_CACHE = REPLAY_ROOT / "gamma-static.jsonl"

FETCH_SLEEP_S = 0.4
# gamma's /events list endpoint. One page carries every market of every
# event it returns, so one request maps up to a few hundred markets to their
# event - orders of magnitude cheaper than a per-market fetch, which cannot
# answer the question at all (/markets/<id> carries no event field).
EVENTS_URL = f"{pmapi.GAMMA}/events"
GAMMA_PAGE = 100
# gamma refuses offset+limit past this, so a span holding more events than
# it can page has to be halved rather than paged further.
GAMMA_MAX_OFFSET = 2000
EVENT_WINDOW_H = 6
# The divergence bands the report groups on. Half-open [lo, hi).
DIVERGENCE_BUCKETS = (("0-0.05", 0.0, 0.05), ("0.05-0.10", 0.05, 0.10),
                      ("0.10-0.20", 0.10, 0.20), ("0.20+", 0.20, 2.0))
CONFIDENCE_ORDER = ("high", "medium", "low", "unknown")
# screen.py hands the top_n of each batch to a researcher; that is the cut
# the escalation ranking is judged at.
ESCALATION_K = 15
# A market outcome name can never be this, so settle_against_market grades the
# probe row as "lost" and fills outcome_won with the actual winner.
NO_OUTCOME = "\x00not-an-outcome\x00"
# The blend read: q = w*mid + (1-w)*screen. Grid mirrors core/score.py's
# blend_sweep so the two tiers are read the same way; folds are cut by market.
BLEND_GRID = (0.5, 0.6, 0.7, 0.8, 0.9)
BLEND_FOLDS = 5
# Rows where the screen echoed the price cannot move a decision either way.
DISAGREEMENT_MIN = 0.05
# Below this many distinct markets the blend is not fitted at all. Both the
# clustered sandwich SE and the ratio estimator's delta method need clusters
# to work with, and a fit on a handful of events extrapolates the blend line
# far outside [0, 1] - a three-market slice returns w_opt 11.2 at z +5.0,
# which is a straight line through noise wearing an interval. A tuning run
# scores a narrow --before window and the morning scores its --after
# complement, so thin slices are the normal case here, not the exception.
BLEND_MIN_EVENTS = 30

# Below this many same-mids cross-revision re-screens the journal cannot size
# a replay sample, and `prepare` says so instead of printing a number.
PAIRED_SD_MIN_MARKETS = 30

# The paired excess a re-screen should be able to resolve. Set at the scale
# of the gaps `score` already reports between prompt revisions (their excess
# column spans -0.0007 to +0.0033), because a sample that cannot see a
# difference that size cannot rank the revisions it is being run to rank.
PAIRED_EXCESS_TARGET = 0.005

# Each prepared run keeps its own immutable copy of the judgment brief here,
# and its subagents are sent to that copy rather than to the live
# strategy/screener-prompt.md. See prompt_bytes.
ARM_PROMPT_FILE = "prompt.md"


def _parse_ts(s):
    """ISO-8601 timestamp -> aware UTC datetime. Gamma end dates may carry
    fractional seconds or an offset instead of Z."""
    text = str(s).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    ts = dt.datetime.fromisoformat(text)
    return ts.replace(tzinfo=dt.timezone.utc) if ts.tzinfo is None \
        else ts.astimezone(dt.timezone.utc)


def parse_arg_ts(value, flag):
    """A --before/--after argument, normalised to the journal's Z format."""
    if value is None:
        return None
    try:
        return screen.iso(_parse_ts(value))
    except ValueError:
        sys.exit(f"{flag} expects a UTC timestamp like 2026-09-03T00:14:36Z, "
                 f"got {value!r}")


def load_screener_rows():
    if not SCREENER.is_file():
        sys.exit(f"no screener log at {SCREENER.relative_to(ROOT)}")
    return resolve.load_jsonl(SCREENER)


def load_outcome_cache():
    """market_id -> latest cached outcome row (the file is append-only).

    end_date is normalised to the journal's second-precision Z form, because
    gamma serves both that and a fractional-second variant and the window
    filters compare the two against each other.
    """
    cache = {}
    for r in resolve.load_jsonl(OUTCOMES):
        mid = r.get("market_id")
        if mid is None:
            continue
        try:
            r["end_date"] = screen.iso(_parse_ts(r.get("end_date")))
        except (AttributeError, TypeError, ValueError):
            r["end_date"] = None
        cache[str(mid)] = r
    return cache


def load_event_cache():
    """(market_id -> event_id, the set of end-date spans already swept).

    Two row kinds share one append-only file: a mapping row carries
    market_id and event_id, a bookkeeping row carries `window` and says
    that span has been paged to exhaustion, so a re-run skips it instead of
    paying for it twice. A market with no mapping row is not an error - it
    falls back to clustering alone, which is exactly what every report did
    before this cache existed.
    """
    ids, swept = {}, set()
    for r in resolve.load_jsonl(EVENTS):
        if r.get("window"):
            swept.add(str(r["window"]))
        mid, ev = r.get("market_id"), r.get("event_id")
        if mid is not None and ev:
            ids[str(mid)] = str(ev)
    return ids, swept


def cluster_of(market_id, events):
    """The key every interval in this report is clustered on.

    A market_id is the wrong unit. Polymarket sells one EVENT as many
    markets: "highest temperature in Munich will be X" bands of which
    exactly one can win, every exact score of one football match, a ladder
    of "Bitcoin above $X" thresholds that a single price settles. One
    reading settles all of them, so they are one observation and not
    fifteen, in the same way a market's 36 re-screens are one and not
    thirty-six. See cluster_se.

    Prefixed because an event id and a market id are both numeric strings
    out of the same namespace and must never collide.

    A word on what NOT to cluster on. The obvious cheap substitute is
    question text - "Tampa Bay Rays spread" is recognisably a family
    without asking gamma anything - and it is not conservative, it is
    wrong. That key merges 13 different games on 13 different days, and a
    catch-all like "Any other" merges 54 markets with nothing in common;
    measured on this journal it inflated one revision's excess interval by
    1.6x, and splitting exactly the cross-event merges back out returned
    the z to its event-clustered value to two decimals. A grouping that is
    only approximately the dependence structure invents dependence as
    readily as it captures it.
    """
    ev = events.get(market_id)
    return ("e:" + ev) if ev else ("m:" + market_id)


# ---------------------------------------------------------------- outcomes


def classify(market, now):
    """(status, winner, end_date) for a gamma record.

    Delegates the actual grading to resolve.settle_against_market so the
    cache can never disagree with how the ledger settles: a decisive
    outcomePrice (>=0.99) resolves, a market closed without one goes void
    after the same grace period, anything else stays open.
    """
    end_date = market.get("endDate")
    probe = {"outcome": NO_OUTCOME, "status": "open", "end_date": end_date or ""}
    try:
        settled = resolve.settle_against_market(probe, market, now)
    except (AttributeError, TypeError, ValueError):
        # Unparseable end date or malformed outcomes: not resolvable today.
        return "open", None, end_date
    if not settled:
        return "open", None, end_date
    if probe["status"] == "void":
        return "void", None, end_date
    return "resolved", probe.get("outcome_won"), end_date


def needs_check(cached, now):
    """Re-fetch only what could have changed: never-seen and stale-open rows."""
    if cached is None:
        return True
    if cached.get("status") != "open":
        return False  # resolved and void are terminal
    try:
        return _parse_ts(cached.get("end_date")) <= now
    except (AttributeError, TypeError, ValueError):
        return True  # no usable end date: we cannot tell, so ask again


def fetch_order(rows):
    """Every distinct market: whole batches at a time, oldest batch first
    within each prompt_rev, the revisions interleaved round-robin.

    Two things a bounded run must not do. Straight chronological order spends
    the whole budget inside the oldest revision, and a report that can only
    see one revision cannot compare revisions. Spreading the budget market by
    market is worse still: it leaves every batch a fifth resolved, and the
    escalation metric needs a batch's ranking whole, not a sample of it. So
    the unit here is the batch, and the lanes are the revisions.
    """
    members, batch_ts = collections.defaultdict(list), {}
    for r in rows:
        key = (r.get("prompt_rev") or "", str(r.get("batch_id")))
        ts = r.get("ts") or ""
        members[key].append(str(r.get("market_id")))
        if batch_ts.get(key, "9") > ts:
            batch_ts[key] = ts
    lanes, lane_ts = collections.defaultdict(list), {}
    for key in sorted(members, key=lambda k: (batch_ts[k], k)):
        lanes[key[0]].append(key)
        lane_ts.setdefault(key[0], batch_ts[key])
    revs = sorted(lanes, key=lambda rev: lane_ts[rev])
    order, seen = [], set()
    for i in range(max((len(v) for v in lanes.values()), default=0)):
        for rev in revs:
            if i >= len(lanes[rev]):
                continue
            # every member, not only the ones first seen here: a market an
            # older batch already claimed still has to be present for THIS
            # batch's ranking to be gradeable.
            for mid in members[lanes[rev][i]]:
                if mid not in seen:
                    seen.add(mid)
                    order.append(mid)
    return order


def cmd_outcomes(args):
    rows = load_screener_rows()
    order = fetch_order(rows)
    cache = load_outcome_cache()
    now = screen.utcnow()
    todo = [m for m in order if needs_check(cache.get(m), now)]
    pending = len(todo)
    if args.limit is not None:
        todo = todo[:max(0, args.limit)]

    counts, failed = collections.Counter(), 0
    OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOMES.open("a") as fh:
        for i, mid in enumerate(todo):
            if i:
                time.sleep(args.sleep)
            try:
                market = pmapi.gamma_market(mid)
            except RuntimeError as e:
                print(f"screen_replay: fetch failed for {mid}: {e}", file=sys.stderr)
                failed += 1
                continue
            status, winner, end_date = classify(market, screen.utcnow())
            fh.write(json.dumps({
                "market_id": mid, "checked_ts": screen.iso(screen.utcnow()),
                "status": status, "winner": winner, "end_date": end_date,
            }) + "\n")
            fh.flush()  # a killed run keeps every market it already paid for
            counts[status] += 1

    after = load_outcome_cache()
    terminal = sum(1 for m in order
                   if after.get(m, {}).get("status") in ("resolved", "void"))
    print(f"outcomes: {len(order)} distinct markets in the screener log; "
          f"{pending} needed a check, {len(todo)} checked this run "
          f"({failed} fetch failures)")
    print(f"  this run: resolved {counts['resolved']}, open {counts['open']}, "
          f"void {counts['void']}")
    print(f"  cache now: {len(after)} markets, "
          f"{sum(1 for r in after.values() if r.get('status') == 'resolved')} resolved, "
          f"{sum(1 for r in after.values() if r.get('status') == 'void')} void, "
          f"{len(order) - terminal} not yet terminal")
    return 0


# ------------------------------------------------------------------- events


def window_start(ts, hours):
    """`ts` floored to the start of its `hours`-long span of the UTC day."""
    day = ts.replace(hour=0, minute=0, second=0, microsecond=0)
    n = int((ts - day).total_seconds() // (hours * 3600))
    return day + dt.timedelta(hours=hours * n)


def window_key(lo, hours):
    return f"{screen.iso(lo)}/{hours}h"


def record_events(events, state):
    """Write a mapping row for every TARGET market in `events`."""
    for e in events:
        ev_id = e.get("id")
        if ev_id is None:
            continue
        # a split span re-pages what it already returned, so count the event
        # once rather than once per page it appeared on
        state["seen_events"].add(str(ev_id))
        for m in (e.get("markets") or []):
            mid = str(m.get("id"))
            if mid not in state["targets"] or mid in state["seen"]:
                continue
            state["seen"].add(mid)
            state["fh"].write(json.dumps({
                "market_id": mid, "event_id": str(ev_id),
                "event_slug": e.get("slug"),
                "checked_ts": screen.iso(screen.utcnow()),
            }) + "\n")
            state["fh"].flush()  # a killed run keeps what it already paid for
            state["written"] += 1


def sweep_span(lo, hi, sleep, state):
    """Page every gamma event ending in [lo, hi) and record its markets.

    True if the span was paged to exhaustion, so the caller may mark it
    swept. False if the request budget ran out or a fetch failed - the span
    is then left unmarked and a later run sweeps it again. Whatever it did
    map before stopping is already written, so the repeat is cheap in
    coverage even when it is not cheap in requests.

    Splitting rather than paging on is forced by gamma: offsets past
    GAMMA_MAX_OFFSET are refused outright, so a span holding more events
    than that can only be read by halving it. Whatever the span did return
    before the ceiling is still recorded - an extra mapping is never wrong,
    only a missing one is.
    """
    events, offset = [], 0
    while True:
        if state["left"] is not None and state["left"] <= 0:
            record_events(events, state)
            return False
        if offset > GAMMA_MAX_OFFSET:
            record_events(events, state)
            # truncated to the second the request will actually carry:
            # a mid that formats back to lo would recurse forever on a
            # one-second span
            mid = (lo + (hi - lo) / 2).replace(microsecond=0)
            if not lo < mid < hi:
                print(f"screen_replay: span {screen.iso(lo)} is one second "
                      f"deep and still over gamma's offset ceiling; it may be "
                      f"incompletely mapped", file=sys.stderr)
                return True
            return (sweep_span(lo, mid, sleep, state)
                    and sweep_span(mid, hi, sleep, state))
        if state["requests"]:
            time.sleep(sleep)
        state["requests"] += 1
        if state["left"] is not None:
            state["left"] -= 1
        try:
            page = pmapi.get_json(EVENTS_URL, {
                "end_date_min": screen.iso(lo), "end_date_max": screen.iso(hi),
                "limit": GAMMA_PAGE, "offset": offset})
        except RuntimeError as e:
            print(f"screen_replay: events fetch failed at "
                  f"{screen.iso(lo)}+{offset}: {e}", file=sys.stderr)
            state["failed"] += 1
            record_events(events, state)
            return False
        if not page:
            break
        events.extend(page)
        offset += len(page)
        if len(page) < GAMMA_PAGE:
            break
    record_events(events, state)
    return True


def cmd_events(args):
    """Fill journal/screener-events.jsonl: which event each screened market
    belongs to, which is the unit every interval in `score` clusters on.

    The spans to sweep come from the markets still unmapped and the end
    dates the resolution cache already holds, so the work shrinks to nothing
    as coverage fills and a market whose outcome has never been fetched is
    reported rather than silently skipped. Run `outcomes` first.
    """
    rows = load_screener_rows()
    targets = {str(r.get("market_id")) for r in rows
               if r.get("market_id") is not None}
    outcomes = load_outcome_cache()
    mapped, swept = load_event_cache()
    hours = args.window
    if hours < 1:
        sys.exit("--window is a whole number of hours, at least 1")

    spans, unplaceable = {}, 0
    for mid in sorted(targets - set(mapped)):
        end = (outcomes.get(mid) or {}).get("end_date")
        try:
            ts = _parse_ts(end)
        except (AttributeError, TypeError, ValueError):
            unplaceable += 1
            continue
        lo = window_start(ts, hours)
        spans.setdefault(window_key(lo, hours),
                         (lo, lo + dt.timedelta(hours=hours)))
    pending = [k for k in sorted(spans) if args.resweep or k not in swept]

    state = {"left": args.limit, "requests": 0, "failed": 0,
             "seen_events": set(), "written": 0, "targets": targets,
             "seen": set(), "fh": None}
    done = 0
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a") as fh:
        state["fh"] = fh
        for key in pending:
            if state["left"] is not None and state["left"] <= 0:
                break
            lo, hi = spans[key]
            if sweep_span(lo, hi, args.sleep, state):
                done += 1
                fh.write(json.dumps({
                    "window": key, "swept_ts": screen.iso(screen.utcnow()),
                }) + "\n")
                fh.flush()

    after, _ = load_event_cache()
    covered = len(targets & set(after))
    print(f"events: {len(targets)} distinct markets in the screener log; "
          f"{len(spans)} end-date spans hold an unmapped one, {len(pending)} "
          f"not yet swept, {done} swept this run")
    print(f"  this run: {state['requests']} requests "
          f"({state['failed']} failures), {len(state['seen_events'])} "
          f"events seen, "
          f"{state['written']} mappings written")
    print(f"  cache now: {covered} of {len(targets)} markets mapped to "
          f"{len(set(after.values()))} events; {len(targets) - covered} "
          f"unmapped (they cluster alone)")
    if unplaceable:
        print(f"  {unplaceable} unmapped markets have no cached end date and "
              f"cannot be placed in a span - run `outcomes` first")
    return 0


# ------------------------------------------------------------------- score


def rev_time(sha):
    """When the prompt text `sha` first existed, as a Z timestamp, or None.

    prompt_rev is a git BLOB hash (screen.blob_rev hashes the bytes actually
    read, so an uncommitted edit is still identified). So resolve it as a
    commit first for the case where an operator passes one, then fall back
    to the commit that introduced that blob into the prompt file.
    """
    attempts = (["git", "-C", str(ROOT), "show", "-s", "--format=%cI",
                 f"{sha}^{{commit}}"],
                ["git", "-C", str(ROOT), "log", "--format=%cI",
                 f"--find-object={sha}", "--", str(PROMPT_FILE)])
    for cmd in attempts:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=15, check=True).stdout
        except Exception:  # noqa: BLE001 - provenance is best-effort
            continue
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        if lines:
            return screen.iso(_parse_ts(lines[-1]))  # oldest = first appearance
    return None


def mid_null_surprise(mids):
    """E[1 - mid_winner] when the winner is drawn from the mids themselves.

    The free-lunch component of any escalation ranking. For a binary market
    priced p it is 2p(1-p): 0.5 at an even market, 0.02 at 0.99. Divergence
    correlates with an even price - a 0.99 market leaves the screen little
    room to disagree - so a ranking that does nothing but prefer uncertain
    markets still escalates more-surprising markets than average, without
    the screen having read anything. Subtracting this is what separates
    "the ranking beats a coin flip" from "the ranking beats the mids".
    """
    total = sum(float(v) for v in mids.values())
    if total <= 0:
        return 0.0
    return 1.0 - sum(float(v) ** 2 for v in mids.values()) / total


def brier(dist, winner):
    """Multi-outcome Brier: sum over outcomes of (p - 1[o wins])^2."""
    return sum((p - (1.0 if o == winner else 0.0)) ** 2 for o, p in dist.items())


def delta_null(triples):
    """The Brier delta a screen that reads NOTHING still pays: sum (p - m)^2.

    Everywhere else this report treats a positive delta as "the screen lost
    to the price". By default that reading is wrong. Write one outcome's
    delta out in full:

        (p - y)^2 - (m - y)^2 = (p - m)^2 + 2 (p - m)(m - y)

    The first term never sees the outcome. It is the toll for disagreeing
    with the price at all, and it is charged whether the disagreement was
    right or wrong. The second term is the only part that knows how the
    market resolved, and it has mean zero whenever the mids are calibrated
    (E[y] = m). So a screen that picks probabilities out of a hat still
    scores a positive delta, and one that disagrees twice as loudly scores
    four times as much of it.

    For a binary market this is 2 * divergence^2, which is the same
    quantity the by-divergence table groups on - so that table's monotone
    rise is guaranteed before a single market resolves and cannot be read
    without subtracting this first. summarize() reports the toll as `null`
    and `excess` = delta - null beside it: the directional residual, what is
    left once the screen is charged only for the volume of its disagreement.

    The null assumes the market is calibrated and this market is not quite.
    Over the resolved log it carries a favourite-longshot bias: outcomes
    priced in [0.90, 0.95) win 0.940 of the time and those priced in
    [0.05, 0.10) win 0.059. Recentring every excess on that empirical
    calibration curve instead of on the raw mids moves the overall figure
    from +0.0009 to +0.0007 and no revision's by more than 0.0004, changing
    no sign and no significance - so the raw mids null is the one reported
    and the bias is this paragraph rather than a column.

    It is the same quantity as the blend's denominator, which is why
    select() stores it once: w_opt = 1 + excess / (2 * null) exactly, so
    `excess` and `w_opt` are one reading in two units. See blend_slice.
    """
    return sum((m - p) ** 2 for p, m, y in triples)


def delta_excess(item):
    """One scored row's Brier delta, minus the part delta_null explains."""
    return (item["brier_model"] - item["brier_mids"]) - item["delta_null"]


def bucket_of(divergence):
    for name, lo, hi in DIVERGENCE_BUCKETS:
        if lo <= divergence < hi:
            return name
    return DIVERGENCE_BUCKETS[-1][0]


def scored_item(market_id, ts, prompt_rev, batch_id, confidence, divergence,
                probs, mids, winner, end_date, cluster=None):
    """One gradeable (screen, mids, outcome) triple in the shape every
    statistic in this module reads.

    Built in one place because there are two ways in. `select` walks the
    journal; `replay_rows` walks the out files of a re-screened sample. A
    replay row that reached this function has been through screen.py's own
    parse_answers and grade_answer, so the two sources differ only in which
    prompt text produced the probabilities - which is the entire point of
    the comparison and would be worth nothing if the two arms were scored
    by two slightly different pieces of arithmetic.
    """
    if divergence is None:
        divergence = max(abs(probs[o] - mids[o]) for o in probs)
    # (screen, mid, outcome) per outcome, plus the two sums the
    # closed-form blend weight is a ratio of. See w_opt_of. Ordered by
    # outcome name, not by whatever order the subagent happened to write
    # its probabilities in: every statistic here sums over the triples and
    # does not care, but paired_excess_sd keys on them and does.
    triples = [(float(probs[o]), float(mids[o]),
                1.0 if o == winner else 0.0) for o in sorted(probs)]
    return {
        "market_id": market_id, "ts": ts,
        # the unit every interval is clustered on: the market's event when
        # the events cache knows it, the market itself otherwise
        "cluster": cluster or ("m:" + market_id),
        "prompt_rev": prompt_rev, "batch_id": batch_id,
        "confidence": confidence,
        "divergence": float(divergence),
        "brier_model": brier(probs, winner),
        "brier_mids": brier(mids, winner),
        # what the market itself got wrong: 1 - the mid it gave the winner
        "surprise": abs(1.0 - float(mids[winner])),
        # ...and what that would have been on average had the mid been
        # perfectly calibrated: E[1 - mid_winner] over winners drawn from
        # the mids themselves. Peaks at an even market, so a ranking that
        # merely prefers uncertain markets scores surprise for free.
        "surprise_mid_null": mid_null_surprise(mids),
        "blend": triples,
        "blend_a": sum((m - p) * (y - p) for p, m, y in triples),
        # doubles as the blend's denominator and as the mids-null
        # expected Brier delta - they are the same sum. See delta_null.
        "delta_null": delta_null(triples),
        "end_date": end_date,
    }


def select(rows, cache, before, after, since_rev, events=None):
    """(scored rows, filtered counts, skipped counts).

    filtered = out of scope for this report. skipped = in scope but not
    gradeable, which is the number a prompt edit should watch.
    """
    filtered, skipped = collections.Counter(), collections.Counter()
    events = events or {}
    rev_sha, rev_ts = since_rev if since_rev else (None, None)
    scored = []
    for r in rows:
        rev = r.get("prompt_rev") or ""
        if rev_sha:
            if not rev.startswith(rev_sha):
                filtered["other_prompt_rev"] += 1
                continue
            if rev_ts and (r.get("ts") or "") <= rev_ts:
                filtered["screened_before_rev"] += 1
                continue
        out = cache.get(str(r.get("market_id")))
        if out is None:
            filtered["outcome_not_cached"] += 1
            continue
        end_date = out.get("end_date") or ""
        if before and not (end_date and end_date < before):
            filtered["after_window"] += 1
            continue
        if after and not (end_date and end_date >= after):
            filtered["before_window"] += 1
            continue
        if out.get("status") != "resolved":
            skipped[out.get("status") or "unknown_status"] += 1
            continue
        if r.get("screen_error"):
            skipped["screen_error"] += 1
            continue
        probs, mids = r.get("probs"), r.get("mids")
        if not isinstance(probs, dict) or not probs:
            skipped["missing_probs"] += 1
            continue
        if not isinstance(mids, dict) or not mids:
            skipped["missing_mids"] += 1
            continue
        winner = out.get("winner")
        if set(probs) != set(mids) or winner not in mids:
            skipped["outcome_mismatch"] += 1
            continue
        scored.append(scored_item(
            market_id=str(r.get("market_id")), ts=r.get("ts"), prompt_rev=rev,
            batch_id=r.get("batch_id"),
            confidence=r.get("confidence") or "unknown",
            divergence=r.get("divergence"), probs=probs, mids=mids,
            winner=winner, end_date=end_date,
            cluster=cluster_of(str(r.get("market_id")), events)))
    return scored, filtered, skipped


def rounded(x, places=4):
    """round(), minus negative zero - "-0.0000" reads as a negative result."""
    r = round(x, places)
    return 0.0 if r == 0 else r


def cluster_se(contribs):
    """Standard error of a statistic written as a sum of small contributions,
    clustered by a key that repeats across them.

    Nothing this module measures is independent. A market is re-screened
    every cycle it stays in the universe - up to 36 times under one
    prompt_rev - and every one of those repeats is graded against the same
    single realized outcome. Treating them as separate observations would
    shrink the interval by roughly the square root of the repeat count and
    promote noise to a finding, which is the exact failure this tool exists
    to prevent.

    So: the sandwich estimator. Total the contributions within each cluster
    first, then take the spread of the cluster totals, with the usual
    c/(c-1) small-cluster inflation. One contribution per cluster reduces it
    to the ordinary standard error of that sum.

    `contribs` is an iterable of (cluster_key, value) whose values sum to
    the statistic itself.
    """
    totals = collections.defaultdict(float)
    for key, value in contribs:
        totals[key] += value
    c = len(totals)
    if c < 2:
        return None
    mean_total = sum(totals.values()) / c
    var = sum((t - mean_total) ** 2 for t in totals.values()) * (c / (c - 1))
    return var ** 0.5 if var > 0 else None


def mean_se(items, value):
    """Cluster-robust standard error of the mean of `value` over rows.

    The mean is a sum of (value - mean)/n contributions, one per row, so it
    drops straight into cluster_se keyed on the row's cluster. Both the
    Brier delta and its mids-null excess are means of this shape and share
    the estimator rather than each growing their own.
    """
    n = len(items)
    if n < 2:
        return None
    mean = sum(value(s) for s in items) / n
    return cluster_se((s["cluster"], (value(s) - mean) / n) for s in items)


def delta_se(items):
    """Standard error of the mean Brier delta, clustered by event."""
    return mean_se(items, lambda s: s["brier_model"] - s["brier_mids"])


EMPTY_SUMMARY = {"n": 0, "markets": 0, "clusters": 0, "brier_model": None,
                 "brier_mids": None, "delta": None, "delta_se": None,
                 "delta_ci95": None, "z": None, "null": None,
                 "excess": None, "excess_se": None, "excess_ci95": None,
                 "excess_z": None}


def summarize(items):
    n = len(items)
    if not n:
        return dict(EMPTY_SUMMARY)
    bm = sum(s["brier_model"] for s in items) / n
    bk = sum(s["brier_mids"] for s in items) / n
    null = sum(s["delta_null"] for s in items) / n
    excess = (bm - bk) - null
    se = delta_se(items)
    ese = mean_se(items, delta_excess)
    return {"n": n, "markets": len({s["market_id"] for s in items}),
            "clusters": len({s["cluster"] for s in items}),
            "brier_model": round(bm, 4), "brier_mids": round(bk, 4),
            "delta": rounded(bm - bk),
            "delta_se": None if se is None else round(se, 4),
            "delta_ci95": None if se is None else round(1.96 * se, 4),
            "z": None if not se else rounded((bm - bk) / se, 2),
            "null": round(null, 4),
            "excess": rounded(excess),
            "excess_se": None if ese is None else round(ese, 4),
            "excess_ci95": None if ese is None else round(1.96 * ese, 4),
            "excess_z": None if not ese else rounded(excess / ese, 2)}


def clustering_note(items):
    """What the intervals in this report were clustered on, and how well.

    Coverage is a fact about the run, not a constant: journal/
    screener-events.jsonl is filled incrementally by `events`, and a market
    it has not reached yet clusters alone. That is the pre-cache behaviour
    and it is anti-conservative, so the number of markets still on their own
    belongs beside every interval rather than in a comment.
    """
    markets = {s["market_id"]: s["cluster"] for s in items}
    grouped = sum(1 for c in markets.values() if c.startswith("e:"))
    return {"markets": len(markets), "clusters": len(set(markets.values())),
            "in_events": grouped, "alone": len(markets) - grouped,
            "largest": max(collections.Counter(markets.values()).values(),
                           default=0)}


def group(items, key, order=None):
    """key -> summary, in `order` if given, else by descending n."""
    buckets = collections.defaultdict(list)
    for s in items:
        buckets[key(s)].append(s)
    names = list(order) if order else sorted(buckets, key=lambda k: -len(buckets[k]))
    if order:
        names += [k for k in sorted(buckets) if k not in names]
    return [dict(summarize(buckets[k]), key=k) for k in names if buckets[k]]


def top_k_weights(values, k):
    """P(each value is in the top k of `values`), ties broken uniformly.

    Divergence is rounded to four places by screen.py and is coarse in
    practice: two values, 0.005 and 0.0, cover most of the log, and in 84%
    of batches the k/k+1 cut falls strictly inside a tie group. So "the top
    k by divergence" is mostly decided by whatever the sort does with ties,
    which carries no information about anything - screen.py's live sort is
    stable and keeps universe order, this module used to break ties by
    market_id, and neither is a fact about the screen.

    Breaking ties by market_id is not merely arbitrary, it is biased: a
    random ranking scored with that tiebreak lands 0.012 BELOW the k*k/n
    baseline the report subtracts, which is twice the size of any lift this
    report has ever printed. Averaging over tiebreaks instead is exact,
    deterministic and cheap: everything strictly above the cut has weight 1,
    everything strictly below has 0, and the tie group straddling the cut
    splits its remaining slots evenly. The overlap and the lift are both
    linear in these weights, so the expectation over random tiebreaks is
    just the statistic evaluated at them.
    """
    order = sorted(values, reverse=True)
    cut = order[k - 1]
    above = sum(1 for v in order if v > cut)
    tied = sum(1 for v in order if v == cut)
    frac = (k - above) / tied
    return [1.0 if v > cut else (frac if v == cut else 0.0) for v in values]


def escalation(items, k=ESCALATION_K):
    """Per prompt_rev: does ranking a batch by divergence escalate the
    markets the market itself got wrong?

    Two readings of the same ranking, because the pipeline does not act on
    probabilities, it acts on an order: each batch hands its top k by
    divergence to a researcher.

    Both rankings are taken with ties averaged over rather than broken - see
    top_k_weights, which is the difference between a null the report can
    subtract and one that is off by twice the effect size.

    `precision_at_k` is the expected overlap between the top k by divergence
    and the top k by realized surprise. It has no mids null beside it: an
    overlap of two rankings is not linear in the surprises, so pricing the
    mids in would take a simulation rather than an expectation, and a report
    should not roll dice. Read surprise_lift_excess for that question - on
    this journal the simulated version of the count null lands on the same
    answer, 0.0182 of the 0.0189 lift f055b035 scores. Overlap of two independent k-subsets
    of n is hypergeometric, so the null has the closed-form mean k*k/n and a
    matching variance; with 20 gradeable markets and k = 15 that baseline is
    0.75, so only the lift over it is evidence of anything. It is still a
    blunt instrument - it throws away the order inside the top k and the
    size of every surprise, and it counts a market the price missed by 0.02
    the same as one it missed by 0.9.

    That hypergeometric variance is exact per batch but assumes batches are
    independent, and they are not: consecutive cycles re-screen the same
    markets against the same eventual outcomes. So the count lift is
    clustered by market_id the same way the delta is - write the batch
    overlap as a sum of per-market pieces, P(in top surprise) * (P(in top
    divergence) - k/n), which sums to exactly hits - k*k/n - and the z takes
    whichever standard error is larger. Reporting the hypergeometric one
    alone overstates the count lift by roughly a factor of two here, which
    is enough to print a significant edge where there is none.

    `surprise_lift` keeps both. It is the mean realized surprise of the k
    markets the pipeline would have escalated minus the mean over the whole
    batch: the extra wrongness escalation actually buys, in the units the
    researcher cares about. Beside it, `surprise_lift_mids` is that same
    lift computed against mid_null_surprise instead of the realized outcome
    - the lift the ranking would have earned if every market resolved
    exactly as its own price implied - and `surprise_lift_excess` is what is
    left for the screen. A ranking can score a large lift and no excess,
    which is what this journal does. Under a random top k the expected lift is
    exactly zero and the variance is the finite-population one,
    (S^2/k)*((n-k)/(n-1)) per batch - which is the variance of a hard top k,
    so it is conservative for the tie-averaged one. That SE is exact given
    independent batches, which these are not, so it is reported beside an
    event-clustered SE and the z takes whichever is larger - the same
    treatment precision_at_k gets above.

    Clustering by event is not cosmetic for THIS statistic the way it is for
    the Brier tables. The ranking is taken within a batch of 20, and a batch
    routinely holds several markets of one event, which carry near-identical
    divergence and near-identical surprise and so enter or leave the top k
    as a block. On this journal that inflation is real: f055b035's precision
    lift reads z +4.6 clustered by market and +3.6 clustered by event.

    A batch with k or fewer gradeable markets is degenerate: every market is
    escalated, so precision is 1.0 and the lift is 0 by construction.
    Excluded and counted.
    """
    by_batch = collections.defaultdict(list)
    for s in items:
        by_batch[(s["prompt_rev"], s["batch_id"])].append(s)
    agg = collections.defaultdict(
        lambda: {"batches": 0, "hits": 0.0, "k_total": 0, "baseline_hits": 0.0,
                 "baseline_var": 0.0, "degenerate_batches": 0,
                 "surprise_top": 0.0, "surprise_all": 0.0, "perm_var": 0.0,
                 "mid_null_lift": 0.0,
                 "contribs": [], "prec_contribs": []})
    for (rev, _batch), rows in sorted(by_batch.items(), key=lambda kv: str(kv[0])):
        a = agg[rev]
        if len(rows) <= k:
            a["degenerate_batches"] += 1
            continue
        n = len(rows)
        p_div = top_k_weights([s["divergence"] for s in rows], k)
        p_sur = top_k_weights([s["surprise"] for s in rows], k)
        a["batches"] += 1
        a["hits"] += sum(d * u for d, u in zip(p_div, p_sur))
        a["k_total"] += k
        a["baseline_hits"] += k * k / n
        a["baseline_var"] += k * (k / n) * ((n - k) / n) * ((n - k) / (n - 1))
        # Same ranking, read as a mean instead of a count. The batch lift is
        # sum_i w_i * surprise_i with w_i = 1[escalated]/k - 1/n, which is
        # mean(top k) - mean(batch) and is zero in expectation under a
        # random top k. Keeping the per-market pieces lets the same sum be
        # re-clustered by market at the end.
        mean_all = sum(s["surprise"] for s in rows) / n
        mean_top = sum(d * s["surprise"] for d, s in zip(p_div, rows)) / k
        a["surprise_top"] += mean_top
        a["surprise_all"] += mean_all
        spread = sum((s["surprise"] - mean_all) ** 2 for s in rows) / (n - 1)
        a["perm_var"] += spread / k * ((n - k) / (n - 1))
        for s, escalated, surprising in zip(rows, p_div, p_sur):
            w = escalated / k - 1.0 / n
            a["contribs"].append((s["cluster"], w * s["surprise"]))
            # Same weights against the calibrated-mids expectation. The lift
            # is linear in the surprises, so this is the exact expected lift
            # under that null - no simulation needed.
            a["mid_null_lift"] += w * s["surprise_mid_null"]
            # The count reading of the same ranking, split the same way:
            # over the batch these sum to hits - k*k/n, so clustering them
            # by market gives the overlap lift a non-independent null too.
            a["prec_contribs"].append(
                (s["cluster"], surprising * (escalated - k / n)))
    out = []
    for rev, a in sorted(agg.items(), key=lambda kv: -kv[1]["k_total"]):
        b = a["batches"]
        prec = a["hits"] / a["k_total"] if a["k_total"] else None
        base = a["baseline_hits"] / a["k_total"] if a["k_total"] else None
        kt = a["k_total"]
        hyper_se = prec_clustered_se = prec_se = None
        lift = perm_se = clustered_se = surprise_se = None
        mid_lift = excess = None
        if kt:
            hyper_se = a["baseline_var"] ** 0.5 / kt
            prec_clustered_se = cluster_se((m, v / kt) for m, v in a["prec_contribs"])
            prec_se = max((x for x in (hyper_se, prec_clustered_se) if x),
                          default=None)
        if b:
            lift = sum(v for _, v in a["contribs"]) / b
            mid_lift = a["mid_null_lift"] / b
            excess = lift - mid_lift
            perm_se = a["perm_var"] ** 0.5 / b
            clustered_se = cluster_se((m, v / b) for m, v in a["contribs"])
            # both can be zero when a batch's surprises are all equal
            surprise_se = max((x for x in (perm_se, clustered_se) if x),
                              default=None)
        out.append({"key": rev, "batches": b,
                    "degenerate_batches": a["degenerate_batches"],
                    "precision_at_k": None if prec is None else round(prec, 4),
                    "baseline": None if base is None else round(base, 4),
                    "lift": None if prec is None else rounded(prec - base),
                    "lift_se": None if not prec_se else round(prec_se, 4),
                    "lift_hyper_se": None if not hyper_se else round(hyper_se, 4),
                    "lift_clustered_se": (None if not prec_clustered_se
                                          else round(prec_clustered_se, 4)),
                    "z": None if not prec_se else rounded((prec - base) / prec_se, 2),
                    "surprise_top": None if not b else round(a["surprise_top"] / b, 4),
                    "surprise_all": None if not b else round(a["surprise_all"] / b, 4),
                    "surprise_lift": None if lift is None else rounded(lift),
                    "surprise_lift_se": None if not surprise_se else round(surprise_se, 4),
                    "surprise_perm_se": None if not perm_se else round(perm_se, 4),
                    "surprise_clustered_se": (None if not clustered_se
                                              else round(clustered_se, 4)),
                    "surprise_z": (None if not surprise_se
                                   else rounded(lift / surprise_se, 2)),
                    "surprise_lift_mids": None if mid_lift is None else rounded(mid_lift),
                    "surprise_lift_excess": None if excess is None else rounded(excess),
                    "surprise_excess_z": (None if not surprise_se
                                          else rounded(excess / surprise_se, 2))})
    return out


def blend_brier(item, w):
    """Mean Brier of the blend w*mid + (1-w)*screen for one scored row."""
    return sum((p + w * (m - p) - y) ** 2 for p, m, y in item["blend"])


def w_opt_of(items):
    """The least-squares optimal market weight, in closed form, or None.

    Brier(w) = sum over rows and outcomes of (w*(m-p) - (y-p))^2, a quadratic
    in one variable, so the minimiser is sum (m-p)(y-p) / sum (m-p)^2 - the
    per-row numerators and denominators are accumulated in select(). For a
    binary market both sums double, so this is exactly core/score.py's
    binary blend_sweep formula generalised to a distribution.

    Not clamped to [0, 1]. w_opt above 1 means the fit wants to lever AWAY
    from the screen - the screen is not merely uninformative there, it is
    anti-informative - and clamping would hide the only reading that
    distinguishes the two.
    """
    den = sum(s["delta_null"] for s in items)
    if den <= 0:
        return None  # the screen never disagreed with the mids
    return sum(s["blend_a"] for s in items) / den


def fold_of(cluster):
    """Deterministic fold for out-of-sample blending, assigned per CLUSTER.

    Per cluster and not per row: a market is re-screened every cycle it
    survives and every one of those rows is graded against one outcome, so
    splitting by row would put the same answer on both sides of the split
    and the held-out Brier would not be held out at all. Per cluster and
    not per market for the same reason one step up - the 27 temperature
    bands of one day in one city are settled by one reading, so a market
    split leaks the answer across the fold boundary too. See cluster_of.
    """
    # keyed on the id, not the "e:"/"m:" prefix cluster_of adds: which fold
    # a cluster lands in is arbitrary, so dropping the prefix costs nothing
    # and keeps an unmapped market in the fold it had before this cache
    # existed - which is what makes the change provably additive.
    return int(screen.sample_key("blend-fold", cluster.split(":", 1)[-1]),
               16) % BLEND_FOLDS


def blend_slice(items):
    """One blend row: is there information in the screen at the margin?

    The rest of this report asks whether the screen BEATS the mids, and the
    answer everywhere is no. That leaves two very different situations
    indistinguishable. The screen may be reading nothing, in which case no
    prompt edit short of a rewrite will help; or it may be reading something
    real and expressing it far too loudly, in which case the edit that pays
    is about humility and the content is already fine. w_opt separates them:
    it is the weight the market gets in the blend that fits the outcomes
    best, so w_opt = 1 means the screen adds nothing on top of the price and
    w_opt below 1 means it does, however badly it is scaled on its own.

    Two numbers are reported for it and only one of them is evidence.

    `delta_in_sample` (brier_at_w_opt - brier_mids) is <= 0 ALWAYS, for any
    data whatsoever, because w = 1 is on the blend line and reproduces the
    mids exactly - so the fit can never do worse than the thing it is being
    compared against. Quoting it as a win would be quoting the fitting
    procedure. It is kept only because its size next to the honest number is
    a direct read of how much this report's own optimism is worth.

    It is also redundant with w_opt rather than being a second reading of
    it: the algebra collapses to delta_in_sample = -(w_opt - 1)^2 * sum(b)/n
    exactly, verified to 1e-12 on every slice of the real journal. A larger
    in-sample "gain" means only that the fitted weight sat further from 1,
    which is the column beside it.

    `delta_oos` is the honest one: BLEND_FOLDS-fold cross-validation with
    the folds cut by market, so the weight scoring a row was fitted without
    ever seeing that market's outcome.

    Its null is NOT zero, and assuming it was is the mistake this paragraph
    exists to prevent. Fitting a weight to noise costs you out of sample as
    surely as it flatters you in sample: for a held-out fold,
    E[brier(w_f) - brier(mids)] = (w_f - 1)^2 * B >= 0, so under a screen
    with no information delta_oos is slightly POSITIVE - simulated at
    +0.00025 against an in-sample -0.00021 on this journal's geometry, a
    ratio of 1.2 against the K/(K-1) = 1.25 the algebra predicts. Only a
    clearly negative delta_oos is evidence of anything.

    Below BLEND_MIN_EVENTS distinct events nothing is fitted and the row
    reports its counts and a note instead. The blend line is an
    extrapolation, not a policy: w is unconstrained, and on a thin slice the
    least-squares fit happily lands at w = 11, where q = 11*mid - 10*screen
    is not a distribution at all. Printing that with an interval beside it
    would be worse than printing nothing.

    The interval on w_opt is the clustered one. w_opt is a ratio of two
    sums, so its influence contributions are (a_i - w*b_i)/sum(b), which sum
    to exactly zero by construction and get totalled per market before the
    spread is taken - the same sandwich the Brier delta uses. `z` is against
    1.0, not against 0: the null here is "the market weight is everything",
    not "the market weight is nothing".
    """
    n = len(items)
    if not n:
        return {"n": 0, "markets": 0, "clusters": 0}
    bk = sum(s["brier_mids"] for s in items) / n
    out = {"n": n, "markets": len({s["market_id"] for s in items}),
           "clusters": len({s["cluster"] for s in items}),
           "brier_model": round(sum(s["brier_model"] for s in items) / n, 4),
           "brier_mids": round(bk, 4),
           "by_weight": [{"w_market": w,
                          "brier": round(sum(blend_brier(s, w) for s in items) / n, 4),
                          "delta_vs_mids": rounded(
                              sum(blend_brier(s, w) for s in items) / n - bk)}
                         for w in BLEND_GRID],
           "w_opt": None, "w_opt_se": None, "w_opt_ci95": None, "z": None,
           "brier_at_w_opt": None, "delta_in_sample": None,
           "delta_oos": None, "delta_oos_se": None, "delta_oos_z": None,
           "note": None}
    if out["clusters"] < BLEND_MIN_EVENTS:
        out["note"] = f"under {BLEND_MIN_EVENTS} events, not fitted"
        return out
    w = w_opt_of(items)
    if w is None:
        out["note"] = "the screen never disagreed with the mids"
        return out
    den = sum(s["delta_null"] for s in items)
    se = cluster_se((s["cluster"], (s["blend_a"] - w * s["delta_null"]) / den)
                    for s in items)
    bo = sum(blend_brier(s, w) for s in items) / n
    out.update({"w_opt": round(w, 3),
                "w_opt_se": None if not se else round(se, 3),
                "w_opt_ci95": None if not se else round(1.96 * se, 3),
                "z": None if not se else rounded((w - 1.0) / se, 2),
                "brier_at_w_opt": round(bo, 4),
                "delta_in_sample": rounded(bo - bk)})

    by_fold = collections.defaultdict(list)
    for s in items:
        by_fold[fold_of(s["cluster"])].append(s)
    if len(by_fold) < 2:
        out["note"] = "every market landed in one fold, nothing to hold out"
        return out
    held = []
    for f, rows_ in by_fold.items():
        w_f = w_opt_of([s for s in items if fold_of(s["cluster"]) != f])
        if w_f is None:
            out["note"] = "a fold had no disagreement to fit on"
            return out
        held += [(s, blend_brier(s, w_f) - s["brier_mids"]) for s in rows_]
    mean = sum(d for _, d in held) / n
    oos_se = cluster_se((s["cluster"], (d - mean) / n) for s, d in held)
    out.update({"delta_oos": rounded(mean),
                "delta_oos_se": None if not oos_se else round(oos_se, 4),
                "delta_oos_z": None if not oos_se else rounded(mean / oos_se, 2)})
    return out


def blend_report(items, revs):
    """The blend read, overall, per prompt_rev and on the disagreement slice.

    The disagreement slice (divergence >= DISAGREEMENT_MIN) is the one that
    can move a decision. Rows where the screen simply echoed the price have
    (m - p) near zero, so they carry almost no weight in the fit and almost
    no information about w - but they do drag every fixed-weight grid delta
    toward zero, which makes a blend look harmless when it is not. Same
    split core/score.py's blend_sweep uses on the research tier.
    """
    return {"grid": list(BLEND_GRID), "folds": BLEND_FOLDS,
            "disagreement_min": DISAGREEMENT_MIN,
            "overall": blend_slice(items),
            "disagreement": blend_slice(
                [s for s in items if s["divergence"] >= DISAGREEMENT_MIN]),
            "by_prompt_rev": [dict(blend_slice(g), key=rev) for rev, g in
                              ((r, [s for s in items if s["prompt_rev"] == r])
                               for r in revs) if g]}


def rev_first_ts(items):
    first = {}
    for s in items:
        rev = s["prompt_rev"]
        if rev not in first or (s["ts"] or "") < first[rev]:
            first[rev] = s["ts"] or ""
    return first


def build_report(rows, cache, args, events=None):
    since_rev = None
    if args.since_rev:
        ts = rev_time(args.since_rev)
        if ts is None:
            print(f"screen_replay: could not date prompt_rev {args.since_rev} in "
                  f"this repo; filtering on the revision only", file=sys.stderr)
        since_rev = (args.since_rev, ts)
    before = parse_arg_ts(args.before, "--before")
    after = parse_arg_ts(args.after, "--after")
    scored, filtered, skipped = select(rows, cache, before, after, since_rev,
                                       events)
    first_ts = rev_first_ts(scored)
    revs = sorted(first_ts, key=lambda r: first_ts[r])
    return {
        "screener_rows": len(rows),
        "markets_in_log": len({str(r.get("market_id")) for r in rows}),
        "outcomes_cached": len(cache),
        "clustering": clustering_note(scored),
        "window": {"before": before, "after": after,
                   "since_rev": args.since_rev,
                   "since_rev_ts": since_rev[1] if since_rev else None},
        "scored": len(scored),
        "batches_scored": len({s["batch_id"] for s in scored}),
        "filtered": dict(filtered),
        "skipped": dict(skipped),
        "all": summarize(scored),
        "by_prompt_rev": group(scored, lambda s: s["prompt_rev"], revs),
        "by_confidence": group(scored, lambda s: s["confidence"], CONFIDENCE_ORDER),
        "by_divergence": group(scored, lambda s: bucket_of(s["divergence"]),
                               [b[0] for b in DIVERGENCE_BUCKETS]),
        "escalation": {"k": ESCALATION_K, "by_prompt_rev": escalation(scored)},
        "blend": blend_report(scored, revs),
    }


def _num(row, field, fmt="+.4f", width=8):
    v = row[field]
    return ("-" if v is None else f"{v:{fmt}}").rjust(width)


def _row(label, s, width=22):
    return (f"{str(label)[:width]:<{width}} {s['n']:>6} {s['markets']:>6} "
            f"{s['clusters']:>6} "
            f"{s['brier_model']:>8.4f} {s['brier_mids']:>8.4f} "
            f"{_num(s, 'delta')} {_num(s, 'delta_ci95', '.4f')} "
            f"{_num(s, 'z', '+.1f', 6)} {_num(s, 'null', '.4f')} "
            f"{_num(s, 'excess')} {_num(s, 'excess_z', '+.1f', 6)}")


def _table(title, rows_, label, width=22):
    print()
    print(title)
    print(f"{label:<{width}} {'n':>6} {'mkts':>6} {'evts':>6} {'brier':>8} "
          f"{'mids':>8} {'delta':>8} {'+/-95%':>8} {'z':>6} {'null':>8} "
          f"{'excess':>8} {'exc_z':>6}")
    for s in rows_:
        print(_row(s["key"], s, width))


def _blend_row(label, s, width=20):
    return (f"{str(label)[:width]:<{width}} {s['n']:>6} {s['markets']:>6} "
            f"{s['clusters']:>6} "
            f"{_num(s, 'w_opt', '.3f', 7)} {_num(s, 'w_opt_ci95', '.3f', 8)} "
            f"{_num(s, 'z', '+.1f', 6)} {_num(s, 'delta_oos', '+.4f')} "
            f"{_num(s, 'delta_oos_z', '+.1f', 6)} "
            f"{_num(s, 'delta_in_sample', '+.4f')}"
            + (f"  ({s['note']})" if s.get("note") else ""))


def print_blend(bl):
    print()
    print("blend: q = w*mid + (1-w)*screen - does the screen add information "
          "at the margin?")
    print("  w_opt: the market weight that fits the outcomes best. 1.00 = the "
          "screen adds nothing")
    print("  over the price, below 1 = it adds something however badly scaled, "
          "above 1 = the fit")
    print("  wants to lever away from it. z is (w_opt - 1) over an "
          "event-clustered SE.")
    print(f"  oos: {bl['folds']}-fold-by-EVENT held-out Brier delta vs the "
          "mids. Its null is slightly ABOVE")
    print("  zero, not at it - fitting a weight to noise costs you out of "
          "sample - so only a clearly")
    print("  negative oos is evidence.")
    print("  in_s: the same delta fitted in sample, which is <= 0 for ANY "
          "data - read oos, not in_s.")
    print(f"  a slice under {BLEND_MIN_EVENTS} events is not fitted at all; "
          "it prints its counts and a note.")
    print(f"{'slice':<20} {'n':>6} {'mkts':>6} {'evts':>6} {'w_opt':>7} {'+/-95%':>8} "
          f"{'z':>6} {'oos':>8} {'oos_z':>6} {'in_s':>8}")
    for s in bl["by_prompt_rev"]:
        if s.get("n"):
            print(_blend_row(s["key"], s))
    for name, label in (("overall", "ALL"),
                        ("disagreement",
                         f"divergence>={bl['disagreement_min']}")):
        if bl[name].get("n"):
            print(_blend_row(label, bl[name]))
    for name in ("overall", "disagreement"):
        s = bl[name]
        if s.get("n"):
            print(f"  fixed-w delta vs mids [{name}]: " + " ".join(
                f"w{b['w_market']:.1f}:{b['delta_vs_mids']:+.4f}"
                for b in s["by_weight"]))


def print_clustering(c):
    """One line saying what the intervals below are clustered on."""
    if not c or not c["markets"]:
        return
    if not c["in_events"]:
        print(f"  clustered by: market ({c['markets']} of them) - "
              f"journal/screener-events.jsonl has no event for any of them, "
              f"so run `events`")
        return
    print(f"  clustered by: event - {c['in_events']} of {c['markets']} "
          f"markets grouped into {c['clusters']} clusters "
          f"(largest {c['largest']}, {c['alone']} still on their own)")


def print_report(rep):
    w = rep["window"]
    scope = [f"{k} {v}" for k, v in
             (("before", w["before"]), ("after", w["after"]),
              ("since-rev", w["since_rev"])) if v]
    print(f"screen replay: {rep['screener_rows']} screener rows over "
          f"{rep['markets_in_log']} markets, {rep['outcomes_cached']} outcomes cached")
    print(f"  window: {', '.join(scope) if scope else 'everything cached'}"
          + (f" (rev dated {w['since_rev_ts']})" if w["since_rev_ts"] else ""))
    print(f"  scored: {rep['scored']} rows in {rep['batches_scored']} batches")
    print_clustering(rep["clustering"])
    for name, counts in (("filtered", rep["filtered"]), ("skipped", rep["skipped"])):
        if counts:
            print(f"  {name}: " + ", ".join(f"{k} {v}" for k, v in
                                            sorted(counts.items(), key=lambda kv: -kv[1])))
    if not rep["scored"]:
        print("\nnothing resolved in scope yet - run `outcomes` first")
        return
    print()
    print("delta = brier - mids, so a negative delta is the screen beating "
          "the price it was handed.")
    print("  null: the delta a screen that read NOTHING still pays for "
          "disagreeing, mean sum (p-mid)^2.")
    print("  It is 2*divergence^2 on a binary market, so it rises with "
          "divergence whatever resolves.")
    print("  excess = delta - null: the part that depends on WHICH way the "
          "screen was wrong, and the only")
    print("  part a prompt edit can move. exc_z is its event-clustered z; "
          "--json carries excess_ci95.")
    print("  mkts counts markets, evts the clusters the interval is actually "
          "taken over: Polymarket sells")
    print("  one event as many markets (every exact score of one match, 27 "
          "temperature bands) and the")
    print("  screen is wrong about them together, so they are one "
          "observation. See cluster_of.")
    _table("by prompt_rev (negative delta = the screen beat the mids)",
           rep["by_prompt_rev"], "prompt_rev")
    _table("by confidence", rep["by_confidence"], "confidence")
    _table("by divergence bucket", rep["by_divergence"], "divergence")
    print(_row("ALL", rep["all"]))
    print_blend(rep["blend"])
    esc = rep["escalation"]
    print()
    print(f"escalation: the top {esc['k']} of each batch by divergence, "
          f"against the realized surprise")
    print(f"  prec/random/lift/z: overlap with the top {esc['k']} by surprise, "
          f"against the hypergeometric random ranking")
    print("  s_lift/s_z: extra mean surprise the escalated markets buy over "
          "the batch mean (0 = no skill)")
    print("  s_mids: the same lift if every market resolved as its own mid "
          "implied. s_exc/s_ez: what is left for the screen")
    print("  the prec columns have no mids null (no closed form for a rank "
          "overlap), so read s_exc for that question")
    print("  every z uses the larger of the batch-independent and the "
          "event-clustered standard error")
    print(f"{'prompt_rev':<14} {'batches':>7} {'prec':>7} {'random':>7} "
          f"{'lift':>7} {'z':>6} {'s_lift':>8} {'s_z':>6} {'s_mids':>8} "
          f"{'s_exc':>8} {'s_ez':>6}")
    for e in esc["by_prompt_rev"]:
        if e["precision_at_k"] is None:
            continue
        print(f"{str(e['key'])[:14]:<14} {e['batches']:>7} {e['precision_at_k']:>7.3f} "
              f"{e['baseline']:>7.3f} {e['lift']:>+7.3f} {_num(e, 'z', '+.1f', 6)} "
              f"{_num(e, 'surprise_lift')} {_num(e, 'surprise_z', '+.1f', 6)} "
              f"{_num(e, 'surprise_lift_mids')} {_num(e, 'surprise_lift_excess')} "
              f"{_num(e, 'surprise_excess_z', '+.1f', 6)}")


# ------------------------------------------------------------------ replay


def resolve_run_dir(value):
    path = pathlib.Path(value)
    if not path.is_absolute():
        path = ROOT / value if (ROOT / value).is_dir() else path.resolve()
    if not path.is_dir():
        sys.exit(f"{value} is not a directory - pass a `prepare` run directory")
    return path


def load_replay_answers(run_dir):
    """The held-back answers.json of a prepared run: market_id -> answer row."""
    path = run_dir / "answers.json"
    if not path.is_file():
        sys.exit(f"{path} not found - is that a `prepare` run directory?")
    try:
        data = json.loads(path.read_text())
    except ValueError as e:
        sys.exit(f"{path} is not readable JSON: {e}")
    answers = data.get("answers") if isinstance(data, dict) else None
    if not isinstance(answers, dict) or not answers:
        sys.exit(f"{path} holds no answers")
    return {str(k): v for k, v in answers.items()}


def replay_rows(run_dir, answers, events=None):
    """(replay arm, recorded arm, skipped) for a re-screened prepared run.

    The out files are read by screen.py's own parse_answers - which forgives
    the wrapper-object failure mode Haiku subagents intermittently produce -
    and graded by its own grade_answer, so a replay row goes through every
    step a journal row went through. Anything else and the comparison would
    be measuring the two graders as much as the two prompts.

    Both arms are built for the same market from the SAME mids and the SAME
    realized outcome, and the mids used are the ones in the batch file, i.e.
    the numbers the subagent actually saw. They are cross-checked against
    the mids answers.json recorded at prepare time: a batch rebuilt from
    anything but the recorded mids has already broken the pairing, so those
    markets are dropped rather than quietly scored.
    """
    skipped = collections.Counter()
    events = events or {}
    new_items, old_items = [], []
    batch_files = sorted(run_dir.glob("batch-*.json"))
    if not batch_files:
        sys.exit(f"no batch-NN.json under {run_dir} - nothing to grade")
    for bpath in batch_files:
        loaded = screen.load_batch_file(bpath)
        if loaded is None:
            skipped["batch_unreadable"] += 1
            continue
        batch_id, markets, batch_mids = loaded
        opath = run_dir / bpath.name.replace("batch-", "out-", 1)
        if not opath.is_file():
            skipped["out_file_missing"] += len(markets)
            continue
        try:
            got = screen.parse_answers(opath.read_text())
        except ValueError as e:
            print(f"screen_replay: {opath.name} unusable ({e}); batch skipped",
                  file=sys.stderr)
            skipped["out_file_unusable"] += len(markets)
            continue
        for m in markets:
            market_id = str(m.get("market_id"))
            ans = answers.get(market_id)
            if not isinstance(ans, dict):
                skipped["not_in_answers"] += 1
                continue
            mids = batch_mids.get(market_id) or m.get("market_prices") or {}
            recorded = ans.get("mids")
            if not isinstance(mids, dict) or not mids:
                skipped["missing_mids"] += 1
                continue
            if (not isinstance(recorded, dict) or set(recorded) != set(mids)
                    or any(abs(float(recorded[o]) - float(mids[o])) > 1e-9
                           for o in mids)):
                skipped["mids_not_the_recorded_ones"] += 1
                continue
            row = screen.row_base(m, mids, ans.get("screened_ts"), None,
                                  ans.get("original_prompt_rev"), batch_id)
            screen.grade_answer(row, got.get(market_id))
            if row.get("screen_error"):
                skipped["screen_error"] += 1
                continue
            winner, probs = ans.get("winner"), row["probs"]
            old = ans.get("original_probs")
            if set(probs) != set(mids) or winner not in mids:
                skipped["outcome_mismatch"] += 1
                continue
            if not isinstance(old, dict) or set(old) != set(mids):
                skipped["no_recorded_read"] += 1
                continue
            common = dict(market_id=market_id, ts=ans.get("screened_ts"),
                          batch_id=batch_id, mids=mids, winner=winner,
                          end_date=ans.get("end_date"),
                          cluster=cluster_of(market_id, events))
            new_items.append(scored_item(
                prompt_rev="replay", confidence=row["confidence"],
                divergence=row["divergence"], probs=probs, **common))
            old_items.append(scored_item(
                prompt_rev=str(ans.get("original_prompt_rev") or "recorded"),
                confidence="unknown",
                divergence=ans.get("original_divergence"), probs=old, **common))
    return new_items, old_items, skipped


def paired(new_items, old_items):
    """Per market, the replay prompt's Brier minus the recorded prompt's.

    Both arms grade the same market against the same outcome from the same
    mids, so the mids term cancels exactly and the comparison is paired:

        (brier_new - brier_mids) - (brier_old - brier_mids)
            = brier_new - brier_old
            = (null_new - null_old) + (excess_new - excess_old)

    Pairing is what makes the test affordable, by a measured factor rather
    than a hoped-for one. The alternative - scoring a new prompt on one
    sample and comparing it to the recorded prompt's excess on another -
    costs sd * sqrt(2) per market, which on this journal is 0.0790. Paired
    on the journal's own same-mids cross-revision re-screens it costs
    0.0467: 1.7x in the standard error, 2.9x in the markets that have to be
    re-screened. See paired_excess_sd, which measures that rather than
    assuming it, and size_note, which turns it into a --size.

    The gain is real and it is smaller than it looks like it should be.
    What cancels is 2 * sum (p_new - p_old)(m - y), so every market the two
    prompts agree on drops out whatever it did - but they mostly do not
    agree. The paired spread is 0.84 of a single arm's, meaning two Haiku
    screens under two different prompt texts land nearly as far from each
    other as either lands from the price. So a re-screen still needs
    hundreds of markets and pairing is what brings that down from a
    thousand, not what brings it down to fifty.

    The decomposition is the same one delta_null draws for a single arm.
    d_null never sees the outcome: it says only whether the new prompt
    disagrees with the price more loudly than the old one did, and it can be
    read off the moment the re-screen finishes. d_excess is the whole
    question - the part that knows how the market resolved, mean zero under
    calibrated mids for ANY pair of prompts, so unlike a single arm's
    positive delta it needs no apology before it is read. An edit worth
    keeping has a negative d_excess.
    """
    pairs = []
    for new, old in zip(new_items, old_items):
        d_brier = new["brier_model"] - old["brier_model"]
        d_null = new["delta_null"] - old["delta_null"]
        pairs.append({"market_id": new["market_id"],
                      "cluster": new["cluster"],
                      "divergence": old["divergence"],
                      "divergence_new": new["divergence"],
                      "brier_new": new["brier_model"],
                      "brier_old": old["brier_model"],
                      "brier_mids": new["brier_mids"],
                      "d_brier": d_brier, "d_null": d_null,
                      "d_excess": d_brier - d_null})
    return pairs


EMPTY_PAIRED = {"n": 0, "markets": 0, "clusters": 0,
                "brier_new": None, "brier_old": None,
                "d_brier": None, "d_brier_se": None, "d_brier_ci95": None,
                "z": None, "d_null": None, "d_excess": None,
                "d_excess_se": None, "d_excess_ci95": None, "d_excess_z": None}


def summarize_paired(pairs):
    n = len(pairs)
    if not n:
        return dict(EMPTY_PAIRED)
    def mean(f):
        return sum(pr[f] for pr in pairs) / n

    d_brier, d_null, d_excess = mean("d_brier"), mean("d_null"), mean("d_excess")
    se = mean_se(pairs, lambda p: p["d_brier"])
    ese = mean_se(pairs, lambda p: p["d_excess"])
    return {"n": n, "markets": len({p["market_id"] for p in pairs}),
            "clusters": len({p["cluster"] for p in pairs}),
            "brier_new": round(mean("brier_new"), 4),
            "brier_old": round(mean("brier_old"), 4),
            "d_brier": rounded(d_brier),
            "d_brier_se": None if se is None else round(se, 4),
            "d_brier_ci95": None if se is None else round(1.96 * se, 4),
            "z": None if not se else rounded(d_brier / se, 2),
            "d_null": rounded(d_null),
            "d_excess": rounded(d_excess),
            "d_excess_se": None if ese is None else round(ese, 4),
            "d_excess_ci95": None if ese is None else round(1.96 * ese, 4),
            "d_excess_z": None if not ese else rounded(d_excess / ese, 2)}


def paired_excess_sd(scored):
    """Per-market sd of the paired excess between two prompt texts, measured.

    `prepare --size` is a bet on how many markets a re-screen needs, and the
    only honest way to size it is from how much two prompt texts actually
    disagree - which this journal already records. The live screener has run
    four prompt revisions over an overlapping universe, so a market read
    under two of them, and handed the SAME mids both times, is exactly the
    paired design `--replay` implements, with a real prompt edit in place of
    a synthetic one.

    Same mids is the requirement, not a refinement: the pairing identity
    needs both arms scored against one price, and the same market screened
    two days apart is usually not. Most re-screen pairs are dropped by it.

    Measured rather than hardcoded because it moves with the prompt: two
    revisions that differ by a sentence will pair far more tightly than two
    that differ by a rewrite, and a constant baked in today would quietly
    mis-size every sample after the next big edit.

    Returns (sd, markets) or (None, 0) when the journal holds too few
    same-mids re-screen pairs to say anything.

    It counts MARKETS where every interval in this report counts events, so
    a size drawn from it is optimistic by whatever the draw's own event
    families cost - `prepare` samples markets uniformly and a draw that
    lands on three exact scores of one match has bought two fewer
    observations than it paid for. The two readings are kept apart on
    purpose: an interval must be conservative, and a sample size stated in
    markets is the number `prepare --size` actually takes.
    """
    latest = {}
    for s in scored:
        key = (s["market_id"], s["prompt_rev"])
        if key not in latest or (s["ts"] or "") > (latest[key]["ts"] or ""):
            latest[key] = s
    by_market = collections.defaultdict(dict)
    for (market_id, rev), s in latest.items():
        by_market[market_id][rev] = s
    diffs = []
    for reads in by_market.values():
        if len(reads) < 2:
            continue
        # one contribution per market, so the sd is over independent markets
        by_mids = collections.defaultdict(list)
        for rev in sorted(reads):
            item = reads[rev]
            by_mids[tuple(round(m, 6) for _, m, _ in item["blend"])].append(item)
        for pair in by_mids.values():
            if len(pair) >= 2:
                diffs.append(delta_excess(pair[1]) - delta_excess(pair[0]))
                break
    if len(diffs) < PAIRED_SD_MIN_MARKETS:
        return None, len(diffs)
    mean = sum(diffs) / len(diffs)
    var = sum((d - mean) ** 2 for d in diffs) / (len(diffs) - 1)
    return var ** 0.5, len(diffs)


def align_arms(new_items, new_recorded, ctrl_items, ctrl_recorded):
    """Match two re-screened arms market by market, or refuse to.

    `paired` takes two lists that are already aligned by position, which is
    true of the two arms `replay_rows` returns for one run. Two SEPARATE
    prepared runs are not: they were sampled independently, their batches
    are ordered differently, and either can lose a market to a skip the
    other did not hit.

    Three things have to match before a difference between the arms is a
    difference between two prompts and nothing else: the mids both arms were
    handed, the outcome both are graded against, and the recorded read the
    two are each compared to. The last one matters because the report
    decomposes the naive number exactly, and an exact decomposition needs
    one journal arm, not two. Everything that fails is dropped and counted.

    Returns (new, recorded, control, skipped), three lists aligned by index.
    """
    skipped = collections.Counter()
    ctrl_by_id = {}
    for item, rec in zip(ctrl_items, ctrl_recorded):
        ctrl_by_id.setdefault(item["market_id"], (item, rec))
    out_new, out_rec, out_ctrl = [], [], []
    seen = set()
    for item, rec in zip(new_items, new_recorded):
        market_id = item["market_id"]
        if market_id in seen:
            skipped["duplicate_market"] += 1
            continue
        found = ctrl_by_id.get(market_id)
        if found is None:
            skipped["not_in_control"] += 1
            continue
        c_item, c_rec = found
        if len(c_item["blend"]) != len(item["blend"]):
            skipped["control_outcomes_differ"] += 1
            continue
        if any(abs(m1 - m2) > 1e-9 or y1 != y2 for (_, m1, y1), (_, m2, y2)
               in zip(item["blend"], c_item["blend"])):
            skipped["control_mids_or_winner_differ"] += 1
            continue
        if any(abs(p1 - p2) > 1e-9 for (p1, _, _), (p2, _, _)
               in zip(rec["blend"], c_rec["blend"])):
            skipped["control_recorded_read_differs"] += 1
            continue
        seen.add(market_id)
        out_new.append(item)
        out_rec.append(rec)
        out_ctrl.append(c_item)
    return out_new, out_rec, out_ctrl, skipped


def control_block(new_items, new_recorded, control_dir, events=None):
    """Three reads of one sample, once a same-day control arm exists.

    `--replay` on its own pairs the re-screened arm against the journal, and
    that pairing cancels less than it looks like it does. The journal arm was
    produced days or weeks earlier, by whatever "subagent:haiku" resolved to
    then - the journal records the alias, not a version - and the subagent
    was told a different date. For a market that has since closed, the brief
    still carries its end_date, so the re-screen is answering "who won" where
    the live screen answered "who will win". None of that is the prompt, and
    all of it rides on a new-vs-journal number.

    Screening the SAME prepared sample twice on the same day, once under each
    prompt text, holds every one of those fixed: same model, same date, same
    briefs, same mids, same outcomes. `prepare --like` builds the second run.

    The three reads decompose exactly, per market and therefore in the mean,
    because each is a difference of Briers over the same three arms:

        naive (new - journal) = prompt (new - control) + drift (control - journal)

    So this block does not merely add a cleaner number, it says how much of
    the number the tool reported before was ever about the prompt. A drift
    read far from zero is not a bug in either prompt; it is the measurement
    of what re-screening alone moves, and it is the reason the prompt read is
    the one to quote.
    """
    c_answers = load_replay_answers(control_dir)
    ctrl_items, ctrl_recorded, c_skipped = replay_rows(control_dir, c_answers,
                                                       events)
    new, rec, ctrl, a_skipped = align_arms(new_items, new_recorded,
                                           ctrl_items, ctrl_recorded)
    prompt_pairs = paired(new, ctrl)
    buckets = collections.defaultdict(list)
    for pr in prompt_pairs:
        buckets[bucket_of(pr["divergence"])].append(pr)
    sd, sd_markets = excess_sd(prompt_pairs)
    return {
        "run": control_dir.name,
        "run_dir": str(control_dir),
        "arm_prompt": arm_prompt(control_dir),
        "prompt_excess_sd": None if sd is None else round(sd, 6),
        "prompt_excess_sd_markets": sd_markets,
        "answers": len(c_answers),
        "graded": len(ctrl_items),
        "matched": len(new),
        "skipped": dict(c_skipped),
        "unmatched": dict(a_skipped),
        "arm": summarize(ctrl),
        "prompt": summarize_paired(prompt_pairs),
        "prompt_by_divergence": [
            dict(summarize_paired(buckets[b]), key=b)
            for b, _, _ in DIVERGENCE_BUCKETS if buckets[b]],
        "drift": summarize_paired(paired(ctrl, rec)),
        "naive": summarize_paired(paired(new, rec)),
    }


def read_manifest(run_dir):
    """A prepared run's manifest.json, or {} if it is gone or unreadable."""
    path = run_dir / "manifest.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except ValueError:
        return {}


def arm_prompt(run_dir):
    """Which judgment brief a prepared run's subagents were sent to.

    Re-hashes the run's own copy and checks it against the hash the manifest
    recorded, so this answers "what text did this arm read" with evidence
    rather than with a note about what was in the working tree at the time.
    A run prepared before pinning existed has no copy: it is reported
    unpinned, and any comparison built on it carries the possibility that
    both arms read the same text. See prompt_bytes.
    """
    rec = (read_manifest(run_dir).get("replay") or {}).get("prompt") or {}
    path = run_dir / (rec.get("file") or ARM_PROMPT_FILE)
    present = path.is_file()
    return {"pinned": bool(rec.get("rev")),
            "rev": rec.get("rev"),
            "source": rec.get("source"),
            "file": rec.get("file") or ARM_PROMPT_FILE,
            "present": present,
            "intact": bool(rec.get("rev")) and present
                      and screen.blob_rev(path) == rec.get("rev")}


def arm_prompt_state(a):
    """One phrase for what is known about an arm's prompt text."""
    if not a:
        return "unknown"
    if a.get("intact"):
        return f"pinned {str(a['rev'])[:12]}"
    if a.get("pinned"):
        return f"pinned {str(a['rev'])[:12]} but its copy is missing or edited"
    return "not pinned"


def excess_sd(pairs):
    """Per-market sd of a paired-excess reading, over its own markets.

    The same quantity paired_excess_sd estimates from the journal's
    cross-revision re-screens, measured instead on the comparison actually in
    hand - so a run that has already been screened can size the next one
    without the proxy. Counts markets rather than events for the reason
    paired_excess_sd gives. Returns (sd, markets).
    """
    by_market = {}
    for pr in pairs:
        by_market.setdefault(pr["market_id"], pr["d_excess"])
    diffs = list(by_market.values())
    if len(diffs) < 2:
        return None, len(diffs)
    mean = sum(diffs) / len(diffs)
    var = sum((d - mean) ** 2 for d in diffs) / (len(diffs) - 1)
    return var ** 0.5, len(diffs)


def replay_report(run_dir, control_dir=None):
    answers = load_replay_answers(run_dir)
    events, _ = load_event_cache()
    new_items, old_items, skipped = replay_rows(run_dir, answers, events)
    pairs = paired(new_items, old_items)
    manifest = read_manifest(run_dir)
    buckets = collections.defaultdict(list)
    for pr in pairs:
        buckets[bucket_of(pr["divergence"])].append(pr)
    rep = {
        "run": run_dir.name,
        "run_dir": str(run_dir),
        "clustering": clustering_note(new_items),
        "prepared_prompt_rev": manifest.get("prompt_rev"),
        "prompt_rev_now": screen.blob_rev(PROMPT_FILE),
        "arm_prompt": arm_prompt(run_dir),
        "answers": len(answers),
        "graded": len(pairs),
        "skipped": dict(skipped),
        "replay": summarize(new_items),
        "recorded": summarize(old_items),
        "paired": summarize_paired(pairs),
        "paired_by_divergence": [
            dict(summarize_paired(buckets[b]), key=b)
            for b, _, _ in DIVERGENCE_BUCKETS if buckets[b]],
    }
    if control_dir is not None:
        rep["control"] = control_block(new_items, old_items, control_dir,
                                       events)
    return rep


def _paired_row(label, s, width=22):
    return (f"{str(label)[:width]:<{width}} {s['n']:>6} {s['markets']:>6} "
            f"{s['clusters']:>6} "
            f"{s['brier_new']:>8.4f} {s['brier_old']:>8.4f} "
            f"{_num(s, 'd_brier')} {_num(s, 'd_brier_ci95', '.4f')} "
            f"{_num(s, 'z', '+.1f', 6)} {_num(s, 'd_null')} "
            f"{_num(s, 'd_excess')} {_num(s, 'd_excess_z', '+.1f', 6)}")


def print_replay(rep):
    print(f"screen replay: re-screened run {rep['run']}")
    print(f"  {rep['graded']} of {rep['answers']} prepared markets graded")
    print_clustering(rep.get("clustering"))
    if rep["skipped"]:
        print("  skipped: " + ", ".join(
            f"{k} {v}" for k, v in sorted(rep["skipped"].items(),
                                          key=lambda kv: -kv[1])))
    ap = rep.get("arm_prompt") or {}
    if ap.get("intact"):
        print(f"  prompt: pinned {str(ap['rev'])[:12]} at {rep['run']}/"
              f"{ap['file']} (from {ap['source']}), which is the file this "
              f"run's subagents were sent to")
    elif ap.get("pinned"):
        print(f"  WARNING: this run pinned prompt {str(ap['rev'])[:12]} but "
              f"{rep['run']}/{ap['file']} is missing or has been edited "
              f"since, so what its subagents read is no longer provable")
    elif rep["prepared_prompt_rev"] and rep["prepared_prompt_rev"] != rep["prompt_rev_now"]:
        print(f"  note: the run was prepared under prompt_rev "
              f"{rep['prepared_prompt_rev'][:12]} and "
              f"strategy/screener-prompt.md is now {rep['prompt_rev_now'][:12]}. "
              f"This run pinned no copy of the brief, so which text its "
              f"subagents read is not recorded - re-prepare it with --prompt "
              f"or --prompt-rev.")
    if not rep["graded"]:
        print("\nnothing graded - write out-NN.json beside each batch-NN.json first")
        return
    print()
    print("each arm against the mids it was handed (same columns as `score`):")
    print(f"{'arm':<22} {'n':>6} {'mkts':>6} {'evts':>6} {'brier':>8} {'mids':>8} "
          f"{'delta':>8} {'+/-95%':>8} {'z':>6} {'null':>8} {'excess':>8} "
          f"{'exc_z':>6}")
    print(_row("replay prompt", rep["replay"]))
    print(_row("recorded prompt", rep["recorded"]))
    print()
    print("paired, per market: the replay prompt's Brier minus the recorded "
          "one's, same outcome,")
    print("  same mids, so every market the two prompts agree on drops out. "
          "That is worth roughly")
    print("  a third of the sample an unpaired comparison would need on this "
          "journal - real, but not")
    print("  magic, since two prompts disagree nearly as much as either "
          "disagrees with the price.")
    print("  d_null is the extra volume of disagreement alone and is known "
          "before anything resolves;")
    print("  d_excess is the directional part, mean zero under calibrated "
          "mids for any pair of")
    print("  prompts. A NEGATIVE d_excess is an edit worth keeping.")
    print(f"{'slice':<22} {'n':>6} {'mkts':>6} {'evts':>6} {'new_b':>8} {'old_b':>8} "
          f"{'d_brier':>8} {'+/-95%':>8} {'z':>6} {'d_null':>8} "
          f"{'d_exc':>8} {'d_ez':>6}")
    for s in rep["paired_by_divergence"]:
        print(_paired_row(s["key"], s))
    print(_paired_row("ALL", rep["paired"]))
    if rep.get("control"):
        print_control(rep["control"], rep.get("arm_prompt"))
    else:
        print()
        print("no control arm. This reading pairs a re-screen done today "
              "against a live screen")
        print("  done days earlier, so it carries model drift (the journal "
              "records the alias")
        print("  \"subagent:haiku\", not a version) and date drift (a closed "
              "market's brief still")
        print("  carries its end_date, so the re-screen is asked who won "
              "where the live screen")
        print("  was asked who will win) on top of the prompt edit. "
              "`prepare --like` the same")
        print("  sample, re-screen it under the OLD prompt too, and pass it "
              "as --control to")
        print("  separate the two.")


def print_control(c, new_arm=None):
    print()
    print(f"control arm: run {c['run']}, {c['matched']} of {c['graded']} "
          f"graded markets matched to the replay arm")
    ca = c.get("arm_prompt") or {}
    na = new_arm or {}
    if ca.get("intact") and na.get("intact"):
        if ca["rev"] == na["rev"]:
            print(f"  BOTH ARMS PINNED THE SAME TEXT ({str(ca['rev'])[:12]}). "
                  f"This is an A/A run: `prompt` below")
            print("    measures the subagents' own run-to-run noise under one "
                  "brief, not an edit. That")
            print("    is the floor a real edit has to clear, and the sd "
                  "beside it is the honest number")
            print("    to size the next A/B with.")
        else:
            print(f"  arms: replay pinned {str(na['rev'])[:12]} ({na['source']}), "
                  f"control pinned {str(ca['rev'])[:12]} ({ca['source']}) - "
                  f"two different texts")
    else:
        print(f"  WARNING: replay arm {arm_prompt_state(na)}, control arm "
              f"{arm_prompt_state(ca)}. Nothing proves the two")
        print("    arms read different briefs, so `prompt` below may be "
              "comparing one prompt with")
        print("    itself. Re-prepare both arms with --prompt / --prompt-rev.")
    if c["skipped"]:
        print("  control skipped: " + ", ".join(
            f"{k} {v}" for k, v in sorted(c["skipped"].items(),
                                          key=lambda kv: -kv[1])))
    if c["unmatched"]:
        print("  unmatched: " + ", ".join(
            f"{k} {v}" for k, v in sorted(c["unmatched"].items(),
                                          key=lambda kv: -kv[1])))
    if not c["matched"]:
        print("  nothing matched - the two runs share no market that both "
              "arms graded from the same mids")
        return
    print(_row("control prompt", c["arm"]))
    print()
    print("three reads of the same markets. The control arm was re-screened "
          "the same day as")
    print("  the replay arm, from the same briefs and the same mids, so "
          "prompt holds the model")
    print("  version and the date fixed and is the only one of the three "
          "that is about the")
    print("  edit. drift is what re-screening alone moves with no prompt "
          "change at all, and")
    print("  naive = prompt + drift exactly, per market. Quote prompt; read "
          "drift to know how")
    print("  much of naive was never the prompt.")
    print(f"{'read':<22} {'n':>6} {'mkts':>6} {'evts':>6} {'new_b':>8} {'old_b':>8} "
          f"{'d_brier':>8} {'+/-95%':>8} {'z':>6} {'d_null':>8} "
          f"{'d_exc':>8} {'d_ez':>6}")
    print(_paired_row("prompt  new-control", c["prompt"]))
    print(_paired_row("drift   control-jrnl", c["drift"]))
    print(_paired_row("naive   new-journal", c["naive"]))
    if c.get("prompt_excess_sd") is not None:
        sd, m = c["prompt_excess_sd"], c["prompt_excess_sd_markets"]
        need = max(1.0, (1.96 * sd / PAIRED_EXCESS_TARGET) ** 2)
        def small(v):
            return f"{v:.4f}" if v >= 5e-5 else f"{v:.2e}"
        print(f"  this comparison's own per-market paired-excess sd is "
              f"{small(sd)} over {m} markets, so it")
        print(f"    resolves +/-{small(1.96 * sd / m ** 0.5)} and "
              f"+/-{PAIRED_EXCESS_TARGET:.4f} would need about {need:.0f}. "
              f"That is this design's")
        print("    own number; `prepare --size` has to use the journal's "
              "cross-revision proxy instead.")
    if c["prompt_by_divergence"]:
        print()
        print("prompt read by the control arm's divergence bucket:")
        for s in c["prompt_by_divergence"]:
            print(_paired_row(s["key"], s))


def cmd_score(args):
    if args.replay:
        if args.before or args.after or args.since_rev:
            sys.exit("--replay grades one prepared run; the window filters "
                     "apply to the journal and mean nothing beside it")
        run_dir = resolve_run_dir(args.replay)
        control_dir = resolve_run_dir(args.control) if args.control else None
        if control_dir is not None and control_dir.resolve() == run_dir.resolve():
            sys.exit("--control must be a different run from --replay; an arm "
                     "compared with itself measures nothing")
        rep = replay_report(run_dir, control_dir)
        printer = print_replay
    elif args.control:
        sys.exit("--control is the second arm of a --replay comparison and "
                 "means nothing on its own")
    else:
        events, _ = load_event_cache()
        rep = build_report(load_screener_rows(), load_outcome_cache(), args,
                           events)
        printer = print_report
    if args.json:
        print(json.dumps(rep, indent=1))
    else:
        printer(rep)
    return 0


# ----------------------------------------------------------------- prepare


def load_static_cache():
    cache = {}
    for r in resolve.load_jsonl(STATIC_CACHE):
        mid = r.get("market_id")
        if mid is not None:
            cache[str(mid)] = r
    return cache


def fetch_static(market_ids, sleep):
    """market_id -> {question, description, end_date} from gamma, cached.

    Only the fields that cannot move after the fact. Never prices, never
    volume or liquidity: the sample is already resolved, so anything the
    market did later is hindsight the re-screen must not see.
    """
    cache = load_static_cache()
    missing = [m for m in market_ids if m not in cache]
    if missing:
        STATIC_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with STATIC_CACHE.open("a") as fh:
            for i, mid in enumerate(missing):
                if i:
                    time.sleep(sleep)
                try:
                    m = pmapi.gamma_market(mid)
                except RuntimeError as e:
                    print(f"screen_replay: static fetch failed for {mid}: {e}",
                          file=sys.stderr)
                    continue
                row = {"market_id": mid, "fetched_ts": screen.iso(screen.utcnow()),
                       "question": m.get("question"),
                       "description": m.get("description"),
                       "end_date": m.get("endDate")}
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh.flush()
                cache[mid] = row
    return cache


def replay_candidates(rows, cache, after, before):
    """Latest PAIRABLE screening row per resolved market in [after, before).

    Pairable, not merely gradeable: the recorded read is half of every
    comparison the re-screen will be put to, so a market whose recorded probs
    are missing or name outcomes the mids do not is a subagent call spent on
    a market `score --replay` will drop as no_recorded_read. Four markets in
    this journal answer a Yes/No market with Over/Under; they cost nothing to
    exclude here and a whole re-screen slot each to include.
    """
    latest = {}
    for r in rows:
        ts = r.get("ts") or ""
        if (after and ts < after) or (before and ts >= before):
            continue
        if r.get("screen_error"):
            continue
        mid = str(r.get("market_id"))
        out = cache.get(mid)
        if not out or out.get("status") != "resolved":
            continue
        mids, probs = r.get("mids"), r.get("probs")
        if not isinstance(mids, dict) or out.get("winner") not in mids:
            continue
        if not isinstance(probs, dict) or set(probs) != set(mids):
            continue
        if mid not in latest or ts > (latest[mid].get("ts") or ""):
            latest[mid] = r
    return latest


def event_note(picked):
    """How many independent observations a drawn sample actually holds.

    `--size` is counted in markets and paid for in subagent calls, one per
    market, but the intervals `score` reports are taken over events. A draw
    that lands on four exact scores of one match has spent four calls to buy
    one observation, and nothing else in `prepare`'s output would say so.
    """
    events, _ = load_event_cache()
    clusters = {cluster_of(m, events) for m in picked}
    mapped = sum(1 for m in picked if m in events)
    if not mapped:
        return (f"screen_replay: none of the {len(picked)} drawn markets is "
                f"in journal/screener-events.jsonl, so `score` will cluster "
                f"each on its own - run `events` to check for families")
    return (f"screen_replay: the drawn {len(picked)} markets span "
            f"{len(clusters)} events ({mapped} mapped), which is the count "
            f"the paired interval is really taken over; the sd above counts "
            f"markets, so read it as an upper bound on what this draw buys")


def size_note(rows, cache, size):
    """What --size the operator just bought, in the units the report speaks.

    A re-screen costs a subagent call per market and the number is chosen
    before any of them run, so it should not be chosen blind. This turns the
    measured per-market spread into the two figures that decide it: the
    smallest paired excess the drawn sample could distinguish from zero, and
    the sample the operator would need for a difference the size of the ones
    `score` already reports between revisions - which are hundredths of a
    Brier point, so the answer is hundreds of markets rather than dozens.
    """
    scored, _, _ = select(rows, cache, None, None, None)
    sd, pairs = paired_excess_sd(scored)
    if sd is None:
        return (f"screen_replay: only {pairs} same-mids cross-revision "
                f"re-screens in the journal, too few to size this sample")
    mde = 1.96 * sd / max(size, 1) ** 0.5
    need = (1.96 * sd / PAIRED_EXCESS_TARGET) ** 2
    return (f"screen_replay: per-market paired-excess sd {sd:.4f} over {pairs} "
            f"same-mids cross-revision re-screens, so {size} markets resolve a "
            f"paired excess of +/-{mde:.4f} and +/-{PAIRED_EXCESS_TARGET:.4f} "
            f"would need about {need:.0f}")


def prompt_bytes(prompt_path, prompt_rev):
    """The exact judgment brief one arm pins, and where it came from.

    A controlled comparison needs its two arms to read two DIFFERENT prompt
    texts, and the live subagent prompt sends every arm to one mutable file,
    strategy/screener-prompt.md. Editing that file between the two
    re-screens is not a workable way to get there: an arm fans out as many
    parallel subagents, so a late starter in the first arm reads the second
    arm's text, and nothing in the record afterwards says which text any
    subagent read. A comparison whose two arms cannot be shown to differ can
    report a prompt effect for two identical prompts.

    So each prepared run gets its own copy of the brief under work/, its
    subagent prompt points at that copy, and the copy's blob hash goes in the
    manifest. The copy is immutable in practice - nothing writes to a run
    directory after `prepare` - and `score --replay` re-hashes it, so the
    text every arm read is provable after the fact rather than remembered.

    --prompt-rev takes the text straight out of git by blob hash, which is
    the same identifier journal/screener.jsonl records in prompt_rev (see
    screen.blob_rev), so the four revisions the `score` tables rank can be
    put head to head under one model on one day instead of compared across
    the weeks that separated them live.

    Returns (bytes, source label).
    """
    if prompt_path and prompt_rev:
        sys.exit("pass --prompt PATH or --prompt-rev SHA, not both")
    if prompt_rev:
        try:
            out = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob",
                                  prompt_rev], capture_output=True,
                                 timeout=10, check=True)
        except Exception:  # noqa: BLE001 - any git failure means "no such blob"
            sys.exit(f"--prompt-rev {prompt_rev}: not a blob in this "
                     f"repository. prompt_rev in journal/screener.jsonl is a "
                     f"git blob hash of strategy/screener-prompt.md; the blob "
                     f"has to be reachable here to be re-screened.")
        return out.stdout, f"git blob {prompt_rev}"
    path = pathlib.Path(prompt_path) if prompt_path else PROMPT_FILE
    if not path.is_absolute() and not path.is_file():
        path = ROOT / path
    if not path.is_file():
        sys.exit(f"{prompt_path or PROMPT_FILE}: no such prompt file")
    data = path.read_bytes()
    if not data.strip():
        sys.exit(f"{path}: prompt file is empty")
    try:
        label = str(path.relative_to(ROOT))
    except ValueError:
        label = str(path)
    return data, label


def replay_subagent_prompt(rel_dir):
    """The live subagent prompt, pointed at this arm's pinned brief.

    Built by substitution into screen.SUBAGENT_PROMPT_TEMPLATE rather than
    written out fresh, because everything in it except which file holds the
    judgment brief - the output schema, the calibration rules, the no-browse
    rule, the stale-mids warning - has to stay identical to what the live
    screener says, or the arms differ by more than a prompt.
    """
    needle = "strategy/screener-prompt.md"
    tmpl = screen.SUBAGENT_PROMPT_TEMPLATE
    if needle not in tmpl:
        print(f"screen_replay: screen.SUBAGENT_PROMPT_TEMPLATE no longer names "
              f"{needle}; the re-screen will read the live prompt, not this "
              f"run's pinned copy", file=sys.stderr)
        return tmpl.format(work_dir=rel_dir)
    return tmpl.replace(needle, "{work_dir}/" + ARM_PROMPT_FILE).format(
        work_dir=rel_dir)


ANSWER_FIELDS = ("winner", "end_date", "mids", "screened_ts",
                 "original_prompt_rev", "original_probs", "original_divergence")


def fresh_run_dir(now):
    """A run directory that is not an existing run's.

    The stamp is second-precision, and the two-arm workflow deliberately runs
    `prepare` twice back to back - `--like` fetches nothing, so the second
    call can land in the same second as the first. Writing into the first
    run's directory would overwrite its batch files and its answers with the
    copy's, which is silent and destroys the arm being copied.
    """
    base = REPLAY_ROOT / screen.stamp(now)
    path, n = base, 1
    while path.exists():
        path = base.with_name(f"{base.name}-{n}")
        n += 1
    return path


def picks_from_journal(rows, cache, after, before, seed, size):
    """(market_id -> held-back answer row, eligible count) for a window."""
    latest = replay_candidates(rows, cache, after, before)
    picked = sorted(latest, key=lambda m: screen.sample_key(seed, m))[:size]
    picks = {mid: {"winner": cache[mid].get("winner"),
                   "end_date": cache[mid].get("end_date"),
                   # not written to answers.json; only a fallback for the
                   # brief when the gamma static fetch misses this market
                   "question": latest[mid].get("question"),
                   "mids": latest[mid]["mids"],
                   "screened_ts": latest[mid].get("ts"),
                   "original_prompt_rev": latest[mid].get("prompt_rev"),
                   "original_probs": latest[mid].get("probs"),
                   "original_divergence": latest[mid].get("divergence")}
             for mid in picked}
    return picks, len(latest)


def picks_from_run(source_dir):
    """The exact sample of an existing prepared run: answers and briefs.

    The control arm of a `score --replay --control` comparison has to be the
    same question put to the same model on the same day, differing only in
    the prompt text. Re-deriving the sample from the journal cannot promise
    that: the resolution cache grows between runs, so a window that was
    eligible yesterday is a slightly different population today and the
    sample drifts with it. Worse, the static fields come from gamma, which
    can edit a question or a description between two fetches.

    So this copies both halves of the source run - its answers.json and the
    briefs out of its own batch files - and re-chunks them. Nothing is
    fetched. The only thing that differs between the two runs is which
    strategy/screener-prompt.md the subagents read, which is the whole point.

    Returns (market_id -> answer row, market_id -> candidate dict).
    """
    answers = load_replay_answers(source_dir)
    briefs = {}
    for bpath in sorted(source_dir.glob("batch-*.json")):
        loaded = screen.load_batch_file(bpath)
        if loaded is None:
            continue
        for m in loaded[1]:
            prices = m.get("market_prices") or {}
            outcomes = [str(o) for o in (m.get("outcomes") or prices)]
            briefs.setdefault(str(m.get("market_id")), {
                "market_id": str(m.get("market_id")),
                "question": m.get("question"),
                "outcomes": outcomes,
                "outcome_prices": [prices.get(o) for o in outcomes],
                "end_date": m.get("end_date"),
                "description": m.get("description") or "",
                "volume_24h": m.get("volume_24h") or 0,
                "liquidity": m.get("liquidity") or 0,
            })
    picks, candidates = {}, {}
    for market_id, ans in answers.items():
        market_id = str(market_id)
        if not isinstance(ans, dict) or market_id not in briefs:
            continue
        if not isinstance(ans.get("mids"), dict) or not ans.get("winner"):
            continue
        picks[market_id] = {f: ans.get(f) for f in ANSWER_FIELDS}
        candidates[market_id] = briefs[market_id]
    if not picks:
        sys.exit(f"{source_dir} has no market held in both answers.json and a "
                 f"batch file - nothing to rebuild")
    return picks, candidates


def cmd_prepare(args):
    source_dir = resolve_run_dir(args.like) if args.like else None
    if source_dir is None and not (args.after and args.before):
        sys.exit("prepare needs --after and --before, or --like DIR to rebuild "
                 "an existing run's sample")
    after = parse_arg_ts(args.after, "--after")
    before = parse_arg_ts(args.before, "--before")
    if after and before and after >= before:
        sys.exit("--after must be earlier than --before")
    rows = load_screener_rows()
    cache = load_outcome_cache()
    copied = None
    if source_dir is not None:
        picks, copied = picks_from_run(source_dir)
        eligible, static = len(picks), {}
    else:
        picks, eligible = picks_from_journal(rows, cache, after, before,
                                             args.seed, args.size)
        if not picks:
            print("screen_replay: no resolved, gradeable markets screened in "
                  "that window - widen it or run `outcomes` first",
                  file=sys.stderr)
            return 1
        static = fetch_static(list(picks), args.sleep)

    picked = list(picks)
    candidates = []
    for mid in picked:
        if copied is not None:
            candidates.append(copied[mid])
            continue
        a, s = picks[mid], static.get(mid, {})
        mids = a["mids"]
        candidates.append({
            "market_id": mid,
            "question": s.get("question") or a.get("question"),
            # recorded at screen time; never a live book
            "outcomes": list(mids),
            "outcome_prices": [mids[o] for o in mids],
            "end_date": s.get("end_date") or a.get("end_date"),
            "description": s.get("description") or "",
            # not recorded at screen time and post-resolution now: left at 0
            # rather than backfilled with hindsight.
        })

    brief, prompt_source = prompt_bytes(args.prompt, args.prompt_rev)
    now = screen.utcnow()
    work_dir = fresh_run_dir(now)
    work_dir.mkdir(parents=True)
    prompt_path = work_dir / ARM_PROMPT_FILE
    prompt_path.write_bytes(brief)
    arm_rev = screen.blob_rev(prompt_path)
    if args.prompt_rev and not arm_rev.startswith(args.prompt_rev):
        sys.exit(f"pinned brief hashes {arm_rev}, not the requested "
                 f"{args.prompt_rev} - refusing to label an arm with a "
                 f"revision it does not hold")
    # --like re-chunks the source run's markets, so it inherits its batch size
    # unless told otherwise: a control arm whose batches hold different
    # neighbours is not the same question put to the same model, and batch
    # composition is one of the few things about a re-screen that is free to
    # hold fixed.
    batch_size = args.batch_size
    if batch_size is None:
        batch_size = (read_manifest(source_dir).get("batch_size")
                      if source_dir is not None else None)
    batch_size = max(1, int(batch_size or screen.SCREENER_DEFAULTS["batch_size"]))
    batches = screen.chunk(candidates, batch_size)
    cfg = {"batch_size": batch_size, "top_n": ESCALATION_K}
    written = screen.write_work_dir(work_dir, batches, {}, {}, {}, cfg,
                                    arm_rev, now)

    rel_dir = str(work_dir.relative_to(ROOT))
    # The answers never enter a batch file or the subagent prompt; the manifest
    # only names the file so `score` can find it later.
    (work_dir / "answers.json").write_text(json.dumps({
        "run": work_dir.name, "created_utc": screen.iso(now),
        "answers": {mid: {f: picks[mid].get(f) for f in ANSWER_FIELDS}
                    for mid in picked},
    }, indent=2, ensure_ascii=False) + "\n")

    manifest_path = work_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["replay"] = {
        "source": (str(source_dir) if source_dir is not None
                   else str(SCREENER.relative_to(ROOT))),
        "like": source_dir.name if source_dir is not None else None,
        "window": {"after": after, "before": before},
        "seed": args.seed, "size": args.size,
        "eligible_markets": eligible, "selected": len(picked),
        "static_fetch_misses": [m for m in picked if m not in static]
                               if copied is None else [],
        "mids": "recorded at screen time (journal/screener.jsonl), never live",
        "volume_liquidity": "zeroed - not recorded at screen time",
        "answers_file": "answers.json",
        "prompt": {"file": ARM_PROMPT_FILE, "rev": arm_rev,
                   "source": prompt_source},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    print(json.dumps({"work_dir": rel_dir, "batch_count": len(written),
                      "batches": written, "markets": len(picked),
                      "eligible_markets": eligible,
                      "prompt_file": f"{rel_dir}/{ARM_PROMPT_FILE}",
                      "prompt_rev": arm_rev,
                      "prompt_source": prompt_source,
                      "subagent_prompt_template":
                          replay_subagent_prompt(rel_dir)},
                     indent=2))
    print(f"screen_replay: this arm's judgment brief is pinned at {rel_dir}/"
          f"{ARM_PROMPT_FILE} (rev {arm_rev[:12]}, from {prompt_source}); the "
          f"printed subagent prompt sends the re-screen to that copy, not to "
          f"{PROMPT_FILE.relative_to(ROOT)}, so the two arms of a --control "
          f"comparison cannot read each other's text", file=sys.stderr)
    if copied is not None:
        print(f"screen_replay: copied all {len(picked)} markets of "
              f"{source_dir.name} into {len(written)} batch(es) under "
              f"{rel_dir}, briefs and mids byte for byte, nothing fetched; "
              f"answers held in {rel_dir}/answers.json. Re-screen this run "
              f"and pass it to `score --replay ... --control ...`",
              file=sys.stderr)
        return 0
    print(f"screen_replay: rebuilt {len(picked)} of {eligible} eligible "
          f"resolved markets into {len(written)} batch(es) under {rel_dir}; "
          f"answers held in {rel_dir}/answers.json", file=sys.stderr)
    print(size_note(rows, cache, len(picked)), file=sys.stderr)
    print(event_note(picked), file=sys.stderr)
    print(f"screen_replay: for a drift-free reading, `prepare --like "
          f"{rel_dir} --prompt-rev <old blob>` and re-screen that copy too, "
          f"then `score --replay <new> --control <old>`. Pinning the SAME rev "
          f"in both arms makes it an A/A run, which measures this design's "
          f"own noise floor instead of an edit.", file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("outcomes", help="fill the resolution cache")
    o.add_argument("--limit", type=int, help="stop after this many fetches")
    o.add_argument("--sleep", type=float, default=FETCH_SLEEP_S,
                   help="seconds between requests (default %(default)s)")
    o.set_defaults(fn=cmd_outcomes)

    e = sub.add_parser("events", help="fill the market -> event cache")
    e.add_argument("--limit", type=int,
                   help="stop after this many gamma requests")
    e.add_argument("--sleep", type=float, default=FETCH_SLEEP_S,
                   help="seconds between requests (default %(default)s)")
    e.add_argument("--window", type=int, default=EVENT_WINDOW_H,
                   help="hours of end date per swept span (default "
                        "%(default)s); smaller spans page more shallowly")
    e.add_argument("--resweep", action="store_true",
                   help="sweep spans this cache has already swept")
    e.set_defaults(fn=cmd_events)

    s = sub.add_parser("score", help="score the screen against resolutions")
    s.add_argument("--before", metavar="TS",
                   help="keep only markets whose end_date is before this")
    s.add_argument("--after", metavar="TS",
                   help="keep only markets whose end_date is at or after this")
    s.add_argument("--since-rev", metavar="SHA",
                   help="keep only rows screened under this prompt_rev, after "
                        "the commit that introduced it")
    s.add_argument("--replay", metavar="DIR",
                   help="grade a re-screened `prepare` run instead of the "
                        "journal, paired against the recorded reads")
    s.add_argument("--control", metavar="DIR",
                   help="a second re-screen of the same sample under the old "
                        "prompt (see `prepare --like`), so the comparison "
                        "cancels model and date drift as well as the mids")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_score)

    p = sub.add_parser("prepare", help="rebuild a resolved sample as batches")
    p.add_argument("--after", metavar="TS",
                   help="required unless --like is given")
    p.add_argument("--before", metavar="TS",
                   help="required unless --like is given")
    p.add_argument("--like", metavar="DIR",
                   help="rebuild the exact sample of an existing prepared run "
                        "- same markets, same briefs, same mids, nothing "
                        "fetched - as the control arm of a `score --control` "
                        "comparison")
    p.add_argument("--seed", default="screen-replay",
                   help="sample seed; the same seed and window give the same "
                        "sample (default %(default)s)")
    p.add_argument("--size", type=int, default=100)
    p.add_argument("--batch-size", type=int, default=None,
                   help="markets per batch (default %d, or the source run's "
                        "under --like)" % screen.SCREENER_DEFAULTS["batch_size"])
    p.add_argument("--prompt", metavar="PATH",
                   help="the judgment brief this arm pins and its subagents "
                        "read (default strategy/screener-prompt.md)")
    p.add_argument("--prompt-rev", metavar="SHA",
                   help="pin the brief from a git blob hash instead - the "
                        "same identifier journal/screener.jsonl records in "
                        "prompt_rev, so a historical revision can be "
                        "re-screened exactly")
    p.add_argument("--sleep", type=float, default=FETCH_SLEEP_S)
    p.set_defaults(fn=cmd_prepare)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
