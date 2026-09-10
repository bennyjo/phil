#!/usr/bin/env python3
"""Scheduled-release calendar: agency schedules -> watchlist calendar entries.

PROTECTED CORE - the trading agent must not edit files under core/.

DORMANT. Nothing calls this file: not CYCLE.md, not core/watch.py, not the
cloud routines. It reads a hard-coded release table plus live gamma and it
PRINTS. It never writes strategy/watchlist.json, never writes any journal, and
never touches the CLOB order book. Switching it on is an operator act, and
journal/lane-coverage-decision.md carries the bar and the merge step.

Why it exists: journal/screener-value-decision.md found scheduled economic
prints to be one of two families where research beats the price, and
journal/lane-coverage-decision.md found that the agent's calendar tier fires
from hand-written entries only, so a release nobody wrote down is a release
nobody watched. Release dates are public months ahead. This turns that public
schedule into the exact entry shape core/watch.py already reads.

Not named core/calendar.py: every core script puts core/ on sys.path[0], and
a file with that name answers the standard library's `import calendar`, which
`_strptime` needs - core/validate.py then dies on its first strptime.
Verified 2026-09-10, then renamed.

Usage:
  python3 core/release_calendar.py releases [--weeks 8] [--json]
      The scheduled official releases inside the horizon, from the table
      below: agency, series, release time in UTC, source URL, read date.
  python3 core/release_calendar.py match [--weeks 8] [--max-lag-days 21] [--json]
      Each upcoming release joined to the OPEN gamma markets that resolve on
      it, with the market's mid, liquidity, end date, and the lag from the
      release to the end date.
  python3 core/release_calendar.py emit --lead <hours> [--weeks 8] [--window-min 45]
      One watchlist calendar entry per matched release, fire_at at the release
      time minus <hours>. The JSON array goes to stdout and the header to
      stderr, so `emit --lead 48 > entries.json` is a valid merge source.

A market resolves on a release when three tests pass, all on gamma title and
slug: the agent's own family mapper (strategy/screener-value.json, loaded
through core/screen_value.py) calls it an econ print; the playbook's
Mechanical-econ carve-out property 1 holds (a named official series or policy
decision, a numeric or directional criterion, no company-event shape); and the
release's own series pattern fires. Of the releases that then sit at or before
the market's end date, the one whose reference month the title names wins, and
failing that the nearest one.

Times. Every release_utc below is an explicit UTC instant, so there is no
timezone database in the loop. The DATES all come from the source pages. The
TIMES do not all: the BLS and BEA schedule pages state 08:30 America/New_York
per release (12:30Z on EDT dates, 13:30Z from 2026-11-01, when US DST ends),
but the Fed, ECB and BoE calendar pages give dates only, so the FOMC statement
at 14:00 America/New_York, the ECB decision at 14:15 Europe/Berlin and Bank
Rate at 12:00 Europe/London are each the agency's standing publication time
and not a per-date reading. At the leads this tool is meant for, days rather
than minutes, that distinction does not move a fire_at into the wrong day; at
a sub-hour lead it would, so do not use one.

Network: gamma only, read-only, sequential and paced, one page of 100 at a
time under --max-pages. `releases` makes no request at all.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pmapi  # noqa: E402
import screen_value as sv  # noqa: E402

ECON_FAMILY = "econ print"
ECON_TAG_ID = 100328          # gamma tag "economy"; 96.7% of the lane, see memo
PAGE = 100
SLEEP_S = 0.25
MAX_PAGES = 12                # 1,200 open markets is the whole econ tag today
MAX_LAG_DAYS = 21             # release -> end date; wider is a yearly market
PRE_GRACE_H = 36              # gamma end dates run EARLY of the print they
                              # settle: August CPI ends 03:59Z on release day
                              # (-8.5h), the September unemployment brackets
                              # 08:30Z (-4.0h), the ECB pair 11:59Z (-0.3h).
                              # Same-series releases are a month apart, so a
                              # day and a half of slack cannot cross two.
WATCH_MAX_CALENDAR = 10       # core/watch.py MAX_CALENDAR
WATCH_WINDOW_MIN = 5          # core/watch.py clamps price_moves to 5..60 and
WATCH_WINDOW_MAX = 60         # calendar to 1..180; emit stays inside both

# --- the release table -----------------------------------------------------
# Read 2026-09-10. bea.gov, federalreserve.gov, ecb.europa.eu and
# bankofengland.co.uk answered a plain HTTPS GET from this machine and the
# dates below are parsed from those pages. bls.gov returns HTTP 403 to this
# machine's client, so the three BLS series were read from the same public
# schedule pages through a browser fetch on the same day; the URL is the
# authority either way. Refresh yearly: every agency publishes the next year
# in the autumn.
SOURCES = {
    ("BLS", "cpi"): ("https://www.bls.gov/schedule/news_release/cpi.htm",
                     "2026-09-10", "browser fetch (bls.gov 403s this client)"),
    ("BLS", "ppi"): ("https://www.bls.gov/schedule/news_release/ppi.htm",
                     "2026-09-10", "browser fetch (bls.gov 403s this client)"),
    ("BLS", "employment"): ("https://www.bls.gov/schedule/news_release/empsit.htm",
                            "2026-09-10", "browser fetch (bls.gov 403s this client)"),
    ("BEA", "gdp"): ("https://www.bea.gov/news/schedule", "2026-09-10", "fetched"),
    ("BEA", "pce"): ("https://www.bea.gov/news/schedule", "2026-09-10", "fetched"),
    ("FED", "fomc"): ("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
                      "2026-09-10", "fetched"),
    ("ECB", "ecb-decision"): (
        "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html",
        "2026-09-10", "fetched"),
    ("BOE", "boe-decision"): (
        "https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates",
        "2026-09-10", "fetched"),
}

# (agency, series, label, release_utc, reference period as the market names it)
RELEASES = [
    ("BLS", "ppi", "PPI, August 2026", "2026-09-10T12:30:00Z", "august"),
    ("ECB", "ecb-decision", "ECB monetary policy decision (Sep 9-10)",
     "2026-09-10T12:15:00Z", "september"),
    ("BLS", "cpi", "CPI, August 2026", "2026-09-11T12:30:00Z", "august"),
    ("FED", "fomc", "FOMC decision (Sep 15-16, with projections)",
     "2026-09-16T18:00:00Z", "september"),
    ("BOE", "boe-decision", "Bank of England Bank Rate (September MPC)",
     "2026-09-17T11:00:00Z", "september"),
    ("BEA", "gdp", "GDP, Q2 2026 third estimate", "2026-09-30T12:30:00Z", "q2"),
    ("BEA", "pce", "Personal Income and Outlays (PCE), August 2026",
     "2026-09-30T12:30:00Z", "august"),
    ("BLS", "employment", "Employment Situation, September 2026",
     "2026-10-02T12:30:00Z", "september"),
    ("BLS", "cpi", "CPI, September 2026", "2026-10-14T12:30:00Z", "september"),
    ("BLS", "ppi", "PPI, September 2026", "2026-10-15T12:30:00Z", "september"),
    ("FED", "fomc", "FOMC decision (Oct 27-28)", "2026-10-28T18:00:00Z", "october"),
    ("BEA", "gdp", "GDP, Q3 2026 advance estimate", "2026-10-29T12:30:00Z", "q3"),
    ("BEA", "pce", "Personal Income and Outlays (PCE), September 2026",
     "2026-10-29T12:30:00Z", "september"),
    ("ECB", "ecb-decision", "ECB monetary policy decision (Oct 28-29)",
     "2026-10-29T13:15:00Z", "october"),
    ("BOE", "boe-decision", "Bank of England Bank Rate (November MPC, with MPR)",
     "2026-11-05T12:00:00Z", "november"),
    ("BLS", "employment", "Employment Situation, October 2026",
     "2026-11-06T13:30:00Z", "october"),
    ("BLS", "cpi", "CPI, October 2026", "2026-11-10T13:30:00Z", "october"),
    ("BLS", "ppi", "PPI, October 2026", "2026-11-13T13:30:00Z", "october"),
    ("BEA", "gdp", "GDP, Q3 2026 second estimate", "2026-11-25T13:30:00Z", "q3"),
    ("BEA", "pce", "Personal Income and Outlays (PCE), October 2026",
     "2026-11-25T13:30:00Z", "october"),
    ("BLS", "employment", "Employment Situation, November 2026",
     "2026-12-04T13:30:00Z", "november"),
    ("FED", "fomc", "FOMC decision (Dec 8-9, with projections)",
     "2026-12-09T19:00:00Z", "december"),
    ("BLS", "cpi", "CPI, November 2026", "2026-12-10T13:30:00Z", "november"),
    ("BLS", "ppi", "PPI, November 2026", "2026-12-15T13:30:00Z", "november"),
    ("BOE", "boe-decision", "Bank of England Bank Rate (December MPC)",
     "2026-12-17T12:00:00Z", "december"),
    ("ECB", "ecb-decision", "ECB monetary policy decision (Dec 16-17)",
     "2026-12-17T13:15:00Z", "december"),
    ("BEA", "gdp", "GDP, Q3 2026 third estimate", "2026-12-23T13:30:00Z", "q3"),
    ("BEA", "pce", "Personal Income and Outlays (PCE), November 2026",
     "2026-12-23T13:30:00Z", "november"),
]

# --- the market-side rules -------------------------------------------------
# One pattern per series in the table above, on title + slug. These are the
# same rules journal/lane-coverage-decision.md measured the lane with.
SERIES_RULES = {
    "cpi": r"\bcpi\b|consumer\s+price\s+index|\binflation\b",
    "ppi": r"\bppi\b|producer\s+price\s+index",
    "employment": (r"\bnonfarm\b|\bnfp\b|\bpayrolls?\b|jobs\s+report|"
                   r"\bunemployment\b|\bthe\s+us\s+(?:add|lose)\b|jobless\s+claims"),
    "gdp": r"\bgdp\b|gross\s+domestic\s+product",
    "pce": r"\bpce\b|personal\s+consumption\s+expenditure",
    "fomc": (r"\bfomc\b|fed\s+(?:interest\s+)?rate|fed\s+decision|federal\s+reserve|"
             r"fed\s+(?:rate\s+)?(?:cut|hike)|emergency\s+rate\s+cut|fed-decision|"
             r"\bfed\b.{0,60}(?:rates?|bps|basis\s+points?)"),
    "ecb-decision": r"\becb\b|european\s+central\s+bank",
    "boe-decision": r"bank\s+of\s+england|\bboe\b",
}
_SERIES = {k: re.compile(v, re.I) for k, v in SERIES_RULES.items()}

# Carve-out property 1, part 2: the criterion is a number with a comparator,
# bracket or unit.
NUMERIC = re.compile(
    r"\d+(?:\.\d+)?\s*%|\bbps\b|basis\s+points?|"
    r"\bbetween\s+[-+]?\d|\bat\s+least\s+[-+]?\d|\bor\s+(?:more|less|higher|lower|above|below)\b|"
    r"\b(?:above|below|over|under|exceed|greater\s+than|less\s+than)\s+[-+]?\d|"
    r"\bno\s+change\b|\bstay\s+flat\b|\bunchanged\b|"
    r"\b\d+(?:\.\d+)?\s*(?:k|thousand|million|bn|billion)\b|"
    r"\b(?:increase|decrease|rise|fall)\s+by\s+[-+]?\d|"
    r"\b\d+\s+(?:rate\s+)?(?:cut|hike)s?\b|\b(?:cut|hike)\s+(?:by\s+)?\d",
    re.I)
# A policy decision may state its criterion as the DIRECTION of a published
# rate, which is as interpretation-free as a bracket.
POLICY_SERIES = {"fomc", "ecb-decision", "boe-decision"}
DIRECTION = re.compile(
    r"\b(?:cut|cuts|hike|hikes|raise|raises|lower|lowers|increase|increases|"
    r"decrease|decreases|hold|holds|no\s+change|not\s+change|unchanged|"
    r"keep|keeps)\b", re.I)
SIGN = re.compile(r"\bbe\s+negative\b|\bnegative\s+(?:gdp|growth)\b|"
                  r"\b(?:highest|lowest)\b.{0,30}\bsince\b|\brecord\s+(?:high|low)\b", re.I)
# Part 3: scheduled, but not an agency print.
NOT_OFFICIAL = re.compile(
    r"\bdelay|\bpostpone|\bcancel|\brevis(?:e|ion)|\bpublish\b|"
    r"\bmarket\s+cap\b|\bipo\b|\bbankrupt|\bfail\b|\bacquire|\bmerger\b|"
    r"\bquarterly\s+earnings\b|\beps\b|\bshare\s+price\b|\bstock\s+price\b|"
    r"\bunderwriter\b|\blargest\b|\bceo\b|\bstock\s+split\b|\bdividend\b|"
    r"\bs&p\s*500\b|\bnasdaq\b|\bdow\s+jones\b|\bbitcoin\b|\bcoinbase\b",
    re.I)
# Part 4 of the join, not of property 1: an agency prints for one jurisdiction.
# China's CPI is not the BLS's and China's GDP is not the BEA's, and both pair
# on series alone. A market that names no jurisdiction is US by convention -
# "Will PPI YoY be 4.2% or less in August?" is a BLS market.
AGENCY_REGION = {"BLS": "us", "BEA": "us", "FED": "us", "ECB": "ea", "BOE": "uk"}
REGION_RULES = (
    ("ea", r"\beuro(?:zone|pean)?\b|\becb\b|euro\s+area|\bhicp\b|"
           r"\bgermany\b|\bfrance\b|\bitaly\b|\bspain\b"),
    ("uk", r"\buk\b|united\s+kingdom|\bbritain\b|\bbritish\b|"
           r"bank\s+of\s+england|\bboe\b|\bons\b"),
    ("us", r"\bus\b|\bu\.s\.|united\s+states|\bamerican?\b|\bfed\b|"
           r"\bfomc\b|\bbls\b|\bbea\b|federal\s+reserve"),
)
_REGION = [(r, re.compile(p, re.I)) for r, p in REGION_RULES]
FOREIGN = re.compile(
    r"\bchina\b|chinese|\bnbs\b|\bjapan\b|\bboj\b|\bindia\b|\bbrazil\b|"
    r"\brussia\b|\bcanada\b|\bmexico\b|\bkorea\b|\bturkey\b|\bargentina\b|"
    r"\baustralia\b|new\s+zealand|\bisrael\b|\bindonesia\b|\bthailand\b|"
    r"south\s+africa|\bswiss\b|switzerland|\bnorway\b|\bsweden\b|\bpoland\b|"
    r"\bnigeria\b|\begypt\b|\bvietnam\b|\bpakistan\b|\bcolombia\b|\bchile\b",
    re.I)

MONTHS = ("january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december")
PERIOD = re.compile(r"\b(" + "|".join(MONTHS) + r"|q[1-4])\b", re.I)


# --- small helpers ---------------------------------------------------------

def parse_iso(s):
    """UTC-aware datetime from an ISO-8601 string, None if unreadable."""
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def iso(d):
    return d.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def property_one(text):
    """Carve-out property 1 on a title+slug blob, given the series is known."""
    return not NOT_OFFICIAL.search(text) and bool(NUMERIC.search(text) or SIGN.search(text))


def series_of(text):
    """The release series a market's title+slug names, or None."""
    for series, rx in _SERIES.items():
        if rx.search(text):
            return series
    return None


