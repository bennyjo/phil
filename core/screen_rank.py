#!/usr/bin/env python3
"""No-model screening tier: rank scanned markets by mid uncertainty.

PROTECTED CORE - the trading agent must not edit files under core/.

DORMANT. Nothing calls this. CYCLE.md, core/screen.py prepare and
core/screen.py collect are untouched, and the Haiku screening tier is still
the live one. This exists so the operator can switch the screen over in one
step once the evidence is read, and can switch it back by not running it.

Why it exists (operator, 2026-09-04, journal/operator-notes.md): the offline
evaluator core/screen_replay.py scored 18,047 screener rows and found that
the Haiku screen adds nothing over the mid it is handed, on any of the four
prompt revisions - the fitted market weight is 1.11 +/- 0.23 and no fixed
blend beats the mids. It also found WHY ranking a batch by divergence picks
surprising markets: divergence prefers prices near 0.5, and a price near 0.5
is surprising however it resolves. If that is the whole mechanism, then the
mechanism is computable, and the model tier is paying subagent batches for a
number the price already carries.

So this ranks by mid uncertainty instead:

    rank_score = 2 * p * (1 - p)      (the binary form of screen_replay's
                                       mid_null_surprise: the surprise the
                                       market itself expects to realize)

Same input, same strata, same journal, no subagents, no quota. What it
CANNOT do is the part of strategy/screener-prompt.md that is judgment:
"liquid and well-defined", "a named official print", "a fact I would have to
look up". Dropping the model tier drops those. The part of the brief a
formula can carry is in strategy/screener-filters.json, which is
agent-editable and read here - principally the HARD RULE on line-constructed
markets, because a spread line is set so the cover probability sits near
0.50 by construction and would otherwise take half of every list.

Three things this deliberately does NOT do, all so a rank row can never be
mistaken for a screen row:

  * It never sets `divergence`. There is no belief here to diverge from the
    price with, so the field stays null and the ranking lives in
    `rank_score`. Downstream code that ranks or scores on divergence
    (core/screen.py collect, core/screen_replay.py select) therefore skips
    these rows instead of reading the formula as a model opinion.
  * `screen_error` says so on every row, which is what core/validate.py's
    "every unscored row must say why" rule asks of a null divergence, and
    what makes screen_replay count these rows as skipped rather than graded.
  * `probs` is the mids verbatim and `model` names the formula, so a row is
    self-describing: nobody read anything, the price is the estimate.

It never writes journal/forecasts.jsonl and it never places, sizes or vetoes
anything - same two prohibitions as core/screen.py.

It does not touch journal/screener-quota/ either. The quota counts subagent
batches and this spawns none; a rank cycle costs zero batches, which is most
of the point.

Since 2026-09-04 the filters in strategy/screener-filters.json are LIVE as a
pre-filter in core/screen.py prepare (load_filters, filters_fired and
prefilter live there and this module reuses them). The ranking itself stays
dormant: gnhf run 3's decision memo kept the Haiku tier and took only the
filters, because the formula's own escalation list is 13 to 14 of 15 sports
and esports coin flips.

Usage:
  python3 core/scan.py --hours 336 --limit 800 | python3 core/screen_rank.py rank
  python3 core/screen_rank.py rank --file work/scan.json
  python3 core/screen_rank.py rank --file work/scan.json --dry-run
Input:  scan.py candidate JSON lines on stdin or --file, exactly what
        core/screen.py prepare reads.
Output: prints the top-N rows by rank_score as JSON lines on stdout, appends
        one row per screened market to journal/screener.jsonl, and summarises
        on stderr. --dry-run writes nothing and prints a header instead.
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import screen  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The formula, named in the row's `model` field so the journal says what
# produced it. Bump the suffix if the score changes; the blob hash in
# prompt_rev only tracks the filter file.
MODEL_LABEL = "formula:mid-uncertainty-2p1p-v1"

RANK_ERROR = ("no model answer: screen_rank formula mode. divergence is "
              "undefined without a belief; the ranking is in rank_score "
              "(2p(1-p) on the recorded mids)")

# Used when strategy/screener-filters.json is missing or malformed. Deliberately
# empty of title patterns: a formula that silently invents its own exclusions is
# worse than one that escalates a spread market and is seen to.
def rank_score(mids):
    """2p(1-p) on the recorded mids, or None if the mids are unusable.

    This is screen_replay.mid_null_surprise read forward instead of back: the
    surprise the market's own price expects to realize, which on a binary
    market is 2p(1-p) and is maximal at 0.50. Kept as its own function so the
    formula in `model` is one place in the code.
    """
    if not isinstance(mids, dict) or not mids:
        return None
    try:
        vals = [float(v) for v in mids.values()]
    except (TypeError, ValueError):
        return None
    if not vals or any(v < 0.0 or v > 1.0 for v in vals):
        return None
    p = max(vals)
    return round(2.0 * p * (1.0 - p), 6)


def rank_rows(pool, lane_of, ts, prompt_rev, batch_id, compiled, spec):
    """One journal row per screened market, in core/screen.py's row schema."""
    rows = []
    for c in pool:
        mids = screen.mids_of(c)
        row = screen.row_base(c, mids, ts, MODEL_LABEL, prompt_rev, batch_id)
        row["screen_error"] = RANK_ERROR
        # probs IS the mids: the formula's estimate for a market is its price.
        row["probs"] = dict(mids) if mids else None
        row["rank_score"] = rank_score(mids)
        row["filtered_by"] = screen.filters_fired(c, mids, compiled, spec)
        row["stratum"] = lane_of.get(str(c.get("market_id")))
        row["reason"] = (f"mid uncertainty {row['rank_score']}"
                         if row["rank_score"] is not None else "no usable mids")
        if row["filtered_by"]:
            row["reason"] += f"; filtered by {', '.join(row['filtered_by'])}"
        rows.append(row)
    return rows


