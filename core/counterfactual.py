#!/usr/bin/env python3
"""Mechanical counterfactual ledger: the trades Phil's gates declined.

PROTECTED CORE - the trading agent must not edit files under core/.

journal/forecasts.jsonl records a belief (est_prob) and the book at record
time for every researched market, including the ones a gate declined
(skip_reason != "bet"). Nothing in that record says what those declines
cost or saved. This tool answers that mechanically, once, for every settled
declined row, so the answer stops depending on a table re-summed by hand.

`ledger` builds the counterfactual trade each declined row implies:

  side   the sign of est_prob - market_prob_at_record (the model's own
         disagreement with the market; no threshold, no policy)
  stake  flat $5
  fill   replay.fill, so the protected caps and the honest CLOB fill model
         (Yes at the recorded ask, No at 1 - recorded bid) apply unchanged
  edge   the realizable, fill-price edge the hand table uses:
         Yes: est_prob - best_ask;  No: best_bid - est_prob

Two frames, kept apart on purpose. est_prob, the book and replay.fill all
refer to the RECORDED OUTCOME TOKEN, which on some rows is the market's
"No" token; the playbook's table and every reported side split
speak in question frame, where "yes" means the model bet the question
resolves Yes (or that the named outcome happens). Rows carry both: `side`
and `price` are token-frame, as fill() needs them; `market_side` and
`market_outcome` are question-frame, and are what the splits and the
reconcile diff use. Conflating the two silently flips the side and the
result on every No-token row.

A row replay.fill refuses (entry outside the protected price band, banned
question pattern, too close to resolution, no book on the traded side) is
listed with its refusal rather than dropped, because a gate that only ever
declined unfillable rows saved nothing.

Universe: every SETTLED row with skip_reason != "bet". This is wider than
replay.load_rows(), deliberately: that helper drops superseded rows and
rows with no ask, while the hand-kept playbook table grades a row on its
ORIGINAL record-time book even when a later belief superseded it (its BoK
convention). Superseded rows are counted and flagged, never hidden.

Splits: by skip_reason, by side, by category, and by the playbook's named
sub-classes (narrative, trend-extrapolation, countable-metric,
fact-finality, same-day weather), attached when the row's own note or the
retro prose written around that row's id names one. Rows nothing names are
reported as (unlabelled), with the count.

Each split reports n, W/L, pnl, brier_delta and the walk-forward read: the
group's rows cut into K contiguous time folds exactly as replay.py cuts
them, with the counterfactual pnl landing in each fold. A total carried by
one late cluster of wins shows up as one fat fold, not as a verdict.
brier_delta = mean Brier(est_prob) - mean Brier(market at record) over the
declined rows: a gate skipping rows whose beliefs BEAT the market
(negative) is a different problem from one skipping rows whose beliefs
lose to it (positive), and the pnl column alone cannot tell them apart.

`reconcile` diffs that mechanical ledger against the hand-kept table under
"Outside-view veto: settled counterfactual ledger" in strategy/playbook.md
(markdown rows plus the batches written up in prose only). Rows are matched
by forecast id where the playbook names one, else by question text and
date. It prints hand rows with no ledger row, settled outside-view-veto
ledger rows the hand table never entered, matched rows whose side, edge,
result or pnl disagree, both totals and the difference. It does not correct
the playbook; the diff is the output.

The hand table stakes 1u per row, this ledger stakes $5, so reconcile
compares pnl in units (ledger pnl / 5).

Usage: python3 core/counterfactual.py ledger    [--folds K] [--json] [--rows]
                                             [--skip-reason NAME]
       python3 core/counterfactual.py reconcile [--json]
"""
import argparse
import collections
import json
import math
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import replay
import screen_replay  # noqa: E402  (protected sibling: fill model, caps, parsing)

ROOT = replay.ROOT
PLAYBOOK = ROOT / "strategy" / "playbook.md"
RETRO_DIR = ROOT / "journal" / "retros"
STAKE_USD = 5.0
# market -> gamma event, from the cache core/screen_replay.py events fills.
# Snapshots of one event are one observation; `evts` counts them once.
EVENT_OF, _ = screen_replay.load_event_cache()

