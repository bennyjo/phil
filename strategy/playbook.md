# Strategy Playbook

AGENT-EDITABLE. This file is mine (the trading agent's) to rewrite as I learn.
Every edit must be justified by evidence from settled positions (see
`journal/retros/`). Version: v0 — seeded by the operator, unproven.

## Thesis

I cannot out-research the market on everything. I can win where (a) the market
is thin or inattentive, and (b) public information is retrievable in minutes.
Short-term markets force fast feedback: every settled bet is a data point on
where my research actually beats the price.

### Edge classes (added DEEP-2026-07-31, from the 2/2 vs 0/7 split)

Rank every candidate by WHY the market should be wrong, strongest first:

1. **Structural — information race**: the resolution-relevant fact is already
   public and the book demonstrably hasn't finished repricing (verify at the
   live book, not the mid). Evidence: `2dc417ed68f6` won.
   **Fact-finality requirement (DEEP-2026-08-03):** the fact must be FINAL
   as the resolver will see it — an official print/close/result — not an
   estimate subject to scheduled revision, whenever the bet's margin sits
   inside typical revision noise. Sunday box-office numbers are studio/
   Comscore estimates revised by Monday actuals; `84ec821167d5` bet No at
   0.16 on a "$2M short" (0.6%) margin from such an estimate and was
   marked to ~0.02 within 10h as actuals landed. N outlets repeating one
   provisional figure are ONE source, not N confirmations. Corollary: a
   liquid book holding its price AFTER your headlines are public — or
   moving further against you while you check — is the crowd pricing
   something beyond the headline (revision risk, resolver read), not the
   crowd being slow; the NG win (`2dc417ed68f6`) was the opposite shape,
   an already-final official settlement print.
2. **Structural — cross-market inconsistency**: two related markets (sibling
   1X2 legs, spread-vs-ML) imply contradictory probabilities. Evidence:
   `1e8dec1078ba` won.
   **Validity test (DEEP-2026-08-03):** the sibling's implied probability
   must be actually INCOMPATIBLE with the target market's — work the
   implication out numerically before citing it. A bracket market whose
   range contains the target's threshold discriminates nothing:
   `84ec821167d5` cited the $350-360M bracket (~85% Yes) as contradicting
   beat-record-$357.1M (~84% Yes), but $357.1M is inside the bracket, so
   those prices are perfectly consistent (crowd centered ~$357-360M).
   The claimed inconsistency was an inference error, not a signal.
   **Sensing (DEEP-2026-08-05, integrating operator-notes.md §1):** finding
   siblings used to be opportunistic (only noticed when a candidate happened
   to be part of an obviously-bracketed cluster). `strategy/tools/siblings.py
   <market_id>` fetches every sibling market on the same Polymarket event in
   one call (gamma `/markets?id=` exposes an `events[0].id`, and
   `/events/<id>` returns all markets on it with live prices — verified live
   2026-08-05, a soccer exact-score event returned 17 siblings) and prints a
   `_sum_check` of their Yes prices. For a genuinely mutually-exclusive,
   fully-covering set this should sum to ~1.0 (+vig); a sum far off is a
   candidate worth the numeric-implication check above. Run it on any
   candidate whose question implies siblings exist (brackets, exact-score,
   winner-of-N, spread-vs-ML pairs) as a normal part of research.
   **Caveat found on first live use:** the test event's 17 sum-checked to
   4.24, not ~1 — but every individual price sat in a narrow 0.23-0.26 band
   regardless of how plausible the score (0-0 same price as 3-3), and each
   market's `liquidityNum` was ~$100. That is untraded/placeholder resting
   prices, not a mispriced market — nobody would leave a real 4x-overround
   arb sitting there. **Always check book depth/spread (existing `max_spread`
   veto) before treating a sum-check deviation as a signal**; a sum-check
   flag on a thin book is a data-quality tell, not an edge.
3. **Book-devig arbitration** (weakest): "my devig of scraped bookmaker odds
   beats the PM price" on a liquid market. A 1-cent-spread PM book with real
   depth is made by someone pricing off the same feeds, live — this class is
   a head-to-head contest with a sharper counterparty and went **0/7 on
   2026-07-30/31** (`1436bb727464`, `8e67cf4882bc`, `83ef29ef9493`,
   `4d5a4304a4d0`, `3cce11272d9d`, `1399450675ba`, `2c4c6a2adc0a`;
   P(0/7 | own ests) ≈ 1%). It requires `risk.json min_edge_book_devig`
   (0.07), not the base `min_edge`, and a power devig (see Estimation).
   Confirmed 2026-07-31/08-01 at zero cost: ~12 clean benchmarks devigged
   across MLB/WNBA/soccer, every tight PM book matched the devigged line
   within 1-2 cents (cycle logs 17:11Z–02:12Z).
   **Post-power-devig record (DEEP-2026-08-06): 2W/0L** — `509650e5ec31`
   (edge 0.10) and `2363018c118b` (edge 0.0795, Blue Jays +1.5), both
   power-devigged single-book lines against tight 0.01-spread PM books,
   both clearing the 0.07 floor with margin. The 0/7 above was the
   proportional-devig era; n=2 since the fix is far from a verdict, but
   the class is no longer zero-for-everything. The 0.07 floor also became
   BINDING for the first time this window (~10 clean devig edges
   0.003–0.050 skipped, funnel.jsonl 2026-08-05/06, largest A's/Reds
   0.050) — its cost is now measured in skipped candidates instead of
   hypothetical. Unchanged at n=2; the blocked 0.02–0.05 band on tight
   MLB books is exactly the sharp-counterparty zone the 0/7 came from.

Info-race status (updated DEEP-2026-08-05): the class is **2W/3L by
decision** — wins on mechanical/final facts (`2dc417ed68f6` official
print, `1e8dec1078ba` cross-market), losses on provisional or
interpretation-dependent ones (ai-leaderboard pair as one decision,
`84ec821167d5`, and now `b21e42c123a1`, settled LOST -$5 on 2026-08-04 via
a normal UMA flow: est 0.90 on state-media-sourced claims, resolver waited
out the market's 3-day conflicting-reports clause and resolved No — graded
reasoning-wrong per the DEEP-2026-08-02 pre-registration). One leg still
open: `d2dd24206542` (ceasefire No @ 0.92), 5+ days past end date with NO
UMA proposal ever submitted. Pre-registered rule-candidate, to be enacted
ONLY if BOTH pair legs settle as losses (one has; if d2dd loses too):
"multi-source verified" tightens to require at least one non-party primary
source (wire service Reuters/AP/AFP, host-government statement, or the
resolver's own named source) — a consensus composed of state media of the
parties to the event (PressTV, Mehr, TASS, Xinhua on the Iran claims) does
not qualify on its own. If d2dd wins, this stays a caution, not a rule.

NOT an edge class — **resolver-interpretation reads** (graded
DEEP-2026-08-01): "I checked the exact resolution source and it says X"
where the reading requires a judgment call (UI toggle, table choice, which
mirror). The ai-leaderboard pair (`7e753de88823`+`0bf9fe3785c6`, one
decision, -$10) lost while the operator verified the named source three
times over 22h — including after resolution — and it never moved
(journal/operator-notes.md). The fact was right; the resolution process
read it differently. Treat these below book-devig; the §Estimation
resolver-process red-flag rule applies.

## Fit rubric (DEEP-2026-08-05, operator mandate: selection is a learned
competency and was ungraded)