def region_of(text):
    """'us' / 'ea' / 'uk' / 'other' / None (unspecified) for one market."""
    for region, rx in _REGION:
        if rx.search(text):
            return region
    return "other" if FOREIGN.search(text) else None


def periods_in(text):
    """Reference periods the title names, lowercased ('august', 'q3')."""
    return {m.group(1).lower() for m in PERIOD.finditer(text)}


def upcoming(now, weeks):
    """Release rows inside [now, now + weeks], oldest first."""
    horizon = now + dt.timedelta(weeks=weeks)
    out = []
    for agency, series, label, when, period in RELEASES:
        t = parse_iso(when)
        if t is None or not (now <= t <= horizon):
            continue
        url, read_on, how = SOURCES.get((agency, series), ("", "", ""))
        out.append({"agency": agency, "series": series, "label": label,
                    "release_utc": iso(t), "at": t, "period": period,
                    "source": url, "read_on": read_on, "how_read": how})
    return sorted(out, key=lambda r: r["at"])


# --- the gamma side --------------------------------------------------------

def open_econ_markets(end_min, end_max, max_pages, verbose=True):
    """Open econ-lane markets ending in the window: family + property 1."""
    rules = sv.load_value_config()[0]
    seen, kept, pages = set(), [], 0
    while pages < max_pages:
        try:
            batch = pmapi.gamma_markets(
                tag_id=ECON_TAG_ID, closed="false", limit=PAGE,
                offset=pages * PAGE, order="endDate", ascending="true",
                end_date_min=iso(end_min), end_date_max=iso(end_max))
        except RuntimeError as e:
            print(f"calendar: gamma page {pages} failed ({e}); "
                  f"continuing with {len(kept)} markets", file=sys.stderr)
            break
        if not batch:
            break
        for m in batch:
            mid_id = str(m.get("id"))
            if mid_id in seen:
                continue
            seen.add(mid_id)
            q, slug = m.get("question") or "", m.get("slug") or ""
            if sv.family_of(q, slug, rules) != ECON_FAMILY:
                continue
            text = f"{q} {slug}"
            series = series_of(text)
            if series is None or not property_one(text):
                continue
            kept.append(_row(m, series, text))
        pages += 1
        if len(batch) < PAGE:
            break
        time.sleep(SLEEP_S)
    if verbose:
        print(f"calendar: gamma {pages} page(s), {len(seen)} open econ-tag "
              f"markets, {len(kept)} in the lane with a known series",
              file=sys.stderr)
    return kept