# The pre-registered carve-out bar for a veto sub-class (operator notes
# 2026-09-04 ~23:20Z, amended 2026-09-06 to require independent events after
# five GTA VI snapshots met the row count on one event).
BAR = {"subclass": "countable-metric", "min_rows": 5, "min_events": 3,
       "min_positive_held_out_folds": 3}
HAND_STAKE_U = 1.0

# Sub-classes the playbook names, most specific first: a row gets the first
# one its note or its retro prose mentions.
SUBCLASSES = (
    ("countable-metric", r"countable[- ]metric|cumulative[- ]count|dated (?:primary )?count"),
    ("same-day weather", r"same[- ]day weather"),
    ("fact-finality", r"fact[- ]finality"),
    ("trend-extrapolation", r"trend[- ]extrapolat"),
    ("narrative", r"narrative"),
)
SUBCLASS_RE = [(name, re.compile(pat, re.I)) for name, pat in SUBCLASSES]
UNLABELLED = "(unlabelled)"
# Retro prose counts as naming a sub-class only near the row id, not
# anywhere in the file: a deep retro grades a dozen unrelated rows.
RETRO_WINDOW = 600
ID_RE = re.compile(r"\b[0-9a-f]{12}\b")


# ---------------------------------------------------------------- ledger

def candidates():
    """Every settled declined forecast, in record-time order."""
    rows = []
    with open(replay.FORECASTS) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("status") not in ("won", "lost"):
                continue
            if r.get("skip_reason") == "bet":
                continue
            rows.append(r)
    rows.sort(key=lambda r: (r["ts"], r["id"]))
    return rows


def realizable_edge(r, side):
    """Fill-price edge on the model's side: est - ask, or bid - est."""
    if side == "yes":
        ask = r.get("best_ask_at_record")
        return None if ask is None else round(r["est_prob"] - ask, 4)
    bid = r.get("best_bid_at_record")
    return None if bid is None else round(bid - r["est_prob"], 4)


def market_frame(side, token, won):
    """Token-frame side/result -> question frame ("yes" = the question
    resolves Yes, or the named outcome happens)."""
    flip = token == "No"
    q_side = None if side is None else (
        ("no" if side == "yes" else "yes") if flip else side)
    return q_side, ("Yes" if bool(won) != flip else "No")


def refusal(r, side):
    """Why replay.fill refused this side, checked in fill()'s own order."""
    if any(p.search(r["question"]) for p in replay._BANNED):
        return "banned question pattern"
    try:
        minutes = (replay._parse_ts(r["end_date"])
                   - replay._parse_ts(r["ts"])).total_seconds() / 60
    except (KeyError, TypeError, ValueError):
        minutes = None
    if minutes is not None and minutes < replay.PROTECTED["min_minutes_to_resolution"]:
        return f"{minutes:.0f}m to resolution, under min_minutes_to_resolution"
    if side == "yes":
        price = r.get("best_ask_at_record")
        if price is None:
            return "no ask at record time"
    else:
        bid = r.get("best_bid_at_record")
        if bid is None:
            return "no bid at record time"
        price = round(1 - bid, 4)
    lo, hi = replay.PROTECTED["min_entry_price"], replay.PROTECTED["max_entry_price"]
    if not lo <= price <= hi:
        return f"entry {price:.4f} outside [{lo}, {hi}]"
    return "refused by fill (unclassified)"


def retro_context():
    """id -> the retro prose written around each mention of that id."""
    ctx = collections.defaultdict(list)
    for path in sorted(RETRO_DIR.glob("*.md")):
        text = path.read_text()
        for m in ID_RE.finditer(text):
            ctx[m.group(0)].append(
                text[max(0, m.start() - RETRO_WINDOW):m.end() + RETRO_WINDOW])
    return ctx


def label_subclasses(rows):
    """Attach the playbook's sub-class label from the note or the retro."""
    ctx = retro_context()
    for row in rows:
        text = " ".join([row["note"] or ""] + ctx.get(row["id"], []))
        for name, pat in SUBCLASS_RE:
            if pat.search(text):
                row["subclass"] = name
                break


