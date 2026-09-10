# Lane coverage: does Phil see the markets where his research beats the price?

Written 2026-09-09/10 by an overnight gnhf run, against the operator's question:
`journal/screener-value-decision.md` found that scheduled economic prints and
politics are the two families where research holds up on both the Brier and the
walk-forward counterfactual columns, so does Phil actually SEE those markets,
and when in a market's life is the price still wrong there? Nothing in the live
cycle changed. `CYCLE.md`, `core/scan.py`, `core/screen.py`, `core/watch.py`
and `strategy/discovery.py` are untouched, and `strategy/watchlist.json` is the
agent's, so this memo proposes and does not write.

**Status: complete.** Questions 1 to 5 are measured and their tables are
below. The dormant tool is `core/release_calendar.py`, not `core/calendar.py`;
the naming note in question 4 says why. Read question 5 first if you only want
the verdict.

Every gamma and CLOB response is cached under `work/lane/` (gitignored), so a
re-run costs no network. The scratch scripts live there too; this file is where
the tables live.

## What a lane is

The family test is the agent's own mapper in `strategy/screener-value.json`,
loaded through `core/screen_value.py`, so this memo adds no second definition
of a family. On top of it the econ lane applies the playbook's
Mechanical-econ carve-out property 1: the market must resolve off a scheduled
official release, from a statistics agency or a central bank, with a numeric
interpretation-free criterion. That test is three parts, all on title and slug:

1. a named official series or policy decision fires, not merely an
   institution's name;
2. the criterion is numeric - a number with a comparator, bracket or unit, the
   direction of a published policy rate, or the sign of a published series;
3. no disqualifying shape fires - company earnings, market cap, IPOs,
   bankruptcies and share prices are scheduled but are not agency prints, and
   the mapper's `bank of` rule drags them in.

On the 615 econ-print-family markets the econ tag returned in the window,
property 1 keeps 609 and drops exactly 6: three Bank of America underwriting
markets, "Will Bank of America fail by end of 2026?", "Will State Bank of India
be the largest Indian company?" and "BLS delays another CPI release before
2027?". The last one is the interesting drop. It resolves off the BLS calendar
but its criterion is the release process, not the released number.