def _row(m, series, text):
    """The fields match/emit print, straight off the gamma record."""
    try:
        prices = [float(p) for p in json.loads(m.get("outcomePrices") or "[]")]
    except (TypeError, ValueError, json.JSONDecodeError):
        prices = []
    event = (m.get("events") or [{}])[0]
    return {
        "market_id": str(m.get("id")),
        "question": m.get("question") or "",
        "slug": m.get("slug") or "",
        "series": series,
        "periods": periods_in(text),
        "region": region_of(text),
        "mid": prices[0] if prices else None,
        "liquidity": float(m.get("liquidityNum") or 0),
        "volume_24h": float(m.get("volume24hr") or 0),
        "end_date": m.get("endDate"),
        "end": parse_iso(m.get("endDate")),
        "created_at": m.get("createdAt"),
        "event_slug": event.get("slug"),
    }


def match(now, weeks, max_lag_days, max_pages):
    """(releases, unmatched) - each release with the markets that resolve on it."""
    rels = upcoming(now, weeks)
    for r in rels:
        r["markets"] = []
    if not rels:
        return rels, []
    end_max = rels[-1]["at"] + dt.timedelta(days=max_lag_days)
    lag_cap = dt.timedelta(days=max_lag_days)
    unmatched = []
    for mk in open_econ_markets(now, end_max, max_pages):
        if mk["end"] is None:
            continue
        # candidates: same series, release at or (just) before the end date
        cands = [r for r in rels if r["series"] == mk["series"]
                 and (mk["region"] is None
                      or mk["region"] == AGENCY_REGION.get(r["agency"]))
                 and r["at"] <= mk["end"] + dt.timedelta(hours=PRE_GRACE_H)
                 and mk["end"] - r["at"] <= lag_cap]
        if not cands:
            unmatched.append(mk)
            continue
        named = mk["periods"]
        best = max(cands, key=lambda r: ((r["period"] in named) if named else False,
                                         r["at"]))
        mk["lag_h"] = (mk["end"] - best["at"]).total_seconds() / 3600.0
        best["markets"].append(mk)
    for r in rels:
        r["markets"].sort(key=lambda m: -m["liquidity"])
    return rels, unmatched