def build():
    """The mechanical counterfactual ledger, one entry per declined row."""
    out = []
    for r in candidates():
        mkt = replay.market_prob(r)
        won = 1 if r["status"] == "won" else 0
        row = {
            "id": r["id"], "ts": r["ts"], "category": r.get("category"),
            "market_id": str(r.get("market_id")),
            "event": screen_replay.cluster_of(str(r.get("market_id")), EVENT_OF),
            "skip_reason": r.get("skip_reason"), "question": r["question"],
            "note": r.get("note"), "est_prob": r["est_prob"],
            "market_prob": mkt, "token": r.get("outcome"), "won": won,
            "superseded": bool(r.get("superseded_by")), "subclass": None,
            "side": None, "market_side": None, "market_outcome": None,
            "edge": None, "price": None, "stake": None,
            "pnl": None, "bet_won": None, "refused": None,
        }
        row["market_outcome"] = market_frame(None, row["token"], won)[1]
        if mkt is None:
            row["refused"] = "no market price at record time"
        elif r["est_prob"] == mkt:
            row["refused"] = "no disagreement with the market"
        else:
            side = "yes" if r["est_prob"] > mkt else "no"
            row["side"] = side
            row["market_side"] = market_frame(side, row["token"], won)[0]
            row["edge"] = realizable_edge(r, side)
            filled = replay.fill(r, {"side": side, "stake_usd": STAKE_USD})
            if filled is None:
                row["refused"] = refusal(r, side)
            else:
                price, stake, pnl = filled
                row.update(price=price, stake=stake, pnl=round(pnl, 4),
                           bet_won=pnl > 0)
        out.append(row)
    label_subclasses(out)
    return out


def fold_pnl(rows, folds):
    """Counterfactual pnl per contiguous time fold, replay.py's own cut."""
    if not rows:
        return [], 0.0
    size = math.ceil(len(rows) / folds)
    chunks = [rows[i:i + size] for i in range(0, len(rows), size)]
    per = [round(sum(r["pnl"] or 0.0 for r in c), 2) for c in chunks]
    return per, round(sum(per[1:]), 2)


def stats(rows, folds):
    """n, W/L, pnl, brier_delta and the walk-forward read for one group."""
    traded = [r for r in rows if r["pnl"] is not None]
    scored = [r for r in rows if r["market_prob"] is not None]
    per, held = fold_pnl(rows, folds)
    brier = None
    if scored:
        n = len(scored)
        ba = sum((r["est_prob"] - r["won"]) ** 2 for r in scored) / n
        bm = sum((r["market_prob"] - r["won"]) ** 2 for r in scored) / n
        brier = round(ba - bm, 4)
    return {
        "n_rows": len(rows), "n_trades": len(traded),
        "n_events": len({r["event"] for r in rows}),
        "n_refused": len(rows) - len(traded),
        "wins": sum(1 for r in traded if r["bet_won"]),
        "losses": sum(1 for r in traded if not r["bet_won"]),
        "pnl": round(sum(r["pnl"] for r in traded), 2),
        "staked": round(sum(r["stake"] for r in traded), 2),
        "brier_delta": brier, "n_brier": len(scored),
        "fold_pnl": per, "held_out_pnl": held,
    }


def group_by(rows, key, folds):
    """Ordered {group: stats}, biggest group first."""
    buckets = collections.defaultdict(list)
    for r in rows:
        buckets[key(r)].append(r)
    out = [(k, stats(v, folds)) for k, v in buckets.items()]
    out.sort(key=lambda kv: -kv[1]["n_rows"])
    return out


def bar_report(rep):
    """Is the pre-registered sub-class carve-out bar met? Mechanical, no judgment."""
    s = next((g for g in rep["groups"]["subclass"] if g["group"] == BAR["subclass"]), None)
    if s is None:
        return {"bar": BAR, "met": False, "n_rows": 0, "n_events": 0,
                "positive_held_out_folds": 0, "brier_delta": None, "pnl": 0.0}
    held = [x for x in s["fold_pnl"][1:] if x is not None]
    pos = sum(1 for x in held if x > 0)
    met = (s["n_rows"] >= BAR["min_rows"] and s["n_events"] >= BAR["min_events"]
           and s["brier_delta"] is not None and s["brier_delta"] < 0
           and s["pnl"] > 0 and pos >= BAR["min_positive_held_out_folds"])
    return {"bar": BAR, "met": met, "n_rows": s["n_rows"], "n_events": s["n_events"],
            "positive_held_out_folds": pos, "held_out_folds": len(held),
            "brier_delta": s["brier_delta"], "pnl": s["pnl"]}