The politics lane is the mapper's politics family as written, with no second
filter, because that is what the objective's evidence base was built on. Its
composition is in question 1 and it is worth reading before quoting the lane:
7,995 of 8,995 politics-lane markets in the window are election markets, and
663 are say-word props ("Will Trump say 'MAGA' during RNC Convention?", "Will
the announcers say 'Fumble' during the Patriots vs Seahawks game?"). The
say-word rows reach the family through the mapper's `say "` rule. They have a
known resolution time but no scheduled information event, so they are not the
shape the lane hypothesis is about. The value memo already recorded that
politics is the mapper's weakest family, at 0.775 agreement with the agent's
own labels; this is what that number looks like.

## The universe, and what it cost to build

The window is the 28 days before the run start: 2026-08-12T23:19Z to
2026-09-09T23:19Z. A market is in the universe when gamma says
`createdAt <= T0` and `endDate >= T0-28d`, which is "open at some point in the
window", and when the lane test above puts it in a lane. That gives 9,604 lane
markets. Eight more come from `journal/screener.jsonl` alone: Phil screened
them inside the window and no query returned them, which is proof they were
listed, so they are counted in the universe and separately as a query miss.

**An exhaustive sweep of gamma is not possible and the memo does not pretend
otherwise.** `/markets` caps `offset` near 2,500 and returns at most 100 rows a
page, and the near-term universe is thousands of sub-hourly markets deep: a
plain 28-day sweep in endDate order reaches 2026-08-12T03:00Z at offset 2,000
and then 422s. So the union here is the union of 42 targeted queries, 34 of which returned
at least one lane market, and not a listing of Polymarket. Five of them had to be re-swept with an adaptive
endDate bisection, splitting the interval until every slice fits under the cap.
Two operational notes for whoever re-runs this: the `World` tag (101970) with
`closed=true` returns HTTP 500 for `order=endDate&ascending=true` and works
without the order parameter, and the `Elections` tag (144) is a 99.1% subset of
the `Politics` tag (2), so paying for its long tail twice buys 24 markets.

## Question 1: coverage

Reproduce with `python3 work/lane/q1_funnel.py` then `python3
work/lane/q1_md.py`. 120 collect runs are in `journal/screener.jsonl`.

**The funnel, over the full 28-day window.** "Ever" means anywhere in the
journals, not only inside the window:

| stage | econ print | politics |
|---|---|---|
| listed on gamma | 609 | 8,995 |
| ever screened | 71 | 176 |
| ever in a collect run's divergence top 15 | 16 | 51 |
| the same, tie-averaged slots | 23.2 | 122.2 |
| ever researched | 75 | 50 |
| ever bet | 4 | 8 |

The tie-averaged row uses `screen_replay.top_k_weights`, because the live sort
in `core/screen.py collect` is stable and a tie group straddling the 15/16 cut
is decided by universe order, which is not a fact about anything. Across all
120 runs there are 1,800 tie-averaged escalation slots. The econ lane takes
23.2 of them, 1.3%. Politics takes 122.2, 6.8%.

**Research reaches lane markets the screen never sent it.** 26 of the 75
researched econ-lane markets were never screened at all, and 16 of the 50
politics ones. That is the watch tier, the mechanical-econ calendar and the
sibling census claiming their slots under CYCLE.md step 5, and it is why the
`ever researched` row can exceed `ever screened`.

**The same funnel restricted to what the scan could reach.** `journal/
screener.jsonl` starts 2026-08-25, so 13 of the 28 days have no screening
record and a "never screened" there is an artifact of the journal. This row set
keeps only markets whose endDate falls between 2026-08-25 and T0+336h, which is
the scan horizon `CYCLE.md` step 4 uses:

| stage | econ print | politics |
|---|---|---|
| listed on gamma | 181 | 1,489 |
| ever screened | 71 (39%) | 176 (12%) |
| ever in a collect run's divergence top 15 | 16 | 51 |
| ever researched | 63 | 38 |
| ever bet | 3 | 8 |

**Why a lane market was never screened.** One reason per market, first match
wins, in the order shown:

econ print, of the 538 never screened:

| reason | n |
|---|---|
| endDate beyond the 336h scan horizon for the whole window | 400 |
| price outside [0.02, 0.95] today (`scan.keep` would drop it) | 55 |
| resolved since, so the live price at screening time is not reconstructible | 53 |
| resolved before `journal/screener.jsonl` begins (2026-08-25) | 28 |
| reachable and admissible, never reached the 300-market pool | 2 |

politics, of the 8,819 never screened:

| reason | n |
|---|---|
| endDate beyond the 336h scan horizon for the whole window | 6,842 |
| resolved before `journal/screener.jsonl` begins (2026-08-25) | 664 |
| price outside [0.02, 0.95] today (`scan.keep` would drop it) | 559 |
| resolved since, so the live price at screening time is not reconstructible | 472 |
| reachable and admissible, never reached the 300-market pool | 282 |

Two cautions on that table. The price test reads today's `outcomePrices`, not
the price when the market was live, so it is "would be dropped today" and it is
an upper bound on the real cut. And `prepare`'s `dropped_by_reason` categories
cannot be attributed per market from the 19 local briefs, because the manifest
records counts and not identities; the filter regexes in
`strategy/screener-filters.json` were re-applied here directly instead, and
they fire on no lane market at all, which is expected since they target line
shapes, sub-daily crypto and weather brackets.

**The horizon is the whole story on the econ side.** 400 of the 609 econ-lane
markets, 66%, had an endDate more than 336 hours past T0 for the entire window,
so no cycle's scan could have returned them at any point. Only 2 econ-lane
markets were reachable, admissible and still never made the 300-market pool.
Politics is different: 282 of its markets were reachable and admissible and
still lost the pool competition, which is the strata doing their job on a lane
that is 89% election markets.

**endDate mix of the 28-day universe**, which is why the horizon bites:

| bucket | econ print | politics |
|---|---|---|
| already ended | 118 | 1,263 |
| 0-14d, inside the scan horizon | 91 | 882 |
| 14-30d | 90 | 1,875 |
| 30-90d | 134 | 3,321 |
| 90-365d | 176 | 1,308 |
| over 365d | 0 | 338 |
| no endDate | 0 | 8 |

**Composition of the econ lane**, by the release the property-1 test matched:

| series | n |
|---|---|
| CPI and inflation | 168 |
| GDP | 140 |
| other central-bank decisions | 107 |
| PMI and ISM | 40 |
| employment | 37 |
| PCE | 28 |
| FOMC | 25 |
| PPI | 20 |
| consumer sentiment | 14 |
| BoE | 11 |
| BoJ | 10 |
| ECB | 9 |

**Lag from gamma createdAt to first screen, in hours**, as a distribution:

| lane | n | min | p10 | p25 | median | p75 | p90 | max |
|---|---|---|---|---|---|---|---|---|
| econ print | 71 | 376 | 402 | 430 | 486 | 590 | 1,982 | 2,671 |
| politics | 168 | 22 | 92 | 171 | 444 | 1,053 | 5,848 | 6,799 |

**Lag from gamma createdAt to first research, in hours:**

| lane | n | min | p10 | p25 | median | p75 | p90 | max |
|---|---|---|---|---|---|---|---|---|
| econ print | 75 | 190 | 273 | 300 | 620 | 663 | 1,841 | 2,802 |
| politics | 47 | 69 | 106 | 158 | 513 | 2,479 | 6,510 | 6,865 |

Those two tables are the horizon read from the other side. No econ-lane market
is ever screened sooner than 376 hours after it is listed, and the median is
486 hours, 20 days. That is not slowness, it is arithmetic: an econ market is
listed months before it resolves and the scan cannot return it until its
endDate comes inside 336 hours.

**Lead time at first screen and at first research, hours before endDate**, which
is the quantity question 2 needs:

| lane | stage | n | p10 | p25 | median | p75 | p90 |
|---|---|---|---|---|---|---|---|
| econ print | first screen | 71 | 15 | 118 | 186 | 286 | 329 |
| econ print | first research | 75 | 42 | 89 | 287 | 307 | 314 |
| politics | first screen | 168 | 4 | 17 | 36 | 236 | 320 |
| politics | first research | 47 | 2 | 20 | 64 | 260 | 325 |

Econ-lane markets are first screened a median 186 hours, 7.8 days, before they
end. Politics markets are first screened a median 36 hours before they end, a
fifth of that. The two lanes are seen at completely different points in their
lives, and question 2 says which of those points is the useful one.

**What each query returned, against the union.** The four `strategy/
discovery.py` queries are replayed at T0 with the cycle's own `--hours 336`
horizon, so their row is what they would have returned on one cycle, not over
the window. `missed vs union` counts lane markets in the union that this query
did not return:

| query | lane markets | econ | politics | missed vs union |
|---|---|---|---|---|
| tag Politics (2), open | 7,319 | 19 | 7,300 | 2,285 |
| tag Elections (144), open | 6,344 | 0 | 6,344 | 3,260 |
| tag Politics (2), closed | 1,544 | 6 | 1,538 | 8,060 |
| tag Elections (144), closed | 891 | 0 | 891 | 8,713 |
| tag World (101970), open | 686 | 67 | 619 | 8,918 |
| tag Economy (100328), open | 473 | 471 | 2 | 9,131 |
| tag Inflation (702), open | 176 | 176 | 0 | 9,428 |
| discovery `by-liquidity` | 162 | 11 | 151 | 9,442 |
| tag CPI (101701), open | 147 | 147 | 0 | 9,457 |
| tag Geopolitics (100265), open | 135 | 0 | 135 | 9,469 |
| tag Economy (100328), closed | 132 | 118 | 14 | 9,472 |
| discovery `active-today` | 125 | 48 | 77 | 9,479 |
| tag GDP (370), open | 117 | 117 | 0 | 9,487 |
| discovery `econ-tag` | 74 | 74 | 0 | 9,530 |
| discovery `liquid-multiday` | 50 | 15 | 35 | 9,554 |

The full 34-row table is in `work/lane/q1.json`. Two lines to read.

First, **the econ tag is already enough**. The Economy tag (100328) alone
returns 589 of the 609 econ-lane markets, 96.7%, and all eleven econ tags
together return exactly 609, so no econ-lane market in this window was missed
by every econ query. Adding the Inflation, CPI, GDP or jobs tags to
`strategy/discovery.py` would widen the lane by 16, 16, 0 and 0 markets
respectively, because they are near-subsets of the Economy tag. On the politics
side the Politics tag (2) returns 8,838 of 8,995 and the other seven politics
tags add 130 between them. **A new discovery query is not what the econ lane is
short of.** The 336-hour horizon is.

Second, the discovery block's counts are one cycle's snapshot at T0 with the
cycle's own 336-hour horizon, so they are not comparable with a query swept
over 28 days. Between them the four queries return 310 distinct lane markets on
that one cycle, 81 econ and 229 politics, and `econ-tag` supplies 74 of the 81
econ ones on its own.

## Question 2: when is the price still wrong

Reproduce with `python3 work/lane/q2_timing.py` and `python3
work/lane/q2_panel.py`. One CLOB `/prices-history` call per lane market,
`interval=max&fidelity=60`, cached under `work/lane/hist/`. The unit is a
settled forecast row: 91 rows over 76 markets in the econ lane, 41 over 38 in
politics. The price read is the researched token's, so 1 means the forecast's
own side won. Intervals are `screen_replay.mean_se`, the event-clustered
sandwich, keyed on `journal/screener-events.jsonl` with an unmapped market as
its own cluster.

**The balanced panel is the table to read.** Not every market's book was open
seven days before its end, so a curve whose n changes between leads mixes
convergence with composition. The panel keeps only rows priced at all five
leads: 64 rows over 28 events in econ, 17 over 13 in politics.

econ print, balanced panel, n 64, 28 events:

| lead before endDate | mean abs(mid - outcome) | +/- | Brier | +/- |
|---|---|---|---|---|
| 7 days | 0.3211 | 0.0423 | 0.1813 | 0.0377 |
| 3 days | 0.3070 | 0.0360 | 0.1666 | 0.0335 |
| 1 day | 0.2988 | 0.0380 | 0.1652 | 0.0362 |
| 6 hours | 0.1559 | 0.0474 | 0.0797 | 0.0318 |
| 1 hour | 0.1569 | 0.0482 | 0.0831 | 0.0340 |

**This is the finding of the memo.** The econ price barely moves from seven days
out to one day out: Brier 0.181, 0.167, 0.165. It then halves between 24 hours
and 6 hours, to 0.080, and does nothing at all in the last 6 hours. The price
converges AT the print, not before it, and the window in which it is still
wrong runs the whole way to about a day before the market ends. The flat last
6 hours also says these markets' endDates sit well after their release times,
so endDate is a conservative anchor and the true convergence is sharper than
this table can show.

politics, balanced panel, n 17, 13 events:

| lead before endDate | mean abs(mid - outcome) | +/- | Brier | +/- |
|---|---|---|---|---|
| 7 days | 0.3412 | 0.0741 | 0.1851 | 0.0704 |
| 3 days | 0.3746 | 0.0791 | 0.2286 | 0.0823 |
| 1 day | 0.3446 | 0.0817 | 0.2093 | 0.0809 |
| 6 hours | 0.3039 | 0.0841 | 0.1933 | 0.0837 |
| 1 hour | 0.1744 | 0.0652 | 0.0952 | 0.0581 |

Politics converges later still. The whole fall is in the final hour, from Brier
0.193 at 6 hours to 0.095 at 1 hour, and 17 rows over 13 events cannot carry
more than that sentence.

**Where Phil's record sits on those curves.** Median lead at record is 51.5
hours for econ, p25 27.6 and p75 303.6. For politics it is 31.7 hours, p25 11.3
and p75 43.6. So the median econ forecast is recorded two days out, inside the
band where the price is still wrong by Brier 0.165 and before the collapse. The
median politics forecast is recorded 32 hours out, also before its collapse.
Neither lane is being researched too late by this measure.

**brier_delta by lead-time band at record.** Negative means research beat the
price it was handed:

econ print, 91 rows, 33 events, whole lane -0.0010 +/- 0.0127:

| band at record | n | events | brier_delta | +/- | z |
|---|---|---|---|---|---|
| over 7d | 35 | 22 | +0.0033 | 0.0313 | 0.11 |
| 3d-7d | 3 | 2 | -0.0351 | 0.0357 | -0.99 |
| 1d-3d | 36 | 8 | -0.0039 | 0.0081 | -0.48 |
| 6h-24h | 7 | 3 | -0.0046 | 0.0039 | -1.20 |
| under 6h | 10 | 6 | +0.0069 | 0.0046 | 1.50 |

politics, 41 rows, 25 events, whole lane -0.0149 +/- 0.0262:

| band at record | n | events | brier_delta | +/- | z |
|---|---|---|---|---|---|
| over 7d | 3 | 2 | -0.0149 | 0.0107 | -1.39 |
| 3d-7d | 2 | 2 | -0.0165 | 0.0059 | -2.80 |
| 1d-3d | 20 | 9 | -0.0392 | 0.0551 | -0.71 |
| 6h-24h | 7 | 6 | -0.0243 | 0.0216 | -1.12 |
| under 6h | 9 | 7 | +0.0468 | 0.0310 | 1.51 |

**Which bands are too thin to read: all of them except two.** In econ only
`over 7d` (35 rows, 22 events) and `1d-3d` (36 rows, 8 events) carry any
weight, and both sit inside their own interval. The econ `3d-7d`, `6h-24h`
cells hold 3 and 7 rows over 2 and 3 events, which is one or two independent
prints each. In politics every band is under 21 rows and the 3d-7d cell's z of
-2.80 comes from 2 rows in 2 events with an interval of 0.0059, which is two
near-certain markets and not a finding. The honest summary is that the price
evidence, not the brier_delta evidence, is what carries a lead-time
recommendation right now.

## Question 3: the calendar tier as it is

Reproduce from `journal/watch-triggers.jsonl` and `journal/forecasts.jsonl`. A
forecast is attributed to a fire when it is recorded within three hours of it.
The tier has fired 7 times since it was built, up from the 5 the value memo
counted two days ago, against 39 `new_market` and 10 `price_move` fires:

| fire (UTC) | entry | forecasts | bets | settled rows | brier_delta |
|---|---|---|---|---|---|
| 2026-08-27T01:22Z | Bank of Korea rate decision | 6 | 0 | 6 | -0.0301 |
| 2026-08-28T12:30Z | Statistics Canada GDP | 6 | 0 | 6 | +0.0211 |
| 2026-08-28T14:25Z | UMich consumer sentiment, final | 4 | 0 | 4 | +0.0180 |
| 2026-09-01T12:42Z | Brazil Q2 GDP (IBGE) | 6 | 0 | 6 | +0.0002 |
| 2026-09-01T14:24Z | ISM manufacturing PMI | 8 | 0 | 8 | +0.0684 |
| 2026-09-09T01:38Z | China August CPI (NBS) | 3 | 0 | 3 | -0.0103 |
| 2026-09-09T18:38Z | Apple keynote conclusion check | 1 | 0 | 0 | - |
| **total** | | **34** | **0** | **33** | **+0.0162 +/- 0.0219** |

Beside the value memo's tick-type table, which is the same statistic on the
same journal:

| arm | n | events | brier_delta | +/- |
|---|---|---|---|---|
| calendar fires | 33 | 21 | +0.0162 | 0.0219 |
| all TRIGGERED | 19 | 19 | -0.0138 | 0.0495 |
| all FULL | 523 | 376 | +0.0088 | 0.0093 |

Three things to take from that. First, **six of the seven fires are econ-lane
scheduled prints**, so the agent already uses this tier for exactly the lane
this memo is about. Second, **the tier has produced no bet at all**: 34
forecasts, zero positions. Third, the settled rows read +0.0162, on the wrong
side of zero, and 21 events cannot separate that from the FULL arm's +0.0088.
The tier converts fires into forecasts reliably and has not yet converted a
forecast into an edge.

The five calendar entries standing in `strategy/watchlist.json` right now are
all econ-lane prints: China CPI, US PPI, the Bank of Russia key rate, US CPI
and the September FOMC. The agent writes them by hand from its own research, at
most 10 at a time, and `core/watch.py` clamps their window.

The other half of question 3, how many of the 609 econ-lane markets had a
release date a public agency published in advance, needs the release table that
`core/calendar.py releases` will carry. It is not measured yet.

## Question 3, second half: the ceiling of an agency calendar

Reproduce with `python3 work/lane/q3b_ceiling.py`. The unit is a question 1
econ-lane market. The question is whether the date it settles on is one a
public agency publishes in advance, and which agency owns that schedule. The
jurisdiction matters: China's CPI is not the BLS's and Eurozone GDP is not the
BEA's, and both pair on the series name alone unless the join checks the
country.

| tier | markets | distinct gamma events |
|---|---|---|
| the eight series `core/release_calendar.py` carries today | 198 | 34 |
| agencies the objective names that the table does not carry (Eurostat, ONS, NBS) | 92 | 12 |
| some other agency that publishes an advance calendar | 319 | 53 |
| no advance agency schedule | 0 | 0 |
| **total** | **609** | **99** |

By agency:

| agency | markets | events |
|---|---|---|
| a national statistics office outside the named list | 148 | 20 |
| a central bank outside the named list | 107 | 25 |
| BLS | 102 | 12 |
| BEA | 51 | 8 |
| ISM | 40 | 4 |
| NBS (China) | 38 | 5 |
| Eurostat | 31 | 4 |
| Federal Reserve | 25 | 8 |
| ONS (UK) | 23 | 3 |
| UMich | 14 | 2 |
| Bank of England | 11 | 3 |
| Bank of Japan | 10 | 2 |
| ECB | 9 | 3 |

**Every econ-lane market in the window has a release date somebody published in
advance.** That is what carve-out property 1 selects for, so the zero in the
last row is a consistency check and not a surprise. The number that matters is
the split: the eight series in the shipped table reach 198 of 609 markets and
34 of 99 events, 33% and 34%. Adding Eurostat, ONS and NBS takes it to 290 of
609, 48%. The remaining half is a long tail of national central banks and
statistics offices, 255 markets over 45 events, each with its own calendar page
in its own language. A scheduled-release calendar is not a small table that
covers the lane. It is a table whose coverage is exactly as wide as the number
of agency pages somebody keeps up to date.

Read that beside the calendar tier's yield above. The tier is not short of
things to watch. Seven fires and 34 forecasts came out of five hand-written
entries, and the table below would have offered 34 events in the same window
from five agencies alone.

## Question 4: the dormant emitter

**It is `core/release_calendar.py`, not `core/calendar.py`.** A file called
`core/calendar.py` answers the standard library's `import calendar`, because
every core script puts `core/` on `sys.path[0]`. `_strptime` imports the
standard library `calendar` on the first `datetime.strptime` call, so
`python3 core/validate.py` dies with `module 'calendar' has no attribute
'day_abbr'` the moment the file exists. That was written, reproduced and then
renamed, and the docstring records it so nobody renames it back.

Nothing calls the file. `CYCLE.md`, `core/watch.py`, `strategy/discovery.py`
and the routines are untouched, and the tool writes nothing at all: not
`strategy/watchlist.json`, not a journal, not a cache. Three subcommands:

```
python3 core/release_calendar.py releases [--weeks 8] [--json]
python3 core/release_calendar.py match    [--weeks 8] [--max-lag-days 21] [--json]
python3 core/release_calendar.py emit --lead <hours> [--weeks 8] [--window-min 45]
```

### The release table

Hard-coded in the file, one row per release, each an explicit UTC instant so
no timezone database sits in the loop. `bea.gov`, `federalreserve.gov`,
`ecb.europa.eu` and `bankofengland.co.uk` all answered a plain HTTPS GET from
this machine on 2026-09-10 and their rows are parsed from those pages.
`bls.gov` returns HTTP 403 to this machine's client, so the three BLS series
were read from the same public schedule pages through a browser fetch on the
same day. The URL is the authority either way and `releases` prints it.

One honest limit on that table. Every DATE comes from a source page. The TIMES
do not: the BLS and BEA pages state 08:30 ET per release, but the Fed, ECB and
BoE calendar pages give dates only, so the FOMC statement at 14:00 ET, the ECB
decision at 14:15 CET and Bank Rate at 12:00 London are each the agency's
standing publication time rather than a per-date reading. At a lead measured in
days that cannot put a fire on the wrong day. At a sub-hour lead it could, so
the emitter is not for sub-hour leads.

`releases --weeks 8` on 2026-09-09T23:19Z, 14 of the table's 28 rows:

| release (UTC) | agency | series | what |
|---|---|---|---|
| 2026-09-10T12:15Z | ECB | ecb-decision | monetary policy decision (Sep 9-10) |
| 2026-09-10T12:30Z | BLS | ppi | PPI, August 2026 |
| 2026-09-11T12:30Z | BLS | cpi | CPI, August 2026 |
| 2026-09-16T18:00Z | FED | fomc | FOMC decision (Sep 15-16, with projections) |
| 2026-09-17T11:00Z | BOE | boe-decision | Bank Rate, September MPC |
| 2026-09-30T12:30Z | BEA | gdp | GDP, Q2 2026 third estimate |
| 2026-09-30T12:30Z | BEA | pce | Personal Income and Outlays, August 2026 |
| 2026-10-02T12:30Z | BLS | employment | Employment Situation, September 2026 |
| 2026-10-14T12:30Z | BLS | cpi | CPI, September 2026 |
| 2026-10-15T12:30Z | BLS | ppi | PPI, September 2026 |
| 2026-10-28T18:00Z | FED | fomc | FOMC decision (Oct 27-28) |
| 2026-10-29T12:30Z | BEA | gdp | GDP, Q3 2026 advance estimate |
| 2026-10-29T12:30Z | BEA | pce | Personal Income and Outlays, September 2026 |
| 2026-10-29T13:15Z | ECB | ecb-decision | monetary policy decision (Oct 28-29) |

The table runs to 2026-12-23. It needs one refresh a year, each autumn, when
the agencies publish the next year.

Two rows are worth checking against the agent's own hand-written watchlist,
because they were written independently: the PPI entry the agent wrote fires at
2026-09-10T12:30Z and the FOMC entry at 2026-09-16T18:00Z. The table agrees to
the minute on both.

### match

`match --weeks 12`, run live against gamma on 2026-09-09T23:24Z. One gamma
sweep of the Economy tag, 5 pages, 486 open markets, 177 of them in the lane
with a series this table names. 111 markets matched over 11 releases:

| release (UTC) | agency | series | matched markets | events | median listing lead (days before the release) | median liquidity |
|---|---|---|---|---|---|---|
| 2026-09-10T12:15Z | ECB | ecb-decision | 4 | 1 | 84.6 | 37,775 |
| 2026-09-10T12:30Z | BLS | ppi | 10 | 1 | 27.8 | 526 |
| 2026-09-11T12:30Z | BLS | cpi | 38 | 4 | 29.9 | 2,324 |
| 2026-09-16T18:00Z | FED | fomc | 4 | 1 | 126.0 | 1,018,598 |
| 2026-09-17T11:00Z | BOE | boe-decision | 5 | 1 | 85.4 | 4,002 |
| 2026-09-30T12:30Z | BEA | gdp | 0 | 0 | - | - |
| 2026-09-30T12:30Z | BEA | pce | 14 | 2 | 34.5 | 524 |
| 2026-10-02T12:30Z | BLS | employment | 16 | 2 | 27.8 | 2,706 |
| 2026-10-14T12:30Z | BLS | cpi | 0 | 0 | - | - |
| 2026-10-15T12:30Z | BLS | ppi | 0 | 0 | - | - |
| 2026-10-28T18:00Z | FED | fomc | 4 | 1 | 132.8 | 160,670 |
| 2026-10-29T12:30Z | BEA | gdp | 7 | 1 | 89.6 | 1,003 |
| 2026-10-29T12:30Z | BEA | pce | 0 | 0 | - | - |
| 2026-10-29T13:15Z | ECB | ecb-decision | 4 | 1 | 96.9 | 9,104 |
| 2026-11-05T12:00Z | BOE | boe-decision | 5 | 1 | 96.6 | 1,917 |
| 2026-11-06T13:30Z and later (5 rows) | - | - | 0 | 0 | - | - |

Three things that table settles.

**Polymarket lists a release's markets long before the release, and the two
shapes differ.** A central-bank decision pair is listed a median 85 to 133 days
ahead. A statistics-print bracket set is listed a median 28 to 35 days ahead.
Nothing at all exists yet for any release after 2026-11-05. So the emitter's
usable horizon is set by listing, not by the release table: at `--weeks 8`
today, 6 of 14 releases have no market to watch yet, and a weekly re-run is
what keeps up with that, not a longer table.

**Half the matched markets are outside the scan's reach.** 50 of the 111
matched markets, 45%, over 5 of the 11 releases that have markets, have an
endDate more than 336 hours out, so `core/scan.py` cannot return them on any
cycle today. That is the calendar tier's whole reason to exist, in one number.

**Gamma end dates run early of the print they settle on.** August CPI ends
03:59Z on release day, 8.5 hours before the 12:30Z print. The September
unemployment brackets end at 08:30Z, 4 hours early. The September FOMC pair
ends 18 hours before the statement. The join therefore allows a release up to
36 hours after a market's end date, which cannot cross two releases of the
same series because they are a month apart. Without that slack the August CPI
set, 38 markets and the largest print set in the window, matches nothing.

The join also refuses a jurisdiction mismatch. Before that check, 9 China GDP
markets paired with the BEA's Q2 estimate and 5 China CPI markets with the
BLS's September print. Those are NBS releases and the table does not carry NBS,
so `match` now lists them under "lane markets with no matching release", which
is where the ceiling in question 3 shows up on a live run: 71 open lane markets
have no release in this table.

### emit

`emit --lead 72 --weeks 8` printed 7 entries and dropped 0 to the cap. The
header goes to stderr and the JSON array to stdout, so `emit --lead 72 >
entries.json` is a valid merge source. The entries were fed straight back
through `core/watch.py`'s own `calendar_entries` parser: it accepted 7 of 7,
expired none, and `check_calendar` fires on the first entry at its window open.
The schema is the one the agent writes by hand, `{label, fire_at, window_min,
expires}`, with `window_min` clamped to 5..60, which is inside both of
`watch.py`'s clamps.

| fire_at (UTC) | release | markets in the label |
|---|---|---|
| 2026-09-13T18:00Z | FOMC Sep 15-16 | 4 |
| 2026-09-14T11:00Z | BoE September MPC | 5 |
| 2026-09-27T12:30Z | BEA PCE, August | 14 |
| 2026-09-29T12:30Z | BLS Employment Situation, September | 16 |
| 2026-10-25T18:00Z | FOMC Oct 27-28 | 4 |
| 2026-10-26T12:30Z | BEA GDP, Q3 advance | 7 |
| 2026-10-26T13:15Z | ECB Oct 28-29 | 4 |

Of those 7, only the September FOMC is already on the agent's hand-written
watchlist. The other 6 are releases nobody wrote down.

The label carries the release time, the matched market ids, the largest
market's question and the schedule URL, because the label is all the triggered
cycle sees.

### The discovery query this argues for, per lane

Reproduce with `python3 work/lane/q4_queries.py`. Each candidate is replayed as
a filter over the cached 28-day sweeps, so "what would it have returned at T0"
is a set operation and costs no network. `strategy/discovery.py` is not edited.

| candidate | lane | lane markets returned | already in the discovery union | net add | events added | share of the 800 scan cap |
|---|---|---|---|---|---|---|
| econ tag, endDate 336h to 90d | econ | 224 | 0 | 224 | 38 | 28.0% |
| econ tag, endDate 336h to 45d | econ | 115 | 0 | 115 | 20 | 14.4% |
| Politics tag, liquidity >= 5k, 336h to 90d | politics | 3,484 | 0 | 3,484 | 594 | 435.5% |
| Politics tag, liquidity >= 20k, 336h to 90d | politics | 261 | 0 | 261 | 67 | 32.6% |
| Politics tag, liquidity >= 20k, 336h to 45d | politics | 183 | 0 | 183 | 45 | 22.9% |

The `already in the discovery union` column is zero by construction: all four
live queries stop at `end_date_max = T0 + 336h` and every candidate starts
there. That is the point. The proposal is a horizon, not a tag.

**Econ.** Add one query, the Economy tag past the scan horizon and bounded at
45 days:

```python
{"closed": "false", "tag_id": 100328, "order": "endDate", "ascending": "true",
 "end_date_min": <T0 + 336h>, "end_date_max": <T0 + 45d>}
```

115 lane markets over 20 events, 14% of the 800-market scan cap. The 90-day
variant doubles the add for 18 more events and costs 28% of the cap, which is
too much of the pool to spend on one lane before the lane has produced a bet.

**Politics.** Add one query, the Politics tag past the horizon with a liquidity
floor:

```python
{"closed": "false", "tag_id": 2, "order": "liquidity", "ascending": "false",
 "liquidity_num_min": 20000,
 "end_date_min": <T0 + 336h>, "end_date_max": <T0 + 45d>}
```

183 lane markets over 45 events, 23% of the cap. The floor is doing all the
work. At 5,000 the same query returns 3,484 lane markets, four times the entire
scan cap, which is the shape of a lane that is 89% election markets.

Both together take 37% of the scan cap. That is the cost line the bar below
prices.

## Question 5: the decision

**Phil sees the econ lane late, not never, and the reason is the 336-hour scan
horizon rather than the discovery query.** The Economy tag alone returns 96.7%
of the lane, and only 2 of 609 econ-lane markets were reachable, admissible and
still missed the pool, so nothing is wrong with what Phil asks gamma for. What
is wrong is when he asks. 400 of the 609, 66%, sat past the scan horizon for
the entire 28 days, no econ market is ever screened sooner than 376 hours after
listing, and 45% of the markets that a release calendar matches today are still
outside that horizon. On the timing question the price evidence is clear and
points the other way: an econ print's price is essentially as wrong seven days
before the market ends as it is one day before, Brier 0.181 against 0.165, and
it only halves, to 0.080, in the last six hours, which for these markets is at
or after the print itself. So there is no race. Any lead from a week down to a
day sits on the same flat part of the curve, and the agent's median econ
forecast at 51.5 hours is already inside it. **Switch the calendar emitter on,
at a lead of 72 hours, and add the econ discovery query. Do not add the politics
query yet.** The emitter is the cheap half: it costs one gamma sweep a week,
it reaches markets the scan cannot, and 6 of the 7 entries it printed tonight
are releases nobody had written down. The econ query is the half that changes
what the scan competes over, so it goes in second and alone, because the
politics lane's own numbers, 122 of 1,800 escalation slots already and 282
reachable markets that lost the pool competition on merit, say its problem is
crowding rather than blindness. The one thing neither change fixes is the
conversion problem: the calendar tier has fired 7 times, produced 34 forecasts
and placed zero bets, at a settled brier_delta of +0.0162 +/- 0.0219 over 33
rows and 21 events, which is on the wrong side of zero. More fires into that
funnel buy more forecasts, not more positions, so the bar below is written
about bets and not about attention.

The three numbers that carry it:

1. **400 of 609.** Econ-lane markets past the 336-hour scan horizon for the
   whole window, 66%. The coverage gap, and it is a horizon and not a query.
2. **0.181 at 7 days against 0.165 at 1 day, then 0.080 at 6 hours.** The econ
   price converges at the print, so a 72-hour lead loses nothing to a 24-hour
   one and buys two more cycles of research time.
3. **34 forecasts, 0 bets.** What the calendar tier has produced so far. Every
   switch below is on probation against this number.

### The bar that would change this

Pre-registered, in the shape of the switch bars in
`journal/screener-rank-decision.md` and `journal/screener-value-decision.md`.

**Keep the emitter on** only when all three hold, measured over the first 20
calendar fires whose watchlist entry came from `emit`:

1. **Reach.** At least 12 of those 20 fires name a market whose endDate was
   more than 336 hours out at fire time, so the fire reached something the scan
   could not. Read it from `journal/watch-triggers.jsonl` joined to gamma
   endDate.
2. **Conversion.** At least 3 of the 20 fires produce a BET in
   `journal/ledger.jsonl` within 6 hours of the fire, not a forecast. Today the
   tier is 7 fires and 0 bets, so this is the condition the tier has never met.
3. **Edge.** Those fires' settled rows read `brier_delta <= 0` with at least 40
   rows over 25 events, scored with `core/score.py` and clustered with
   `screen_replay.mean_se`. The current calendar arm is +0.0162 over 33 rows
   and 21 events, so this asks for the sign to flip on roughly the same sample
   size.

If 1 holds and 2 does not, the emitter is finding markets the agent will not
bet. Cut it back to the two highest-liquidity releases a month rather than
every match, and re-read after another 20 fires. If 1 and 2 hold and 3 does
not, keep it: a tier that reaches new markets and converts them is worth its
gamma sweep even at par, and par is what the whole research record reads
(+0.0080 +/- 0.0091 over 542 rows). If 1 does not hold, switch it off. The
emitter's only claim over the existing scan is reach.

**Add the econ discovery query** only when all three hold:

1. **Cost.** `core/scan.py` still returns fewer than 800 markets with the query
   added, so nothing is displaced by the cap. Check it on one live cycle
   before committing the edit.
2. **Uptake.** After 4 weeks, the econ lane's share of tie-averaged escalation
   slots is above 3%, up from today's 1.3% (23.2 of 1,800), measured with
   `screen_replay.top_k_weights` exactly as question 1 does.
3. **Quality.** The econ lane's settled `brier_delta` over that period is <= 0
   with at least 60 rows, against today's -0.0010 +/- 0.0127 over 91 rows.

If 2 holds and 3 does not, the query is buying attention that the research
cannot use. Revert it. Revisit the politics query only after the econ one has
cleared all three, because the two compete for the same 800 slots and the
politics lane is the one already taking 6.8% of them.

### How to switch it on

1. Read this file, `journal/screener-value-decision.md` and
   `journal/operator-notes.md` for 2026-09-04 and 2026-09-09.
2. Check what the emitter would write, without writing anything:

   ```
   python3 core/release_calendar.py releases --weeks 8
   python3 core/release_calendar.py match --weeks 8
   python3 core/release_calendar.py emit --lead 72 --weeks 8 > work/cal-entries.json
   ```

   `releases` makes no network call. `match` and `emit` make one paced gamma
   sweep of the Economy tag, capped at `--max-pages`, and neither writes
   anything anywhere.
3. Merge, do not append. `strategy/watchlist.json` is the agent's file and
   already holds 5 calendar entries, and `core/watch.py` honours the FIRST 10
   of the merged array. Open `work/cal-entries.json`, drop any entry whose
   release the agent already watches (tonight that is the September FOMC), and
   paste the rest into the `calendar` array, keeping the array sorted by
   `fire_at` so the cap drops the furthest-out entry and not the nearest.
   Add a line to the file's `_comment` array saying the entries came from
   `core/release_calendar.py emit --lead 72` and on what date, so the next
   cycle knows which entries it did not write.
4. Re-run weekly. Listing lead is a median 28 days for a print bracket set, so
   a weekly re-run catches every set well before its release. A monthly re-run
   would miss the sets listed in between.
5. Record the switch in `journal/operator-notes.md`, with the lead used, so the
   calendar arm in `journal/screener-value-decision.md`'s tick-type table can
   be split into hand-written and emitted fires later.
6. For the econ discovery query, add the fifth entry to `strategy/discovery.py`
   exactly as printed in question 4, run one cycle, and check condition 1
   before committing.

### Landing note: this file's core/ change needs an operator commit

`core/release_calendar.py` is a new file under `core/`, which is operator-owned.
The CI boundary guard treats any commit not prefixed `operator:` as an agent
commit and fails the push when one touches an operator-owned path, and
`loop.sh` cannot revert an untracked file, so the hourly cycle would commit it
and go red. Re-commit the file with an `operator:` prefixed message before the
next push. This is the same failure that landed `core/screen_rank.py` in a
cycle commit on 2026-09-04.