# --- printing --------------------------------------------------------------

def cmd_releases(args, now):
    rels = upcoming(now, args.weeks)
    if args.json:
        print(json.dumps([{k: v for k, v in r.items() if k != "at"} for r in rels],
                         indent=1))
        return
    print(f"Scheduled official releases, {iso(now)} .. "
          f"{iso(now + dt.timedelta(weeks=args.weeks))} ({args.weeks} weeks): "
          f"{len(rels)} of {len(RELEASES)} in the table")
    print(f"{'release (UTC)':21} {'agency':7} {'series':12} {'release':46} "
          f"{'read':11} source")
    for r in rels:
        print(f"{r['release_utc']:21} {r['agency']:7} {r['series']:12} "
              f"{r['label'][:46]:46} {r['read_on']:11} {r['source']}")


def cmd_match(args, now):
    rels, unmatched = match(now, args.weeks, args.max_lag_days, args.max_pages)
    total = sum(len(r["markets"]) for r in rels)
    if args.json:
        out = [{"release_utc": r["release_utc"], "agency": r["agency"],
                "series": r["series"], "label": r["label"],
                "markets": [{k: v for k, v in m.items()
                             if k not in ("end", "periods")} for m in r["markets"]]}
               for r in rels]
        print(json.dumps(out, indent=1))
        return
    print(f"{len(rels)} release(s) in {args.weeks} weeks, {total} open lane "
          f"market(s) matched, {len(unmatched)} lane market(s) with no release "
          f"inside {args.max_lag_days}d")
    for r in rels:
        print(f"\n{r['release_utc']}  {r['agency']} {r['series']}  {r['label']}"
              f"  [{len(r['markets'])} market(s)]")
        for m in r["markets"]:
            mid = "  n/a" if m["mid"] is None else f"{m['mid']:5.2f}"
            print(f"    {m['market_id']:>9}  mid {mid}  liq {m['liquidity']:>9,.0f}"
                  f"  end {m['end_date']}  lag {m['lag_h']:+7.1f}h  "
                  f"{m['question'][:72]}")
    if unmatched:
        print(f"\nlane markets with no matching release "
              f"(the ceiling this table cannot reach): {len(unmatched)}")
        for m in sorted(unmatched, key=lambda m: -m["liquidity"])[:15]:
            print(f"    {m['market_id']:>9}  {m['series']:12} end {m['end_date']}"
                  f"  {m['question'][:72]}")