def ledger_report(rows, folds):
    groups = {
        "skip_reason": group_by(rows, lambda r: r["skip_reason"] or "(none)", folds),
        "side (question frame)":
            group_by(rows, lambda r: r["market_side"] or "(no side)", folds),
        "category": group_by(rows, lambda r: r["category"] or "(none)", folds),
        "subclass": group_by(rows, lambda r: r["subclass"] or UNLABELLED, folds),
    }
    rep = {
        "stake_usd": STAKE_USD, "folds": folds,
        "overall": stats(rows, folds),
        "superseded_rows": sum(1 for r in rows if r["superseded"]),
        "groups": {k: [dict(group=g, **s) for g, s in v] for k, v in groups.items()},
        "refusals": [{"id": r["id"], "ts": r["ts"],
                      "skip_reason": r["skip_reason"], "side": r["side"],
                      "market_side": r["market_side"], "edge": r["edge"],
                      "refused": r["refused"], "question": r["question"]}
                     for r in rows if r["refused"]],
        "rows": rows,
    }
    rep["bar"] = bar_report(rep)
    return rep


def _fold_cols(s, folds):
    cells = list(s["fold_pnl"]) + [None] * (folds - len(s["fold_pnl"]))
    return " ".join("       -" if c is None else f"{c:>+8.2f}" for c in cells[:folds])


def print_ledger(rep, folds, show_rows):
    o = rep["overall"]
    print(f"counterfactual ledger: {o['n_rows']} settled declined forecasts, "
          f"${STAKE_USD:.0f} flat on the model's side of the market")
    print(f"  {o['n_trades']} fillable counterfactual trades, {o['n_refused']} refused, "
          f"{rep['superseded_rows']} superseded rows kept (replay.load_rows drops those)")
    print("  sides are question frame: yes = the model bet the question resolves Yes "
          "(fills still use the recorded token)")
    print(f"  overall: {o['wins']}W/{o['losses']}L  pnl {o['pnl']:+.2f}  "
          f"staked {o['staked']:.2f}  brier_delta {o['brier_delta']:+.4f} over {o['n_brier']} rows")
    print()
    head = (f"{'group':<26} {'rows':>4} {'evts':>4} {'trd':>4} {'W':>3} {'L':>3} {'pnl':>9} "
            f"{'dBrier':>8} | walk-forward pnl by fold (f0 = replay.py train-only) "
            f"| {'held-out':>9}")
    for name, entries in rep["groups"].items():
        print(f"-- by {name}")
        print(head)
        for s in entries:
            bd = "       -" if s["brier_delta"] is None else f"{s['brier_delta']:>+8.4f}"
            print(f"{s['group'][:26]:<26} {s['n_rows']:>4} {s['n_events']:>4} {s['n_trades']:>4} "
                  f"{s['wins']:>3} {s['losses']:>3} {s['pnl']:>+9.2f} {bd} | "
                  f"{_fold_cols(s, folds)} | {s['held_out_pnl']:>+9.2f}")
        print()
    b = rep["bar"]
    print(f"-- pre-registered carve-out bar for {b['bar']['subclass']}: "
          f"{'MET' if b['met'] else 'not met'}")
    print(f"   rows {b['n_rows']} (need {b['bar']['min_rows']}), independent events "
          f"{b['n_events']} (need {b['bar']['min_events']}), brier_delta "
          f"{b['brier_delta']} (need < 0), pnl {b['pnl']:+.2f} (need > 0), positive "
          f"held-out folds {b['positive_held_out_folds']} of {b.get('held_out_folds', 0)} "
          f"(need {b['bar']['min_positive_held_out_folds']})")
    print("   evts counts gamma events via journal/screener-events.jsonl; an unmapped "
          "market counts as its own event, so evts is an upper bound until "
          "`screen_replay.py events` has mapped it")
    print()
    unl = next((s for s in rep["groups"]["subclass"] if s["group"] == UNLABELLED), None)
    if unl:
        print(f"no sub-class label could be attached to {unl['n_rows']} of "
              f"{rep['overall']['n_rows']} rows: neither the row note nor the retro "
              f"prose around its id names one of {', '.join(n for n, _ in SUBCLASSES)}.")
        print()
    print(f"-- refusals ({len(rep['refusals'])}): rows the fill model would not take")
    for r in rep["refusals"]:
        edge = "     -" if r["edge"] is None else f"{r['edge']:>+6.3f}"
        print(f"  {r['id']} {r['ts'][:10]} {(r['market_side'] or '-'):>3} edge {edge}  "
              f"{(r['skip_reason'] or '-'):<20} {r['refused']}")
    if show_rows:
        print()
        print(f"-- rows ({len(rep['rows'])})")
        for r in rep["rows"]:
            pnl = "      -" if r["pnl"] is None else f"{r['pnl']:>+7.2f}"
            edge = "     -" if r["edge"] is None else f"{r['edge']:>+6.3f}"
            print(f"  {r['id']} {r['ts'][:10]} {(r['market_side'] or '-'):>3} edge {edge} "
                  f"pnl {pnl}  {(r['subclass'] or '-'):<20} {r['question'][:44]}")