Estimation is measured to death (brier_delta by category/edge class); WHICH
markets I choose to spend research budget on was not measured at all — a
0-for-N day could mean "no edge existed" or "edge existed, wrong candidates
picked" or "queries built the wrong pool", and nothing distinguished them.
Score every candidate that reaches research (not just ones I bet on) against
five properties, derived from the settled record (2W/3L info-race split by
fact-finality; the Blue Jays book-devig win; the $20k-econ-vs-$400k-tennis
asymmetry):

1. **Mechanical resolution** — official print/close/countable metric/
   arithmetic, not a narrative or judgment call. (Y/N)
2. **Benchmark reachable** — open API, WebSearch-dense coverage, or
   Polymarket-internal arithmetic (siblings), confirmed reachable THIS cycle,
   not assumed. (Y/N)
3. **Edge persistence hours-to-days** — if the thesis would decay in minutes
   (a repricing race), score N; this architecture's unit of action is a
   multi-minute research session and cannot win a speed race (operator-notes
   2026-08-05 ~19:45Z). (Y/N)
4. **Bounded resolution tail** — no open-ended dispute/UMA risk of the kind
   that locked `d2dd24206542` 5+ days past end date. (Y/N)
5. **Research cost small relative to payout** — thin-liquidity/high-effort
   candidates (a $20-1000 China-CPI bracket needing a scrape) score N even if
   1-4 pass.

Fit score = count of Y (0-5). Candidates scoring ≤2 are exploration-budget
territory (see below), not default research targets. Log the score inline
with the skip/bet reason per candidate (funnel instrumentation below) — this
is what lets a deep retro grade selection the way `core/score.py` grades
estimates: which properties actually produced settled edge per research-hour.

## Funnel instrumentation (DEEP-2026-08-05, operator mandate)

Selection was ungraded because nothing recorded the funnel between "scan
pool" and "bet placed" — cycle logs only ever showed the researched subset,
never what was skipped or why. Every FULL cycle, append one JSON line to
`strategy/funnel.jsonl` (strategy-owned, not the ledger) with:
`{"cycle": "<UTC ISO>", "strategy_rev": "<short sha>", "pool_by_query":
{"<discovery.py _label>": <n>}, "researched": [{"market_id": "<id>",
"category": "<cat>", "fit_score": <0-5>, "skip_reason":
"no-edge|benchmark-unreachable|ambiguous-resolution|budget-exhausted|
market-agrees|bet-placed"}]}`. This is additive to the cycle-log prose, not
a replacement — the prose stays for narrative context, the JSONL is what a
deep retro scripts against to grade selection quantitatively (e.g. which
fit-score bucket produced the settled wins). Skip reasons must be the actual
reason, not padded — a "market-agrees" skip on something that later moved
20 points is a selection error, and only shows up in a retro if the original
call is on record.

**Skip calls get graded against outcomes by the deep retro** once the
skipped market resolves — the funnel line is the durable record and the
deep retro is the carrier. (First pass DEEP-2026-08-06: CRCL/OXY
market-agrees skips both resolved as priced — correct calls. The
DEEP-2026-08-05 watch item asking hourly cycles to grade them on
resolution day was never executed; watch items alone are not a carrier
for deferred obligations, the same lesson as the b21 settlement-retro
drop.)

## Exploration budget (DEEP-2026-08-05, operator mandate)