def cmd_emit(args, now):
    rels, _unmatched = match(now, args.weeks, args.max_lag_days, args.max_pages)
    window = min(max(int(args.window_min), WATCH_WINDOW_MIN), WATCH_WINDOW_MAX)
    lead = dt.timedelta(hours=args.lead)
    entries, past, empty = [], 0, 0
    for r in rels:
        if not r["markets"]:
            empty += 1
            continue
        fire_at = r["at"] - lead
        if fire_at + dt.timedelta(minutes=window) <= now:
            past += 1
            continue
        ids = ", ".join(m["market_id"] for m in r["markets"][:6])
        more = "" if len(r["markets"]) <= 6 else f" +{len(r['markets']) - 6} more"
        top = r["markets"][0]["question"][:90]
        entries.append({
            "label": (f"{r['agency']} {r['label']} - release {r['release_utc']}, "
                      f"{len(r['markets'])} open market(s) {ids}{more}; "
                      f"largest: {top}; from core/release_calendar.py emit --lead "
                      f"{args.lead:g}, schedule {r['source']}"),
            "fire_at": iso(fire_at),
            "window_min": window,
            "expires": iso(r["at"] + dt.timedelta(hours=12)),
        })
    entries.sort(key=lambda e: e["fire_at"])
    dropped = max(0, len(entries) - WATCH_MAX_CALENDAR)
    kept = entries[:WATCH_MAX_CALENDAR]
    for line in (
        f"core/release_calendar.py emit --lead {args.lead:g} --weeks {args.weeks} "
        f"--window-min {window}  ({iso(now)})",
        f"  {len(rels)} release(s) in horizon; {empty} with no open market; "
        f"{past} whose fire time has already passed at this lead",
        f"  {len(entries)} entry/entries built, {len(kept)} printed, "
        f"{dropped} dropped by watch.py's cap of {WATCH_MAX_CALENDAR}",
        f"  strategy/watchlist.json already holds calendar entries of its own: "
        f"watch.py honours the FIRST {WATCH_MAX_CALENDAR} of the merged array, "
        f"so merge, do not append blindly. This command writes nothing.",
    ):
        print(line, file=sys.stderr)
    print(json.dumps(kept, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--now", default=None, help="override UTC now (ISO-8601)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, net=True):
        p.add_argument("--weeks", type=float, default=8.0)
        p.add_argument("--json", action="store_true")
        if net:
            p.add_argument("--max-lag-days", type=float, default=MAX_LAG_DAYS)
            p.add_argument("--max-pages", type=int, default=MAX_PAGES)

    common(sub.add_parser("releases", help="the scheduled releases in the horizon"),
           net=False)
    common(sub.add_parser("match", help="releases joined to open gamma markets"))
    e = sub.add_parser("emit", help="watchlist calendar entries, to stdout")
    common(e)
    e.add_argument("--lead", type=float, required=True,
                   help="hours before the release to fire")
    e.add_argument("--window-min", type=float, default=45)

    args = ap.parse_args()
    now = parse_iso(args.now) or dt.datetime.now(dt.timezone.utc)
    {"releases": cmd_releases, "match": cmd_match, "emit": cmd_emit}[args.cmd](args, now)


if __name__ == "__main__":
    main()