# ------------------------------------------------------------- reconcile

SECTION = "## Outside-view veto: settled counterfactual ledger"
STATED_RE = re.compile(
    r"Totals now (\d+) realizable trades,\s*(\d+)W/(\d+)L, net ([-+−–][\d.]+)u")
# A prose batch names the id, then its side, edge, result and bolded P&L.
PROSE_RE = re.compile(
    r"\(`?([0-9a-f]{12})`?[^)]*\)(.{0,700}?)\*\*([-+−–][\d.]+)u?\*\*", re.S)
PROSE_SIDE = re.compile(r"side (Yes|No)")
PROSE_EDGE = re.compile(r"edge \+?([\d.]+)")
PROSE_RESULT = re.compile(r"resolved (Yes|No)")
BATCH_DATE = re.compile(r"\*\*(\d{4}-\d{2}-\d{2})[^*]*update")


def _num(s):
    s = s.replace("−", "-").replace("–", "-").replace("~", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_playbook():
    """The hand-kept table: markdown rows plus the prose-only batches."""
    lines = PLAYBOOK.read_text().splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.startswith(SECTION))
    except StopIteration:
        sys.exit(f"{PLAYBOOK} has no section {SECTION!r}")
    end = next((i for i, ln in enumerate(lines[start + 1:], start + 1)
                if ln.startswith("## ")), len(lines))
    section, entries, prose, batch = lines[start:end], [], [], None
    for off, ln in enumerate(section):
        if ln.startswith("|") and ln.count("|") >= 6:
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if cells[0].lower() == "row" or set(cells[0]) <= set("-: "):
                continue
            pnl = cells[5].replace("*", "").strip()
            m = ID_RE.search(cells[0])
            entries.append({
                "id": m.group(0) if m else None, "label": cells[0],
                "side": cells[2].strip().lower(), "edge": _num(cells[3]),
                "result": cells[4].replace("*", "").strip(),
                "pnl": None if "non-trade" in pnl else _num(pnl),
                "source": "table", "line": start + off + 1, "batch_date": batch,
            })
            continue
        m = BATCH_DATE.search(ln)
        if m:
            batch = m.group(1)
        prose.append((start + off + 1, batch, ln))
    seen = {e["id"] for e in entries if e["id"]}
    text = "\n".join(ln for _, _, ln in prose)
    offsets = []
    pos = 0
    for lineno, bdate, ln in prose:
        offsets.append((pos, lineno, bdate))
        pos += len(ln) + 1
    for m in PROSE_RE.finditer(text):
        rid, body, pnl = m.group(1), m.group(2), m.group(3)
        if rid in seen:
            continue
        side, edge, result = (PROSE_SIDE.search(body), PROSE_EDGE.search(body),
                              PROSE_RESULT.search(body))
        if not (side and edge and result):
            continue  # a mention, not a graded row
        seen.add(rid)
        lineno, bdate = next((ln, bd) for off, ln, bd in reversed(offsets)
                             if off <= m.start())
        entries.append({
            "id": rid, "label": "(prose)", "side": side.group(1).lower(),
            "edge": _num(edge.group(1)), "result": result.group(1),
            "pnl": _num(pnl), "source": "prose", "line": lineno,
            "batch_date": bdate,
        })
    stated = None
    for m in STATED_RE.finditer(re.sub(r"\s+", " ", "\n".join(section))):
        stated = {"trades": int(m.group(1)), "wins": int(m.group(2)),
                  "losses": int(m.group(3)), "pnl": _num(m.group(4))}
    return entries, stated, {"section_lines": len(section), "ids_seen": len(seen)}