Selection rules learned only from wins overfit to the categories already
tried (currently: soccer/MLB book-devig, econ/cross-market). Each FULL cycle,
spend a bounded slice of research budget — target ~1 candidate, more if the
pool is rich — on something OUTSIDE the current fit profile (fit score ≤2,
or a category with n<5 settled), chosen to test a NAMED hypothesis about one
rubric property (e.g. "weather resolves mechanically; is the benchmark
actually reachable?"). Record the result in the funnel JSONL and cycle log
even when the result is "category not viable" or "benchmark unreachable" —
a ruled-out category with evidence is a selection asset, ruling nothing out
is a blind spot. This is a research-time budget only: exploration candidates
still need edge >= min_edge to get an actual bet; the exploration budget
funds looking, not lowering the bar to place.

## Market selection

**Scan horizon (OPERATOR EDIT 2026-08-03, see journal/operator-notes.md):**
default to
`python3 core/scan.py --hours 168 --min-volume-24h 0 --min-total-volume 50000`.
The `--min-total-volume` flag is new (operator patch to core/scan.py, same
date) and is REQUIRED to see past today: results page in endDate order and the
near-term universe is thousands of sub-daily markets deep, so `--hours` alone
never escapes the current day — verified, 1004/1004 candidates were day-0.
With the flag, the same scan surfaces ATP/WTA main-draw tennis 5–7 days out
(liquidity $200k–460k), central-bank decisions, and countable-metric markets.
Do NOT also apply a 24h-volume floor on a weekly window: an event five days
out legitimately has little volume today, so that filter re-creates the bug.
Evidence for all of this: 19 straight no-bet cycles on 2026-08-02/03. The 48h
window structurally selects for
whatever clears the volume filter *soon* — Icelandic, Argentine second-tier
and lower-league fixtures — which are exactly the events with no searchable
sharp benchmark, so research fails and no bet is possible. Well-covered
events (major European leagues, MLB/NBA/NFL/WNBA, big esports finals,
scheduled earnings and macro releases) mostly sit 2–7 days out. Longer
horizon also means slower feedback; that is an accepted cost, since feedback
is already gated by resolution lag, not by bet frequency. Revisit if the
weekly window produces placements without improving hit quality.

**Coverage precondition (OPERATOR EDIT 2026-08-03):** before spending research
effort on a candidate, spend ONE search establishing whether a sharp benchmark
is retrievable at all (a real bookmaker line for this exact market, an analyst
consensus, an official schedule/print). If nothing sharp is retrievable, drop
the candidate immediately and move on — do not build an estimate on aggregator
"prediction model" numbers. Scraping consumer odds portals directly does not
work from the cloud runner: forebet/oddsportal/oddspedia 403 datacenter IPs
(this is site-level bot blocking, NOT the sandbox egress policy — the earlier
"recurring egress block" diagnosis in cycle logs was wrong). WebSearch results
do work; use them. Kalshi and Manifold are different: after the operator's
10:53Z egress allowlist update, direct API fetch to
`api.elections.kalshi.com` and `api.manifold.markets` now returns 200 from
this runner (re-verified 2026-08-05 ~13:30Z, see `strategy/tools/kalshi.py`)
— use the direct fetch, it's cheaper and more precise than WebSearch.
Metaculus (`www.metaculus.com/api2`) is still 403 even with the allowlist
(site-side bot block, confirmed from a residential IP too) — WebSearch-by-name
remains the only channel there.

**Sensing addition (DEEP-2026-08-05):** `strategy/discovery.py` query 4
("econ-tag", gamma `tag_id=100328`) targets Polymarket's Economy tag with no
volume floor — Fed-rate-decision and GDP-bracket markets that resolve off an
official print/vote, the fact-finality profile the settled evidence favors,
but that queries 1-3's volume/liquidity ordering buries under sports. Check
its yield in scan's stderr each cycle; if it stays empty for several cycles
running, that is itself worth a cycle-log note (query 1 already put these
markets in front of everyone, in which case query 4 is redundant, not
broken).

**Two more search-result traps found this cycle (2026-08-05 04:16Z, zero bets
placed, all candidates failed coverage or showed no edge):**
- **Esports "odds" from WebSearch are frequently Polymarket's own price
  echoed back, not an independent benchmark.** Searches for LCK/LPL/Dota
  matchup odds returned pages titled "... Odds & Predictions | Polymarket"
  and numbers in ¢/×-multiplier format matching PM's own pricing exactly
  (e.g. "JD Gaming favored at 1.35x (74¢)" — 74¢ is a PM price, not a
  sportsbook line). Devigging these against the PM book is circular, not
  book-devig arbitrage. Treat any esports "odds" result as unusable unless
  it names an actual sportsbook (bet365, Pinnacle, GG.bet) with a price —
  and even then, WebFetch on those sites 403s, so only a search-snippet
  number naming the book counts.
- **Tip/prediction-site odds for the same soccer match can openly
  contradict each other across sources, not just diverge from PM.** SK
  Brann vs Apollon Limassol: one snippet gave Brann-win implied ~54%, a
  second gave ~65%, with PM sitting between the two (58.5%) — treat
  cross-source disagreement itself as the "mixed line" signal (existing
  rule below), not just disagreement with PM. Aarhus vs Sabah similarly
  produced an internally inconsistent snippet (a "42.6%" figure paired
  with odds of 1.47, which imply 68%) — a sign the summarizer conflated
  numbers from different parts of the source page. Don't average
  contradictory numbers into an estimate; treat as no-benchmark and skip.
- **WebSearch's summarizer can echo an assumption stated in the query back
  as if it were a found fact (2026-08-05 00:17Z).** Asked a leading
  question about Padres/Diamondbacks total pricing, the search summary
  affirmed "-110 for the 8.5 total... align with standard sportsbook
  pricing" with no actual sportsbook number anywhere in the fetched text.
  An odds claim only counts as a benchmark if it is tied to a quoted
  source figure naming the book; phrase odds queries neutrally (no
  candidate number in the query).

**Three more traps found this cycle (2026-08-05 21:16Z — exploration-budget
weather test + econ re-check + soccer 1X2, zero bets placed):**
- **Weather: mechanical resolution does not imply a reachable point
  benchmark.** Exploration-budget test of the operator's own example
  hypothesis ("weather resolves mechanically; is the coverage there?") on
  Hong Kong Aug-6 highest-temperature brackets (PM implied distribution
  peaking ~33°C across the 32-35°C bracket set). Two forecast sources gave
  materially different numbers for the same nominal date: Hong Kong
  Observatory's own 9-day forecast (the market's stated resolution source)
  said 26-31°C (max 31°C), AccuWeather (Sha Tin station, not confirmed as
  the same station HKO uses for the official reading) said 93°F ≈ 34°C — a
  3°C spread, wider than the 1°C bracket width the market is priced on, with
  station identity unconfirmed on top. Resolves the "mechanical resolution"
  rubric property Yes but "benchmark reachable" No: treat as a
  contradictory-source skip (existing rule), not an edge — the forecast
  disagreement is bigger than the thing being priced. Also corrects
  `discovery.py`'s comment: climate-weather tag 1474 was empty on
  2026-08-05, but general volume/liquidity queries surface ~79 weather
  markets independent of that tag (city-temperature brackets, $2-19k
  liquidity) — tag 1474 being empty does not mean the category is absent
  from the pool.
- **WebSearch can surface a PRIOR year's already-released actuals for a
  still-upcoming release when the query doesn't pin the year tightly and
  the event name recurs annually.** Searching for the July 2026 US jobs
  report (due 2026-08-07, not yet released) returned an fxstreet article
  (URL-dated 2025-08-01) describing that year's July jobs report as already
  landed (unemployment 4.1%→4.2%, payrolls +73k) — i.e. July 2025 actuals,
  not a 2026 forecast, surfaced by a query that said "July 2026" but didn't
  stop the summarizer from matching on "July jobs report" generically.
  Caught here because the numbers read as settled/past-tense for an event
  that hasn't happened; a less careful read could log stale-year actuals as
  current consensus. Cross-check any scheduled-release search result's
  implied publish date against the event's actual date before using it —
  don't trust the query's own year framing to have filtered correctly.
- **Same trap, multi-game-series form: WebSearch for "today's" run line odds
  on a series opener/finale skews toward the PRIOR game in the series, and
  favorites can flip game-to-game (different starting pitchers) — no bet
  placed, caught before placement (2026-08-08 02:13Z).** Scanned 5 same-day
  MLB spread candidates (NYY-1.5, WAS-1.5, ARI-1.5, CLE-1.5, TEX-1.5/-2.5),
  all part of 2-3 game series. Initial searches for "run line odds August 8"
  returned articles explicitly dated/framed for August 7 (one snippet even
  said outright "the game was played on August 7"), not the still-upcoming
  Aug 8 game the PM market resolves on. Devigging that stale line against
  today's PM ask produced an apparently huge edge (~0.10-0.14) on NYY-1.5 and
  WAS-1.5 — but a follow-up search pinned to the correct date and probable
  starters (Braves' Aug 8 starter, Reds' Chase Burns vs Nationals' Alvarez)
  showed the FAVORITE HAD FLIPPED both games: Atlanta (not Yankees) and
  Cincinnati (not Washington) were the correct day's -1.5 favorites. The
  "edge" was an artifact of benchmarking against the wrong game entirely,
  not a real mispricing — and even the corrected line was unusable, since it
  only quotes the actual favorite's -1.5 side (Braves/Reds), leaving PM's
  underdog-framed market (Yankees/Nationals -1.5) with no matching book
  quote (reverse-line-mismatch trap, existing rule). Rule: for any series
  game, confirm the search result's date AND probable starting pitcher names
  match the specific game the PM market resolves on before devigging —
  "today" in a query is not enough to prevent the summarizer surfacing the
  most recent (usually prior) game in the same series. Treat an unconfirmed
  game-date/pitcher match as benchmark-unreachable, not as license to use
  the nearest available number.
- **Odds-comparison sites report "best odds" shopped per side across
  different bookmakers, not one book's coherent line — devigging that
  composite is a version of the cross-book-mixing trap** (first named in
  schedule.json 2026-08-05 17:19Z re: Fenerbahce/Sturm Graz, now formally
  in the playbook). Boca Juniors vs Estudiantes 1X2: "best odds" search
  summary gave Boca 2.15 (one book), draw 3.15, Estudiantes 4.01, but a
  second passage in the same result gave Boca 2.22 at Betsson and draw 3.05
  at Betsson — different books' best-per-side numbers stitched together
  don't represent a single market's true vig or fair prices. Devigging it
  anyway produced a marginal ~0.06 edge on Boca-No, under min_edge_book_devig
  (0.07) regardless, but the number shouldn't be trusted even if it had
  cleared: require a single named book's full multi-way quote (not a
  "best odds across bookmakers" aggregation) before devigging a 3-way line.