def escalate(rows, top_n):
    """The rows a researcher would work, highest rank_score first.

    Ties break on market_id so the list is reproducible from the journal, the
    same reason screen.stratify sorts on market_id inside every stratum.
    """
    live = [r for r in rows if r["rank_score"] is not None and not r["filtered_by"]]
    live.sort(key=lambda r: (-r["rank_score"], r["market_id"]))
    return live[:top_n]


def cmd_rank(args):
    cfg = screen.screener_config()
    if args.top_n is not None:
        cfg["top_n"] = max(1, args.top_n)

    candidates, n_bad = screen.read_candidates(args.file)
    if n_bad:
        print(f"screen_rank: {n_bad} input line(s) failed the candidate contract",
              file=sys.stderr)
    if not candidates:
        print("screen_rank: no valid candidates on input; nothing to rank",
              file=sys.stderr)
        return 0

    sizes = screen.strata_sizes()
    now = screen.utcnow()
    pool, lane_of, counts, dropped = screen.stratify(
        candidates, sizes, cfg["max_pool_after_strata"], now, screen.stamp(now))
    if n_bad:
        dropped["unparseable_input_line"] = n_bad
    if not pool:
        print("screen_rank: stratification left no markets to rank",
              file=sys.stderr)
        return 0

    compiled, spec = screen.load_filters()
    ts = screen.iso(now)
    # prompt_rev is the blob hash of the RULE FILE this run read, not of
    # screener-prompt.md: that brief is a model instruction and no model ran.
    prompt_rev = screen.blob_rev(screen.FILTERS_FILE)
    batch_id = f"rank-{screen.stamp(now)}"
    rows = rank_rows(pool, lane_of, ts, prompt_rev, batch_id, compiled, spec)
    escalated = escalate(rows, cfg["top_n"])

    n_filtered = sum(1 for r in rows if r["filtered_by"])
    n_unscorable = sum(1 for r in rows if r["rank_score"] is None)
    by_filter = {}
    for r in rows:
        for name in r["filtered_by"]:
            by_filter[name] = by_filter.get(name, 0) + 1

    header = {"mode": "rank", "model": MODEL_LABEL, "ts": ts,
              "batch_id": batch_id, "prompt_rev": prompt_rev,
              "filters_file": str(screen.FILTERS_FILE.relative_to(ROOT)),
              "filters_loaded": [n for n, _ in compiled],
              "screened_pool": len(rows), "candidates_in": len(candidates),
              "strata": screen.recount_selected(pool, lane_of, counts),
              "dropped_by_reason": dropped, "filtered_rows": n_filtered,
              "filtered_by_reason": by_filter, "unscorable_rows": n_unscorable,
              "escalated": len(escalated), "top_n": cfg["top_n"]}

    if args.dry_run:
        header["dry_run"] = True
        header["escalation"] = [
            {"rank": i, "market_id": r["market_id"], "question": r["question"],
             "rank_score": r["rank_score"], "mids": r["mids"],
             "stratum": r["stratum"]}
            for i, r in enumerate(escalated, 1)]
        print(json.dumps(header, indent=2, ensure_ascii=False))
        print(f"screen_rank: dry run - would rank {len(rows)} of "
              f"{len(candidates)} candidates, filter {n_filtered}, escalate "
              f"{len(escalated)}; journal/screener.jsonl untouched",
              file=sys.stderr)
        return 0

    with screen.LOG_FILE.open("a") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    for row in escalated:
        print(json.dumps(row))
    print(f"screen_rank: ranked {len(rows)} markets, filtered {n_filtered} "
          f"({by_filter or 'none'}), escalated {len(escalated)}; appended to "
          f"journal/screener.jsonl as model={MODEL_LABEL}, prompt_rev="
          f"{prompt_rev[:8]}. No subagents, no quota spent.", file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rank", help="stratify and rank by mid uncertainty; no "
                                    "model, no subagents, no quota")
    r.add_argument("--file", default=None,
                   help="read scan candidates from this file instead of stdin")
    r.add_argument("--dry-run", action="store_true",
                   help="print the header and the escalation list; write nothing")
    r.add_argument("--top-n", type=int, default=None,
                   help="override config screener.top_n")
    r.set_defaults(func=cmd_rank)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