def _tokens(label):
    return [w for w in re.findall(r"[A-Za-z0-9]+", label.lower()) if len(w) >= 4]


def match_by_text(entry, rows):
    """Fallback match for a hand row the playbook gave no id: question words
    plus the batch date."""
    toks = _tokens(re.sub(r"\([^)]*\)", "", entry["label"]))
    if len(toks) < 2:
        return None
    hits = [r for r in rows if all(t in r["question"].lower() for t in toks)]
    if entry["batch_date"]:
        near = [r for r in hits if abs(_days(r["ts"], entry["batch_date"])) <= 3]
        hits = near or hits
    return hits[0] if len(hits) == 1 else None


def _days(ts, date):
    a, b = replay._parse_ts(ts), replay._parse_ts(date + "T00:00:00Z")
    return (a - b).total_seconds() / 86400


def reconcile_report(rows, folds):
    entries, stated, meta = parse_playbook()
    by_id = {r["id"]: r for r in rows}
    matched, missing, by_text = [], [], 0
    for e in entries:
        row = by_id.get(e["id"]) if e["id"] else None
        if row is None:
            row = match_by_text(e, rows)
            if row is not None:
                by_text += 1
        if row is None:
            missing.append(e)
        else:
            matched.append((e, row))
    entered = {r["id"] for _, r in matched}
    section = PLAYBOOK.read_text()
    never = [{"id": r["id"], "ts": r["ts"], "edge": r["edge"],
              "pnl": None if r["pnl"] is None else round(r["pnl"] / STAKE_USD, 2),
              "side": r["market_side"], "refused": r["refused"], "outcome": r["market_outcome"],
              "named_in_playbook": r["id"] in section,
              "question": r["question"]}
             for r in rows
             if r["skip_reason"] == "outside-view-veto" and r["id"] not in entered]
    diffs = []
    for e, r in matched:
        d = {}
        led_pnl = None if r["pnl"] is None else round(r["pnl"] / STAKE_USD, 2)
        if e["side"] != (r["market_side"] or ""):
            d["side"] = (e["side"], r["market_side"])
        if e["edge"] is not None and r["edge"] is not None and abs(e["edge"] - r["edge"]) > 0.005:
            d["edge"] = (e["edge"], r["edge"])
        elif (e["edge"] is None) != (r["edge"] is None):
            d["edge"] = (e["edge"], r["edge"])
        if e["result"] != r["market_outcome"]:
            d["result"] = (e["result"], r["market_outcome"])
        if e["pnl"] is None or led_pnl is None:
            if e["pnl"] is not None or led_pnl is not None:
                d["pnl"] = (e["pnl"], led_pnl)
        elif abs(e["pnl"] - led_pnl) > 0.02:
            d["pnl"] = (e["pnl"], led_pnl)
        if d:
            diffs.append({"id": r["id"], "label": e["label"], "line": e["line"],
                          "refused": r["refused"], "fields": d})
    hand_trades = [e for e in entries if e["pnl"] is not None]
    hand = {"rows": len(entries), "trades": len(hand_trades),
            "wins": sum(1 for e in hand_trades if e["pnl"] > 0),
            "losses": sum(1 for e in hand_trades if e["pnl"] < 0),
            "pnl": round(sum(e["pnl"] for e in hand_trades), 2)}
    veto = [r for r in rows if r["skip_reason"] == "outside-view-veto"]
    s = stats(veto, folds)
    led = {"rows": s["n_rows"], "trades": s["n_trades"], "wins": s["wins"],
           "losses": s["losses"], "pnl": round(s["pnl"] / STAKE_USD, 2)}
    return {"hand": hand, "hand_stated": stated, "ledger_veto": led,
            "difference": {k: round(led[k] - hand[k], 2) for k in
                           ("rows", "trades", "wins", "losses", "pnl")},
            "matched": len(matched), "matched_by_text": by_text,
            "missing_from_ledger": missing, "never_entered": never,
            "field_diffs": diffs, "meta": meta}