**Weather exploration budget, round 2 (2026-08-06 06:25Z) — even the single
official source can disagree with itself.** The 2026-08-05 Hong Kong test
found two different sources 3°C apart. This round tested a well-instrumented
US station (Atlanta/KATL, official NWS gridpoint forecast, `3350823-26`,
4 brackets 84-91°F) on a day with afternoon thunderstorms forecast. NWS's
OWN forecast text gave "high near 90, falling to around 86 in the
afternoon" — a 4°F intraday spread inside ONE official product, before even
counting the ~83-88°F spread across secondary aggregators. On
convective/storm days, "mechanical + official source" is still not
"point-precise enough for 1-2°F brackets" — the uncertainty is physical
(storm timing), not a sourcing problem, so a second corroborating source
won't fix it the way it does for e.g. earnings consensus. Prefer non-
convective, stable-weather days for this category if revisited, or bracket
widths ≥ the NWS's own stated intraday range.

**Exploration budget, UFC main-card moneylines (2026-08-07 16:19Z, first test
of this category).** Hypothesis: "UFC main-card moneylines have dense enough
multi-book sportsbook coverage to devig, and PM either lags or tracks them
loosely enough to leave edge." Gamrot vs Salkilld (UFC Vegas 120, >24h
pre-fight): three independent books (DraftKings, FanDuel, opening line) agree
on favorite and magnitude; power devig (DraftKings) gives Salkilld fair 0.567
vs PM mid 0.575 — within 0.008. Result: **reachable** (multi-book UFC
moneyline coverage is a normal WebSearch hit, unlike the esports-echo trap)
but **no edge** this instance — PM tracks the sportsbook consensus tightly.
Category ruled in, not out; single-book UFC prop markets (KO/TKO, distance)
are a distinct, untested benchmark question — do not assume the same result
transfers to those without checking.
**Second test (2026-08-08 08:15Z), UFC 330 Makhachev vs Machado Garry
(main event, 7 days pre-fight):** multiple books agree closely (FanDuel
-390/+280, DraftKings -325/+240, two other sources -335/+275,+300) —
reachable confirmed a second time. DraftKings power devig: Makhachev fair
0.7426, Garry fair 0.2574; PM live ask Makhachev 0.76, Garry 0.25 (spread
0.01) — edges -0.017 and +0.007, both under min_edge. Same result as the
first test: reachable, tight, no edge. n=2, both no-edge — UFC main-card
moneylines look like an efficiently-tracked market, not a source of edge,
though the sample is still small.

**Exploration budget, primary-election win markets (2026-08-07 07:29Z,
distinct from the vote-share brackets below).** Hypothesis: "named-pollster
averages (not just single polls) are a reachable benchmark for primary
win-probability markets close to the vote." Wisconsin Governor Democratic
primary (2026-08-11): two independent named-pollster results (Marquette,
Main Street Action) into early August both show Francesca Hong leading
David Crowley by a wide, stable double-digit margin (38-44% vs 7-15%). PM
prices Hong Yes=0.921, Crowley Yes=0.08 — consistent with a dominant,
stable leader this close to the vote. Result: **reachable** (named-pollster
averages are a normal WebSearch hit for any actively-polled primary) but
**no edge** this instance — market already reflects the polling lead.
Category ruled in (not out): revisit closer-margin primaries, or ones
without recent, WebSearch-findable pollster figures, before generalizing
further.

**Exploration budget, politics vote-share brackets (2026-08-06 19:13Z, first
test of this category).** Hypothesis: "vote-count resolution is mechanical;
is a constituency poll a granular enough benchmark for a 10-point bracket?"
Tested on the Clacton by-election Count Binface vote-share brackets
(5 mutually-exclusive brackets, siblings-verified `_sum_check` 1.041, normal
vig). A single Survation constituency poll (2026-08-02) put Binface ~20%.
PM's bracket prices (10-20%: 44.5%, 20-30%: 42.5%, <10%: 8%, 30-40%: 6.3%,
≥40%: 2.8%) straddle the poll's 20% point almost exactly evenly — the book is
already well-calibrated to the one available poll. Result: **reachable**
(a single constituency poll is enough to benchmark a bracket set here) but
**no edge** this instance — the market isn't lagging the poll, it's pricing
it correctly. Politics vote-share brackets stay open as a category (ruled
in, not out); revisit when multiple polls disagree or a poll updates after
the book was last priced.

**Durable lessons never live only in `schedule.json` reason fields
(DEEP-2026-08-05).** The reason field is overwritten every full cycle; the
leading-question trap above was originally documented only there and
survived solely in git history. Any instrument finding or method trap
worth keeping goes in this playbook in the same cycle that finds it.

**Re-research cooldown + pacing (DEEP-2026-08-04).** A candidate researched
to a no-edge / no-benchmark conclusion stays concluded for ~2 hours unless
something new happens (material line move, news, event-status change).
Evidence: the 2026-08-04 01:15Z and 02:15Z cycles re-derived identical
no-edge conclusions on the same UCL qualifiers 55 minutes apart, both
logging "no new information"; 03:20Z partially repeated them again. When
the entire window is in that state — every candidate either concluded
within the cooldown or gated on an unreachable benchmark — set
`strategy/schedule.json` `next_full_cycle_after` to the next event
boundary (kickoff, report time, new candidates entering the scan window)
instead of running another full cycle. Deferral spends no capital; its
only cost is a delayed info-race discovery, so keep deferrals ≤3h and
never past a known event start. Settling and open-position monitoring
happen every tick regardless (schedule.json contract).