def print_reconcile(rep):
    h, ledg, d, st = rep["hand"], rep["ledger_veto"], rep["difference"], rep["hand_stated"]
    print("reconcile: hand-kept playbook table vs mechanical counterfactual ledger")
    print(f"  parsed {h['rows']} hand rows ({h['trades']} graded trades) from "
          f"{PLAYBOOK.relative_to(ROOT)}; matched {rep['matched']} to ledger rows "
          f"({rep['matched_by_text']} by question text + date)")
    if st:
        ok = (st["trades"], st["wins"], st["losses"], st["pnl"]) == (
            h["trades"], h["wins"], h["losses"], h["pnl"])
        print(f"  parser check vs the table's own last stated total "
              f"({st['trades']} trades, {st['wins']}W/{st['losses']}L, {st['pnl']:+.2f}u): "
              f"{'match' if ok else 'MISMATCH - the hand total does not re-sum'}")
    print()
    print(f"A. hand rows with no ledger row ({len(rep['missing_from_ledger'])})")
    for e in rep["missing_from_ledger"]:
        print(f"   playbook:{e['line']} {e['id'] or '(no id)'} {e['label'][:60]}")
    print()
    print(f"B. settled outside-view-veto ledger rows the hand table never entered "
          f"({len(rep['never_entered'])})")
    for r in rep["never_entered"]:
        edge = "     -" if r["edge"] is None else f"{r['edge']:>+6.3f}"
        pnl = "      -" if r["pnl"] is None else f"{r['pnl']:>+7.2f}u"
        why = r["refused"] or ("named elsewhere in the section"
                               if r["named_in_playbook"] else "not named in the section")
        print(f"   {r['id']} {r['ts'][:10]} {(r['side'] or '-'):>3} edge {edge} "
              f"pnl {pnl}  {why[:34]:<34} {r['question'][:36]}")
    print()
    print(f"C. rows in both that differ ({len(rep['field_diffs'])})")
    for x in rep["field_diffs"]:
        fields = "  ".join(f"{k}: hand {v[0]} -> ledger {v[1]}" for k, v in x["fields"].items())
        print(f"   {x['id']} playbook:{x['line']} {x['label'][:34]:<34} {fields}")
        if x["refused"]:
            print(f"      ledger refusal: {x['refused']}")
    print()
    print("totals (1u basis: ledger pnl / 5)")
    print(f"  hand table        {h['trades']:>4} trades  {h['wins']:>3}W/{h['losses']:<3}L  "
          f"{h['pnl']:>+8.2f}u   ({h['rows']} rows)")
    print(f"  ledger, veto rows {ledg['trades']:>4} trades  "
          f"{ledg['wins']:>3}W/{ledg['losses']:<3}L  {ledg['pnl']:>+8.2f}u   ({ledg['rows']} rows)")
    print(f"  difference        {d['trades']:>+4} trades  {d['wins']:>+3}W/{d['losses']:<+3}L  "
          f"{d['pnl']:>+8.2f}u   ({d['rows']:+} rows)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    led = sub.add_parser("ledger", help="the counterfactual trade every declined row implies")
    led.add_argument("--folds", type=int, default=5)
    led.add_argument("--json", action="store_true")
    led.add_argument("--rows", action="store_true", help="list every ledger row")
    led.add_argument("--skip-reason", metavar="NAME",
                     help="restrict the ledger to one gate, e.g. outside-view-veto")
    rec = sub.add_parser("reconcile", help="diff the hand-kept playbook table against it")
    rec.add_argument("--folds", type=int, default=5)
    rec.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.folds < 2:
        sys.exit("--folds must be >= 2")
    rows = build()
    if a.cmd == "ledger":
        if a.skip_reason:
            rows = [r for r in rows if r["skip_reason"] == a.skip_reason]
            if not rows:
                sys.exit(f"no settled declined rows with skip_reason {a.skip_reason!r}")
        rep = ledger_report(rows, a.folds)
        if a.json:
            print(json.dumps(rep, indent=1))
        else:
            print_ledger(rep, a.folds, a.rows)
        return
    rep = reconcile_report(rows, a.folds)
    if a.json:
        print(json.dumps(rep, indent=1))
    else:
        print_reconcile(rep)


if __name__ == "__main__":
    main()