**Prefer mechanically-resolving markets.** Consistent with the fact-finality
rule, markets that resolve off an official print, close, or scoreboard
(earnings, macro releases, match results) beat markets needing a judgment call
about a source or a rules reading — the ai-leaderboard and Iran pairs cost $20
between them on resolution-process risk ($15 now settled-lost, $5 still stuck).

**Scheduled-release triage rule (DEEP-2026-08-05).** Every full cycle:
identify the scheduled-release candidates in the pool (earnings-beat,
macro/inflation/central-bank prints, countable-metric deadlines), NAME
them in the cycle log, and disposition each (research now / defer to a
stated cycle nearer the print / skip with reason). Evidence: a July
inflation bracket cluster (annual 3.3%, annual 3.4%, monthly ≥0.1%, all
end 2026-08-12) sat in the 400+-candidate pool while ~37 consecutive
cycles spent their research budget on sports/esports whose benchmarks are
known-blocked; the operator's 2026-08-04 pivot directive names exactly
this category. These markets have reachable, mechanical benchmarks
(official statistical releases, analyst consensus) — read the description
first to pin the exact source and threshold, and check book depth/spread
before treating the mid as real. Current priority: the July inflation
cluster — bracket legs are mutually exclusive siblings, so cross-market
consistency (probabilities summing >1 across brackets) is checkable
arithmetic, our strongest settled edge class (`1e8dec1078ba`).

**Pre-research event-time check (DEEP-2026-08-04, consolidating the two
2026-08-03 findings below).** For any market tied to a scheduled event
(match, series, scheduled report/print): pin down the actual start time —
from the market description or one targeted search — BEFORE deeper
research. `end_date`, `outcome_prices`, and scan mids are all unreliable
about whether the event has started. If the event has started, or its
status cannot be verified, skip. Evidence: the tennis and MLB findings
below, plus 2026-08-04 04:16Z — Draper and Tsitsipas matches showed
plausible paper edges against real bookmaker lines, but every live-score
source (Sofascore, Flashscore, ESPN, TennisExplorer, Olympics.com) 403'd
and match status could not be pinned down; both correctly skipped. An
unverifiable event is not a discount on the edge, it is a veto.

**`end_date` is not the actual match/event time for tennis draws (2026-08-03
finding).** Six National Bank Open / Canadian Open / DC Open candidates in
one scan all carried `end_date` of 2026-08-09 or 2026-08-10 (the tournament's
last day), but WebSearch on the actual matchups showed real scheduled times
of 2026-08-02/08-03 — e.g. Berrettini vs Navone: scan `end_date` 2026-08-10,
actual scheduled time 2026-08-03 16:35 UTC (today); Frech vs Jeanjean and
Boisson vs Ruzic: actual dates 2026-08-02 (yesterday), yet their live books
were still mid-range (0.70-0.88), not resolved-looking. `end_date` for these
markets is evidently a tournament-level fallback/dispute deadline, not the
match's real time — do not assume a scan candidate is safely pre-match
because its `end_date` looks days out. Verify the actual scheduled time (or
live status) per-candidate before researching or betting; if it can't be
pinned down, treat as possible in-play and skip (same reasoning as the
esports in-play rule). This cycle, Fritz vs Jodar showed a similarly
suspicious pattern independent of this issue: pre-match sportsbook odds
implied Fritz ~65%, but the live PM book was 0.92-0.93 bid/ask with >20k
depth — almost certainly in-play with Fritz already dominant, so the
sportsbook "benchmark" was stale, not the PM price. Skipped.

**Scan does not flag in-play status for single-game moneylines (2026-08-03
finding).** WSH/PHI and STL/NYY MLB moneylines both showed large price
divergence from pregame bookmaker consensus on deep, 1-cent-spread books
($170k-295k liquidity) — looked exactly like a book-devig edge. Checking
wall-clock time against the listed first pitch (in the market description,
not `end_date`) showed both games had started 13-38 minutes earlier; the
price move was in-play information, not a mispricing. `outcome_prices` and
`end_date` are both stale/uninformative about in-play status. Before
researching or betting any single-game team-vs-team market (not just
esports), check current time against the actual listed start time in the
description; if the game has started, skip — same rule as esports in-play,
now confirmed to apply to traditional sports moneylines too.

**MLB `Spread: TeamX (-1.5)` markets are per-team, not per-game — verify
which team is the actual moneyline favorite before searching for a
bookmaker run line (2026-08-06 15:41Z finding, 5-game sample).** Polymarket
creates a separate -1.5 spread market for each team, e.g. an event can
carry `Spread: Team A (-1.5)` and/or `Spread: Team B (-1.5)` independently,
and which ones exist varies by game — sometimes only the underdog's (an
alternate line: "underdog wins outright by 2+", a much rarer event than
the standard "favorite lays 1.5"). A single bookmaker "run line" search
(favorite -1.5 / dog +1.5) only prices the FAVORITE's -1.5 side; if PM's
listed market is for the underdog's -1.5 instead, the numbers aren't
comparable at all — buying either side off that mismatch is not a devig,
it's noise. Confirm the PM moneyline favorite (or a moneyline search)
matches the team named in the PM spread market before devigging against a
bookmaker run line. In this cycle's sample: Marlins/Braves and
Diamondbacks/Padres had PM markets on the underdog/coinflip side only
(skipped, mismatched); Twins/Royals had a bookmaker run-line search that
named the wrong favorite entirely (contradicted by both PM's and a second
search's moneyline — discarded as an unreliable source, another instance
of the cross-source-contradiction rule); only Tigers/Mariners had a
verified favorite-side match, and its devig edge (0.014-0.018) came in
under `min_edge_book_devig` (0.07) on both legs — no bet, but the match
methodology held up and is worth reusing.

**Selection pre-filter for this category (DEEP-2026-08-08, from the
funnel record).** The 2026-08-07/08 window spent 15 of 35 research slots
on mlb-spreads and got 9 benchmark-unreachable skips and 0 bets —
`strategy/funnel.jsonl` cycles 04:15Z–02:13Z. The unreachables are
structural, not bad luck: an underdog-framed `Spread: TeamX (-1.5)` (X is
not the book favorite) has NO matching book quote by construction (books
quote favorite -1.5 / dog +1.5; dog -1.5 is a rarer alt line few books
carry), and series games add the wrong-day/starter-flip trap on top. So
run the two cheap checks AT SELECTION TIME, before the candidate gets a
research slot: (1) one moneyline lookup to confirm the PM spread's named
team IS the favorite — if not, log the candidate straight to the funnel
as benchmark-unreachable (fit-score benchmark=N) and spend the slot
elsewhere; (2) for any series game, the date+probable-starter pin
(2026-08-08 02:13Z rule above) before any devig. Full research effort is
reserved for favorite-framed, date-pinned spreads — the only
configuration that has ever produced a usable benchmark match in this
category (Tigers/Mariners 2026-08-06; the 2363018c118b win).

Work from `core/scan.py` output (protected filters already applied).
Prefer, in order:
1. **Earnings-beat markets** (`Will X beat quarterly earnings?`) — resolve
   same evening. Research: consensus EPS estimate, whisper numbers, the
   company's historical beat rate (most large caps beat 75–85% of quarters),
   recent guidance, peer results this season. Suspect mispricing when the
   price is far from the historical beat base rate without news to justify it.
   Sharpened from the 2026-08-04/05 CRCL and OXY passes (3 cycles, no bets):
   - **GAAP vs non-GAAP is a mandatory first check.** The market's fixed
     threshold names a basis; consensus numbers usually don't. CRCL's
     threshold was GAAP $0.16 while every findable consensus ($0.165-$0.19)
     was non-GAAP — applying one to the other is a methodology error, not
     an edge (04:16Z catch, correct skip).
     **Extension (2026-08-06 03:13Z, ABNB `3074288`):** GAAP-specific
     consensus is frequently just unfindable via WebSearch, not merely a
     basis-mismatch risk — every source for Airbnb's Q2 2026 report
     (Yahoo, TipRanks, StockStory, MarketBeat) reported non-GAAP/adjusted
     EPS ($1.19-$1.26) while the market's threshold was GAAP $1.25; no
     source gave a standalone GAAP figure. Treat "no GAAP-basis number
     found" as benchmark-unreachable by default for GAAP-threshold beat
     markets, the same as a basis mismatch — don't fall back to the
     non-GAAP consensus as a stand-in.
   - **"Consensus clears the threshold" is not an edge when PM already
     prices it ≥~0.80** (CRCL 0.845, OXY 0.91): the market has the same
     consensus. The tradeable shapes are (i) PM price *contradicting* the
     consensus direction, or (ii) a threshold sitting far outside the
     analyst range while PM lags near base rates. Absent those, log
     "market confirms, no edge" once and let the cooldown hold it.
   - **Graded (DEEP-2026-08-06):** CRCL (`3074337`) and OXY (`3074403`)
     both resolved YES — the market-confirms skips at 0.845/0.91 held up;
     no edge was foregone by declining to buy an unmodeled favorite.
     First outcome evidence for this rule (n=2, keep grading).
   - **Graded (DEEP-2026-08-07, the full 2026-08-06 reporting slate):**
     all six Aug-6 reporters resolved YES (beat). Per disposition:
     ED (`3074274`, skipped no-edge) — the tentative ~0.045 edge was on
     **No**, built on self-inconsistent WebSearch beat-rate data; ED beat,
     so the data-quality veto avoided a -$5 loss. AKAM/Yelp/DBX/NET
     market-agrees skips all resolved as priced — market-confirms rule now
     outcome-graded at n≈6 with zero foregone edge. MNST (`3074320`,
     benchmark-unreachable: GAAP trap + 0.10 spread) beat — the bullish
     4/4-beat signal would have won, so fails-closed rules have a
     measured cost column now (1 foregone win) as well as a savings
     column (ED, CRCL-basis catches); at n=1 each way, keep the rules,
     keep counting both columns. ABNB (`3074288`, fails-closed on
     unfindable GAAP consensus) beat — outcome consistent with its high
     price, skip graded neutral/cheap insurance.
   - **Graded (DEEP-2026-08-08):** UAA (`3089555`) resolved YES. The
     no-signal skips (threshold $0.02 = consensus exactly, $187 book,
     last priced ~0.52-0.62) grade as process-correct /
     outcome-uninformative — with no directional signal there is no
     foregone-edge claim either way on a coin-flip-priced market.
     Market-confirms tally unchanged at n≈6, zero foregone edge.
2. **Soccer daily match markets** — resolve at final whistle. Research: recent
   form, injuries/rotation news, home/away splits, league table stakes,
   odds at conventional bookmakers (the sharpest available benchmark — if
   Polymarket materially diverges from bookmaker-implied probability, that is
   the signal).
3. **Esports pre-match only** (never in-play — the book moves faster than I
   can research). Research: team ratings (HLTV for CS, etc.), map pools,
   recent roster changes. Thin books here: check the spread before trusting
   the price.
4. **Short-horizon news/politics** — only when a resolution-relevant fact is
   already public but not yet priced. Caveat (2026-07-30): "not yet priced"
   must mean the BOOK, not the scan mid. Near-resolution markets (commodity
   daily closes, IPO-day closes) show stale mids while makers have already
   moved asks to 0.98+. The window between fact-public and book-repriced is
   usually gone by the time scan surfaces it — verify with the live book
   before spending research time.

Avoid: anything the protected config bans (sub-daily crypto), in-play markets,
markets whose resolution criteria I don't fully understand after reading the
description, books with spread > risk.json `max_spread` (scope below).

### Spread-rule scope (DEEP-2026-08-01)

`max_spread` is a HARD veto for book-devig / benchmark-derived bets and for
any market where my own estimate is uncertain: a wide book there means the
benchmark comparison is unreliable and the market is telling me something I
don't know (correctly applied to ENA/XRP retrospective-fact markets,
2026-08-01 03:11Z).

Narrow exception — **structural info-race only**: positions are held to
resolution (never exited) and fill at the ask, so exit liquidity is
irrelevant; a wide bid/ask on a market whose resolving fact is verified by
multiple independent sources is the signature of the inattentive book this
class targets (both structural wins came from 0.01–0.06-spread books; all
seven book-devig losses from 1-cent books). A bet may exceed `max_spread`
only if ALL hold: (1) info-race class, fact multi-source verified;
(2) edge at the ASK ≥ `risk.json min_edge_wide_book` (0.30); (3) the cycle
log explicitly states the bid/ask/spread and invokes this exception.

**Tightened (DEEP-2026-08-05, enacting the b21-loss pre-registration from
DEEP-2026-08-02):** condition (1) now additionally requires the resolving
fact to be FINAL/MECHANICAL (per the fact-finality requirement) and
confirmed by at least one non-party primary source. Evidence:
`b21e42c123a1` — the bet whose profile partly calibrated this exception —
settled lost; its "multi-source verified" fact was state-media consensus
on a contested claim, and the resolver read it the other way. A wide book
plus a contested fact is the market pricing resolution risk, not
inattention.

Violation on record: `b21e42c123a1` (2026-07-31 23:15Z) was placed at
spread 0.13 with no mention of the spread in the cycle log — a silent skip
of a written check. Whatever a bet's merits, a rule that seems wrong gets
flagged in a retro and proposed for change; it does not get silently
ignored. Every placement's cycle-log entry must state the spread check
from now on.

## Open-position monitoring (DEEP-2026-08-02)

Positions are held to resolution — never exited — but their live prices
are free information about the resolver. **REQUIRED line in every cycle
log, no exceptions** (sharpened DEEP-2026-08-03 after 10 of 19 cycles
silently skipped it — including 23:11Z, the cycle that placed
`84ec821167d5` and missed the start of its 0.14 collapse): for each open
position past its market end date, fetch the current book and log
`position id, entry, live bid/ask, mid, adverse move`; if none qualify,
log the literal line "open-position monitor: none past end date". Any
adverse move ≥ 0.10 from entry must be called out explicitly.
Evidence: `d2dd24206542` repriced from ~0.08 Yes at entry to ~0.545 Yes
over 2026-08-01/02 — 46 points against us on a thesis logged as
"structurally impossible" — and ~28 consecutive cycle logs repeated
"awaiting official resolution" without noticing. A sustained multi-day
adverse repricing on an unresolved market is resolver-process evidence
(dispute, rules reading we don't have) and feeds the position's eventual
grading; it is NOT a reason to exit (we can't) or to average in (ledger
forbids add-ons).

## Estimation method

1. Read the resolution criteria in the market description. Bet on what
   *resolves*, not what's likely in spirit.
2. Form an independent estimate BEFORE looking hard at the market price
   (anchoring guard). Write the estimate down in the rationale.
3. Identify the sharpest external benchmark (bookmaker odds, analyst
   consensus, base rates) and reconcile.
   - **Cross-venue divergence (added DEEP-2026-08-05, corrected 2026-08-05
     ~13:30Z after the operator's egress allowlist update):** a real-money
     venue pricing the same event (Kalshi, CME FedWatch for Fed decisions) is
     a benchmark at least as good as a devigged bookmaker line. Direct API
     fetch to `api.elections.kalshi.com` now returns 200 from this runner
     (was 403 before the 2026-08-05 10:53Z allowlist change) — use
     `strategy/tools/kalshi.py events --series-ticker <t>` /
     `markets --series-ticker <t>` (or `--event-ticker`) to pull live
     yes/no bid-ask directly, no auth needed for public market data. Check
     BOTH sides' bid/ask, not just one side's ask, before calling it a
     divergence — and confirm the Kalshi and Polymarket contracts settle on
     the same terms (same strike/threshold, same official source) before
     treating a price gap as edge rather than a definitional mismatch.
     `api.manifold.markets` is also 200 now but Manifold stays play-money —
     reference only, never a benchmark. `www.metaculus.com/api2` is STILL 403
     even with the allowlist (site-side bot block, confirmed from a
     residential IP too) — for Metaculus, WebSearch for the venue's pricing
     by name (e.g. "Kalshi Fed rate decision September odds") is still the
     only channel, same pattern as sportsbook odds coverage.
   - **Kalshi has a per-1%-bracket "Above X%" ladder for the unemployment
     rate, series `KXU3-<YY><MON>` (2026-08-06 15:41Z finding, not the same
     series as the payrolls/CPI ladders already validated 2026-08-05
     13:45Z).** Differencing adjacent `Above` contracts gives an implied
     point distribution to compare against Polymarket's own bracket set —
     for July 2026 it disagreed with PM's internal ranking (Kalshi peaked
     4.2% at ~0.32 with 4.1%≈0.21/4.3%≈0.28; PM priced 4.3% highest at 0.335
     with 4.1% close behind at 0.295, understating 4.2% and overstating
     4.1%/4.3% by several points each vs the Kalshi-implied numbers). Real
     divergence, but PM's per-bracket books on this cluster are thin and
     wide (0.07-0.10 spread on the 4.1%/4.3% legs, `journal/ledger.jsonl`-
     verified via `quote.py`) — over `max_spread` (0.06), a hard veto for a
     benchmark-derived bet (Spread-rule scope below), so the divergence is
     unreachable, not exploitable. Log this as a distinct benchmark-reachable-
     but-book-too-wide skip, and re-check the ladder near the 2026-08-07
     08:30Z BLS release in case the book tightens.
     **Recheck (2026-08-06 19:13Z, ~13h before release):** book tightened to
     0.05 spread (now under `max_spread`) — the wide-book veto no longer
     applies, but the edge itself doesn't clear the bar: best ask-edge across
     the 4.0-4.3% legs is only 0.021-0.03 (4.1% No highest at 0.025, 4.3% No
     at 0.03), under `min_edge` 0.04. The divergence direction is unchanged
     from 15:41Z; it was never blocked on spread alone once you do the actual
     ask-edge arithmetic — say so accurately next time rather than defaulting
     to "unreachable." **`kalshi.py` usage note:** `markets --series-ticker
     KXU3-26JUL` silently returns nothing — `KXU3-26JUL` is the *event*
     ticker, not the series ticker (the series is just `KXU3`, spanning all
     months). Use `markets --event-ticker KXU3-26JUL` to scope to one month's
     ladder; `--series-ticker KXU3` returns all months unscoped. The tool
     itself is correct (verified against the raw API this cycle); this was a
     call-site error worth remembering so it doesn't cost another cycle.
     **Outcome graded (DEEP-2026-08-08): July printed 4.1%** (FRED UNRATE,
     2026-07-01 row, pulled directly). Both venues' modes were wrong —
     Kalshi-implied peak 4.2% (~0.32), PM peak 4.3% (0.335) — so the
     divergence the six-check thread was chasing was two thin, wrong
     distributions disagreeing, not information. The noise-read skips were
     validated concretely: the final pre-release candidate (4.1% No at
     edge 0.04, exactly at min_edge, 07:30Z) was on the wrong side of the
     print and would have lost. Rule: **a Kalshi-vs-PM price divergence is
     a benchmark only when one side has a mechanical anchor** (official
     nowcast, arithmetic on published components); two order books
     disagreeing about the same unknown is a spread, not an edge — trade
     it only with an independent estimate of the underlying, held to the
     same standards as any other estimate. Honest caveat: my own
     fair-value lean pointed away from the outcome (read 4.1% as
     overpriced at ~0.295), so the discipline saved a loss the estimate
     would have taken. n=1; grade the next ladder print the same way.
   - **Devig with `strategy/tools/devig.py`, and use the POWER number for any
     side priced below ~0.60.** Proportional (divide-by-sum) devig spreads
     the vig evenly, but books load vig onto longshots (favorite-longshot
     bias) — at typical 5-7% overrounds it inflates the cheap side by
     ~0.5-1.5 cents (Sun ML +144: proportional 0.390 vs power 0.381), a
     quarter-to-a-third of a 0.04 "edge". All 7 losing bets of
     2026-07-30/31 bought the cheaper side (0.34-0.52) off proportional
     devigs (DEEP-2026-07-31).
   - **Check line freshness before calling a divergence an edge.** Scraped
     aggregators lag; PM sports makers don't. If ANY book already matches
     PM's number, or reports are mixed, assume PM reflects the current line
     and the gap is a line move you saw late — not edge. Evidence:
     `8e67cf4882bc` (entry note said "one book 4.5" while betting against
     -4.5; Sky covered) and `1436bb727464` (aggregator "consensus 188-189"
     vs PM 185.5; Under hit).
4. Only bet when |my estimate − fill price| ≥ the min edge for the edge
   class (`min_edge` for structural, `min_edge_book_devig` for book-devig
   arbitration) AND I can name the specific reason the market is wrong.
   "I feel it's mispriced" is not a reason.
   - **A literal source-reading vs a >0.90 market consensus is a resolver-
     process red flag, not just a confident fact.** Evidence (2026-07-31):
     `7e753de88823` (Moonshot Yes) bet that a named leaderboard source
     showed Moonshot on top; the operator verified that exact source
     directly, three times spanning 22h including 2.5h *after* resolution,
     and it never moved off the same reading — yet the market resolved the
     other way, at ~93% confidence priced in advance. The market's price
     predicted the resolution better than the literal source read did. When
     your reading of a resolution-relevant source disagrees with a >0.90
     consensus, that consensus likely embeds something about HOW the
     resolver reads the source (which table/toggle/view, dispute
     precedent) that a fact-only check doesn't capture. Before betting
     against that kind of consensus, name specifically what the crowd
     might be missing about the *resolution process* — not just re-confirm
     the fact. This applies to resolution reads requiring a judgment call
     (UI settings, which mirror/table); it does not apply to mechanical
     resolution sources (a number printed in an official filing/API),
     which aren't implicated by this evidence.
   - **Outside-view veto on large claimed edges (DEEP-2026-08-07).** The
     settled record splits cleanly on claimed edge size: bets claiming
     edge > 0.10 are **0W/5L, -$25, brier_delta +0.4587** (agent brier
     0.5714 vs market 0.1127 — catastrophically worse than the market:
     `7e753de88823` 0.535, `0bf9fe3785c6` 0.617, `b21e42c123a1` 0.75,
     `84ec821167d5` 0.49, `d6d71ab454dc` 0.17); bets claiming edge ≤ 0.10
     are 6W/8L with brier_delta **+0.0041** — market-level. All five
     large-edge bets were interpretive forecasts where I held NO
     information the market lacked (a UI-toggle reading, two war-news
     readings, a box-office press reading, an intraday-volatility
     extrapolation from public spot data). Mechanism, not just small-n
     correlation: on a liquid book, a 15-75 point disagreement with the
     price is far more likely to be my model missing something than the
     entire market missing something. Rule: before placing any bet with
     claimed edge > 0.10, write down the specific fact or arithmetic the
     market structurally CANNOT have priced (an official number already
     published, a cross-market inconsistency computable from live books).
     "My forecast disagrees with the price" never qualifies. If no such
     fact exists, either shrink the estimate toward the market until the
     edge is ordinary, or skip. (The 0.10 boundary is post-hoc at n=19 —
     treat it as a red-flag trigger for this test, not a proven numeric
     threshold; the test itself is the rule.)
   - **Same-day commodity price-threshold bets on a live geopolitical
     conflict complex: don't extrapolate "realized range so far" as a
     volatility bound (DEEP-2026-08-06).** `d6d71ab454dc` (WTI closes above
     $77) estimated P(Yes)=0.12 mid-day from "needed move ($1-2.4) exceeds
     realized range so far (~$1.40)" plus a same-day bearish catalyst
     (Iran/Strait-of-Hormuz deal hopes) — WTI closed $77.75 (+3.37% on the
     day), the tail move happened, in the opposite direction of the cited
     catalyst. This contract sits on the same US-Iran conflict complex as
     `d2dd24206542` (a ceasefire position that has itself round-tripped
     0.92→0.14→0.20+ on headline swings) — that complex produces discrete
     headline-driven jumps, not bounded continuation from a mid-day
     snapshot. n=1, not enough for a numeric floor, but treat "range so
     far" reasoning on conflict-linked commodities as unreliable; either
     discount confidence well below what the range-based math implies, or
     require a catalyst check close to the actual close rather than hours
     before it.
5. **Check the live book first** (`python3 strategy/tools/quote.py
   <clob_token_id>`, token ids are in scan output; if the sandbox blocks it,
   `curl -s "https://clob.polymarket.com/book?token_id=<id>" -o reports/book_<x>.json`
   and read the file — fetch into `reports/` not `/tmp`; the sandbox blocks
   reading `/tmp` (learned 2026-07-30 cycle 3). Delete the scratch files
   before committing. `scan.py` outcome_prices are stale mids; fills happen
   at the best ask. Apply `min_edge` to the ASK, not the scan price.
   Evidence (2026-07-30 cycle): REF "No" scan mid 0.833 → ask 0.999
   (rejected); NG "Up" scan mid 0.915 → filled 0.95, edge collapsed to 0.02;
   WTI "Down" scan mid 0.926 → best ask 0.98 vs est 0.97 (negative edge,
   skipped). Stale mids cut BOTH ways: Corinthians win scan mid 0.455 →
   live book 0.42/0.43 (2026-07-30 cycle 4) — a marginal-looking edge on
   the mid can be a qualifying edge at the ask, so check the book before
   discarding near-threshold candidates too.

6. **One position per market+outcome** — the ledger rejects add-ons even at a
   better price (2026-07-30 cycle 5: Corinthians Yes re-entry at 0.42 vs held
   0.43 rejected). If new evidence strengthens a held position, capture the
   edge via a correlated sibling market instead: e.g. holding "Team A win Yes",
   the extra edge showed up in "Team B win No" (devig 0.78 vs ask 0.74) —
   sibling 1X2 legs are priced independently enough to diverge.
   Sharpened (DEEP-2026-07-31) — know which pair type you're building:
   - **Hedge-like pair** (e.g. "A win Yes" + "B win No": a draw splits them):
     partial offset, acceptable. Evidence: `2c4c6a2adc0a`+`1e8dec1078ba`
     went 1W/1L on a draw, net -$3.24.
   - **Same-direction pair** (e.g. "A win No" + "B win Yes": both lose if A
     wins): this is doubled event exposure, not extra edge capture. Only
     take it when each leg independently clears its edge threshold, and
     never exceed `risk.json max_stake_per_event_usd` on one underlying
     event. Evidence: `821d54f6b7c8`+`53283a95e7bb` (open) — $10 rides on
     "Bucaramanga doesn't win".
   - Retros must grade a correlated pair as ONE decision (net P&L per
     event), not as independent wins/losses.

## Known unknowns (to resolve with data)

- Which categories actually have positive brier_delta for me. (Bet small and
  wide until `core/score.py` shows n≥30 per category.)
- Whether thin esports books are exploitable or just wide.
- Whether earnings markets are efficient at pricing whisper numbers.
