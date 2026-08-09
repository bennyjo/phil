# Operator notes

Observations from the human operator's side that the cycle agents cannot
reconstruct after the fact. Treat as evidence in retros.

## 2026-07-31 18:35Z — ai-leaderboard pair: resolution contradicted the source

Positions `7e753de88823` (Moonshot Yes @ 0.065) and `0bf9fe3785c6`
(Alibaba No @ 0.083) both lost: Moonshot market resolved No (closed, 0/1),
Alibaba market at 0.9995 pending close.

Operator verification timeline against the named resolution source
(lmarena.ai/leaderboard/text, which 301-redirects to arena.ai/leaderboard/text;
Text Arena Overall, adjustments shown as "None"):

- 2026-07-30 ~20:15Z (entry): kimi-k3-max rank 11 (1486±10), best Qwen =
  qwen3.7-max-preview rank 21 (1475±10). Full rank-8..25 table captured.
- 2026-07-31 11:50Z (4h before check time): unchanged (kimi 11, qwen 21).
- 2026-07-31 18:35Z (2.5h AFTER the 16:00Z check time and after Moonshot
  resolved No): STILL unchanged — kimi 11, qwen3.7-max-preview 21, and no
  new qwen model was added (full qwen list captured, best is rank 21).

Conclusion: the leaderboard fact the description points at did not move.
The resolution went the other way anyway. Candidate explanations, for the
deep retro to weigh:

1. Resolver used a different view than our reading of "style control off"
   (e.g. the style-control-ON default view, where press coverage placed
   Qwen 3.7 Max at #5 overall — i.e., OUR interpretation of the settings
   toggle may be inverted, or the resolver's was).
2. lmarena.ai may serve a different table than the arena.ai redirect target
   we sampled.
3. UMA-style resolution process settled on the 92¢ consensus reading and
   no one disputed — market-consensus-as-resolution-precedent risk.

Lesson candidate (deep retro to formalize): a resolution-source read is a
bet on HOW THE RESOLVER WILL READ IT, not on the underlying fact. When our
literal reading contradicts a 90¢+ market consensus, the consensus embeds
resolution-process knowledge (who proposes, which view they use, dispute
economics). The 6.5¢ price may have been an approximately correct price on
the resolution process even while being a wrong price on the leaderboard
fact. Proposed rules: (a) treat "my reading vs >0.90 consensus" as a red
flag requiring an explanation of what the crowd knows about the resolver,
not just the source; (b) cap total exposure on any single
resolution-interpretation thesis (this pair doubled it: -$10, the exact
correlated-exposure pattern from DEEP-2026-07-31 §d); (c) prefer
resolution-source plays where the criteria are mechanical (a number in an
official filing/API) over ones requiring a UI-settings interpretation.

## 2026-08-03 19:10Z — the "egress block" on odds sites is a misdiagnosis

Cycle logs from 2026-08-02/03 attribute repeated HTTP 403s from oddsportal,
forebet, oddspedia, bet-experts and betmines to "recurring egress block".
Operator tested the same URLs from a residential connection:

- www.forebet.com → **403 from a normal laptop too** (site-level bot block)
- www.oddsportal.com → 200 from residential IP only
- api.the-odds-api.com → 401 (reachable; needs an API key)

Conclusion: these are anti-bot / datacenter-IP blocks at the sites, not the
sandbox egress policy. An allowlist would not fix them, and no amount of
retrying will. Two consequences for strategy:

1. **Scraping consumer odds portals is not a viable benchmark channel from a
   cloud runner.** WebSearch results (which are fetched by Anthropic's
   infrastructure, not the sandbox) DO work and have produced usable
   multi-book consensus before — but only for well-covered events.
2. **Market selection is therefore part of the data problem.** The scan has
   been surfacing Icelandic, Argentine second-tier and lower-league fixtures
   because they clear the volume filter in a 48h window. Those are exactly the
   events with the thinnest public odds coverage, so research fails and the
   cycle no-bets. Prefer events with deep, searchable coverage (major European
   leagues, MLB/NBA/NFL/WNBA, large esports events, scheduled economic and
   corporate releases) even when the raw scan offers "cheaper" candidates.

Operator action pending: a the-odds-api.com key (free tier, ~500 req/month)
would give clean JSON lines for major leagues and remove the scraping
dependency entirely. Not yet provisioned — do not assume it exists.

## 2026-08-03 19:10Z — three positions stuck unresolved, capital and attention locked

`b21e42c123a1` and `d2dd24206542` (Iran pair) are now 4 days past their
2026-07-31T23:59Z end date with `closed: false` and no UMA resolution;
`84ec821167d5` (Spider-Man) marks at ~0.002 but also has not settled. The
open-position monitor is correctly flagging all three as adverse.

Nothing to do about resolution lag itself, but two behaviors are missing:
mark-to-market losses on stuck positions should be reported in the score view
rather than only in cycle logs, and a position that is N days past end date
without resolution should be escalated in the retro as a *process* datapoint
(which market types stall?) rather than silently re-flagged every hour.

## 2026-08-03 19:25Z — root cause of the no-bet drought: the scan could not see past today

Diagnosis correction (supersedes the market-selection note above, which was
right about symptoms but wrong about cause). `core/scan.py` pages the gamma
API in `endDate` order from now. The near-term Polymarket universe is
thousands of sub-daily markets deep (5-minute crypto candles, in-play
derivatives), so pagination exhausts the `--limit` long before reaching
tomorrow. Verified: `--hours 168 --min-volume-24h 0 --limit 2000` returned
1004 candidates, **all of them day-0**. The horizon flag was never the
binding constraint — the agent could not have found well-covered events no
matter how it tuned it, and every "no qualifying candidate" cycle log was
technically accurate but structurally misleading.

Operator patch (protected core, so agent-side rules unchanged): `scan.py`
gains `--min-total-volume`, passed server-side as gamma's `volume_num_min`.
With `--hours 168 --min-volume-24h 0 --min-total-volume 50000` the same scan
returns 32 candidates, 19 of them 1+ days out, including ATP/WTA main-draw
matches at $200k-460k liquidity, a Bank of Mexico rate decision, and
countable-metric markets. Note the interaction: a 24h-volume floor must NOT
be combined with a multi-day window (an event five days out has little volume
today), which is why the two flags move together.

Why this matters beyond the fix: for two days the agent reasoned impeccably
about a candidate pool that was an artifact of a tooling limit it could not
see and was forbidden to edit. Its retros correctly recorded "no qualifying
edge" and correctly declined to force bets; nothing in its own evidence could
have revealed the cause. Worth grading in the next deep retro as a lesson
about the limits of self-improvement inside a fixed harness — the agent can
optimize its judgment, but not its instruments.

## 2026-08-04 ~06:45Z — UMA look on the Iran pair (proposals item, now done)

Checked gamma for both markets directly:

- `b21e42c123a1` (Iran military action vs Gulf State): **resolved No overnight**
  via a normal UMA flow — `umaResolutionStatuses ["proposed"]`,
  `umaResolutionStatus resolved`, `umaEndDate 2026-08-04T06:02:33Z`, final
  prices Yes=0/No=1. resolve.py already settled it (-$5). Nothing pathological
  in the process; the delay matched the market description's own "3 full
  calendar days for conflicting reports" clause (Jul 31 end + 3 days → Aug 4).
- `d2dd24206542` (US x Iran ceasefire, holding No @ 0.92): **no UMA proposal
  has ever been submitted** — `umaResolutionStatuses []`, `closed false`,
  4+ days past end date, Yes trading ~0.515. Reading: the same 3-calendar-day
  clause ran out with reports still conflicting, and no proposer will stake a
  bond on a genuinely contested ~50/50 fact. The oscillating price is not a
  resolver leaning — it is the absence of any resolution attempt. Expect
  settlement only when facts converge or someone risks a proposal+dispute.

Process datapoint for retros: "by <date>?" geopolitical markets with
conflicting-reports clauses have an UNBOUNDED resolution tail — the end date
is when trading stops mattering, not when capital frees. Cost so far: $5 of
bankroll and a monitor line locked for 4+ days. Worth weighing as a liquidity
cost when sizing this market type; category unchanged otherwise.

## 2026-08-05 — reachable benchmark channels: the drought is a sensing problem

Context for the cycle agent and the deep retro. The placement drought
(0 bets in ~21 ticks) is benchmark reachability, not thresholds — and the
odds-API rejection stands (see proposals.md, re-open condition unchanged).
Meanwhile the settled evidence now points one direction: across 5 graded
decisions, mechanical/final facts are 2W-0L and interpretation-dependent
facts are 0W-3L. The channels below are all reachable from the datacenter
(no consumer odds portals, no keys) AND they feed exactly the fact-final
categories the evidence favors. Integrate them through what you own —
strategy/discovery.py queries and playbook research procedure; the deep
retro audits the integration like any other edit.

1. **Polymarket-internal cross-market consistency (no external source at
   all).** Related markets on one event must be jointly consistent:
   moneyline bounds the spread price, sibling outcomes must sum sanely,
   derivative legs imply each other. Every check is arithmetic on CLOB
   books you already fetch. One event with 2+ related markets becomes
   several candidates whose benchmark cannot 403. This feeds the
   cross-market edge class — currently your best-evidenced class.

2. **Cross-venue divergence via open APIs.** Kalshi publishes market data
   as clean JSON (econ, weather, news events that overlap Polymarket);
   Manifold and Metaculus have fully open APIs. A real-money venue
   disagreeing with Polymarket on the same event is a benchmark at least
   as good as a devigged bookmaker line, and these platforms want to be
   fetched. Caveats: check the contracts resolve on the same terms before
   treating a divergence as edge; Manifold is play-money — reference, not
   benchmark.

3. **Categories whose resolution source IS the research source.**
   Scheduled economic prints (central-bank and statistics-agency pages,
   FRED), countable metrics (chart positions, on-chain data via open
   APIs), and weather markets if scan surfaces them (official forecast
   JSON is free). Here your estimate comes from an official number, not a
   narrative read — the exact fact-finality profile of your two wins.

4. **discovery.py is only three generic queries.** Gamma supports tag_id;
   per-category tag queries would surface mid-liquidity markets in
   cheap-to-research categories that the volume-ordered queries bury
   under sports. The right floor is asymmetric: a $20k econ market with a
   free official benchmark is worth more research time than a $400k
   tennis match with no reachable status source. Encode that asymmetry in
   the queries.

One warning attached: the calibration z is -2.61 — estimates run
overconfident — so more candidates through an unchanged estimation pipe
just loses faster. The channels above are chosen so the estimate itself
comes from arithmetic or an official print rather than interpretation;
prefer them for that reason, not only for reachability. This note is a
mandate to sense, not a mandate to bet.

## 2026-08-05 10:53Z — egress allowlist updated; §2 reachability claim corrected

The 07:19Z cycle was right to flag it: the §2 note above asserted
Kalshi/Manifold/Metaculus are reachable, without testing from the runner.
Correction and fix, in two parts.

**Operator action taken:** the cloud environment's network allowlist
(the routine's environment, Network access → Custom) now includes:

    api.elections.kalshi.com
    api.manifold.markets
    www.metaculus.com
    fred.stlouisfed.org
    api.bls.gov
    www.bea.gov
    www.federalreserve.gov
    api.weather.gov

The prior mode was the default "Trusted" list (package registries, GitHub,
cloud SDKs) — so the 403s you saw on raw requests were most plausibly the
egress proxy, not the sites. The odds-API rejection (proposals.md
2026-08-04) is unchanged; nothing here needs a key.

**Laptop-side ground truth (residential IP, 2026-08-05 10:5xZ), so a
remaining failure can be classified correctly:**

- api.elections.kalshi.com/trade-api/v2/markets → 200 (no auth)
- api.manifold.markets/v0/markets → 200
- fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE → 200 (keyless CSV)
- api.bls.gov/publicAPI/v2/timeseries/data/LNS14000000 → 200
- www.bea.gov, www.federalreserve.gov, api.weather.gov → 200
- www.metaculus.com/api2/questions/ → **403 even from residential, with a
  browser UA** — this one is site-side bot protection, NOT egress. Do not
  burn retries on it; treat Metaculus as unreachable unless a later test
  says otherwise.

**Asked of the next full cycle:** re-test the reachable-from-laptop
endpoints from the runner (one cheap GET each is enough) and log per-host
status in the cycle line. If a host now returns 200, the §2 cross-venue
channel is open for it — Kalshi is the one that matters (real-money venue,
econ/news overlap; Manifold stays reference-only per §2). If a host still
403s from the datacenter after this allowlist change, that is site-side
IP blocking — log it as such and keep the WebSearch-by-name fallback; no
further operator egress action will fix it.

## 2026-08-05 ~19:30Z — CPI brackets: the "contradictory sources" were three different series

The 13:45Z/10:26Z cycles skipped the July CPI markets because WebSearch
numbers (2.7-2.8%) didn't parse against brackets centered 3.3-3.5%. Operator
pulled the actual market descriptions from gamma. There is no contradiction —
Polymarket runs THREE separate CPI clusters on the same Aug 12 08:30 ET
release, each resolving on a DIFFERENT series, all to one decimal:

- **"Will annual inflation be X% in July?"** (event 703573): headline CPI-U,
  12-month change, **NOT seasonally adjusted** (BLS series CUUR0000SA0;
  FRED `CPIAUCNS`).
- **"Will monthly inflation increase/decrease by X% in July?"**: headline
  CPI-U, one-month change, **seasonally adjusted** (BLS `CUSR0000SA0`;
  FRED `CPIAUCSL`).
- **"Will Core CPI MoM be X% in July?"**: CPI-U ex food & energy, one-month
  change (FRED `CPILFESL`).

Resolution source for all three: the monthly BLS CPI news release
(bls.gov/bls/news-release/cpi.htm) — api.bls.gov and fred.stlouisfed.org
are both on the runner's allowlist as of the 10:53Z note, so pull the
series directly instead of searching for headline numbers. Any consensus
figure found via WebSearch is only usable after identifying WHICH of these
series it forecasts (press "CPI rose X%" is usually the SA MoM or the YoY;
core is quoted separately).

Mechanical structure worth noting for the cross-market class: with June
data published, 11 of the 12 months in the YoY comparison are already
known — the YoY brackets and the MoM cluster are two prices on
substantially the same single unknown (July's monthly change), linked by
a computable base effect and the seasonal factor. Whether the two clusters
are jointly consistent is arithmetic on data you can now fetch. Checking
that consistency is exactly the fact-final, no-narrative profile of the
settled wins; as always, this is a pointer to sense, not a mandate to bet.

## 2026-08-05 ~19:30Z — instrument change: scan window widened, event_id in scan output

Two operator edits to protected files, announced here so the change in
your inputs is visible rather than inferred (the 2026-08-03 lesson,
applied in reverse):

1. **CYCLE.md step 4 now runs `--hours 336 --limit 800`** (was 168/400).
   Two weeks of scheduled prints and fixtures are now in the window, and
   the higher paging cap keeps the endDate-ascending query from
   truncating in the deeper universe. Expect a larger candidate pool;
   your selection standards, not the pool size, still govern what gets
   researched. discovery.py's queries and their per-query floors are
   untouched and remain yours.

2. **scan.py output records now carry `event_id` and `event_slug`**
   (first entry of gamma's `events` array, null if absent). Sibling
   grouping for the cross-market checks no longer needs the extra
   per-candidate gamma round-trip in siblings.py — group scan output by
   `event_id` directly; keep siblings.py for fetching live sibling prices
   once a group looks interesting.

## 2026-08-05 ~19:45Z — architectural stance: this agent is not built for speed; info-race dropped from real classes

Operator decision, with the reasoning so retros can weigh it as evidence
rather than guess at it. `real.allowed_edge_classes` is now
`["cross-market"]` — info-race no longer qualifies for real twins.

The reasoning is architectural, not just the 0-win record: an
LLM-cycle agent's unit of action is a multi-minute research session. A
speed race against reprice bots on a public data drop is a race this
architecture cannot win at ANY wake-up cadence — arriving "less late"
still means entering after the reprice on an estimate formed before it.
What this architecture IS built for: research and analysis — arithmetic
the market hasn't done (cross-market consistency), official numbers the
market hasn't priced correctly (fact-final reads), interpretation work
where hours of persistence make timing irrelevant. The settled evidence
(mechanical facts 2W-0L, interpretation/speed-adjacent 0W-3L) agrees with
the architecture argument.

For the paper side, the class taxonomy stays yours: keep measuring
whatever you want, including info-race, if you think the evidence
justifies the research budget. But when weighing where to spend cycles,
weigh this: a thesis whose edge decays in minutes is a thesis this
system structurally cannot capture. "Being early on a fact" only fits
you when early means hours-to-days (the market hasn't NOTICED), not
seconds (the market hasn't REACTED yet).

## 2026-08-05 ~19:55Z — tag taxonomy exploration is yours now, not the operator's

The two tag verifications the operator did (Economy 100328, weather 1474)
existed because you didn't know the taxonomy was explorable — not because
you can't reach it. You can: `gamma-api.polymarket.com/tags` is open and
enumerable (paginated, limit/offset, thousands of tags — verified from
the laptop 2026-08-05; the vast majority are per-player/per-meme noise).
Everything needed to verify a tag ("does it surface live markets, what
volume range, do they resolve on an official number?") is one
`/markets?tag_id=X&closed=false` query you already know how to make.

So this moves inside your sensing mandate, on your pacing — roughly
weekly feels right, but that's yours to decide: enumerate or spot-check
tags, score candidates by live-market count and resolution mechanics
(official print / countable metric >> narrative), fold winners into
discovery.py, and re-check previously-empty tags (weather 1474) on the
same cadence. A tags.py under strategy/tools/ is the obvious shape if
you want one. The operator stays available for what you genuinely
cannot do: egress changes, protected-file edits, and ground-truthing
from a residential IP. Taxonomy archaeology no longer qualifies.

## 2026-08-05 ~20:30Z — mandate: market selection is a learned competency, and right now it is ungraded

Operator conviction, stated as direction: how well you perform is
heavily determined by WHICH markets you choose to work on — selection
and exploration, not just estimation. Your estimation is measured to
death (brier_delta by category and edge class, the z line). Your
selection is not measured at all: when a day goes 0-for-N, nothing
recorded can distinguish "the pool held no edge" from "the pool held
edge and research picked the wrong candidates" from "the queries built
the wrong pool". The 2026-08-03 pagination episode showed what an
unmeasured selection layer costs. Three asks, all inside what you own:

1. **Make the fit rubric explicit in the playbook.** You know your
   strengths as a trader by now; write them down as scoreable market
   properties and select against them. From the settled evidence the
   profile looks like: resolution is mechanical (official print,
   countable metric, arithmetic) rather than interpretive; the
   benchmark is reachable from your runner (open API, WebSearch-dense
   coverage, or Polymarket-internal arithmetic); the edge, if real,
   persists hours-to-days (you are built for research, not reaction);
   the resolution tail is bounded (the ceasefire position is 5+ days of
   locked capital and attention); and research cost is small relative
   to what the market can pay (the $20k-econ-vs-$400k-tennis asymmetry).
   Today's Blue Jays bet adds nuance worth encoding: WebSearch-dense
   sports ARE reachable — the property that matters is coverage
   density, not category.

2. **Instrument the funnel so selection can be graded.** Per full
   cycle, record (machine-readably — a JSON line in the cycle log or a
   strategy-owned file): pool size by property/category, how many
   candidates were researched, and a skip reason per researched
   candidate (no-edge / benchmark-unreachable / ambiguous-resolution /
   budget-exhausted / market-agrees). Deep retros should then grade
   selection the way they grade estimates: which properties actually
   produced settled edge per research-hour, and did the skip reasons
   hold up in hindsight (a "market-agrees" skip on a market that then
   moved 20 points was a selection error, not a non-event).

3. **Budget deliberate exploration.** Selection learnt only from your
   wins overfits to two categories. Spend a bounded slice of research
   budget — you pick the fraction — on candidates OUTSIDE the current
   fit profile, chosen to test a named hypothesis about a property
   ("weather resolves mechanically; is the coverage there?"), and
   record the result even when it is "category not viable". A ruled-out
   category with evidence is a selection asset; an unexplored one is a
   blind spot.

The point is not more selection rules — it is that selection improves
the same way estimation does: measured, graded in retros, and edited
with evidence. If instrumenting this properly needs something protected
(a ledger field for market properties, a score.py slice), propose it.

## 2026-08-08 — odds API provisioned (reachability re-open actioned)

The 2026-08-04 reachability rejection's re-open condition was met (see the
2026-08-08 proposals.md entry for the numbers), so the deal changes:
`core/odds.py` gives you bookmaker consensus (decimal, feed to your
devig.py) and event status for the major-league sports the-odds-api covers.
Ground rules:

1. **Budget is the constraint now, not reachability.** ~450 credits/month
   hard-capped in protected code ≈ 10-12/day. A full odds pull for one
   sport is 1 credit; scores are 1-2. Spend on candidates that already
   passed your funnel filters, not on discovery. The 10-minute cache makes
   within-cycle re-checks free — batch your research accordingly.
2. **min_edge_book_devig (0.07) finally gets real tests.** That was the
   point. Grade the floor with settled evidence before touching it.
3. **WebSearch multi-book consensus stays valid** where the API lacks a
   sport/market; the API is the benchmark of record where it has one —
   cite which one the rationale used.
4. Tennis has status coverage again via `scores` — the 2026-08-04
   "visible but untradeable" class is back in scope where the API lists
   the tour.

## 2026-08-09 — forecast ledger: every researched estimate now gets scored

New mechanism (operator commit, protected core): `core/forecast.py record`
writes stake-free forecasts to `journal/forecasts.jsonl`; resolve.py settles
them; score.py reports them in a `forecasts` section. CYCLE.md step 5b makes
it part of every FULL cycle. Why: your calibration was getting ~0-1 settled
feedback events per day because feedback required a bet that cleared an edge
floor AND settled — while you were researching 10-30 candidates/day to
concrete estimates and throwing the numbers away. Now every estimate is
scored brier_delta against the market. Ground rules:

1. **Coverage is mandatory and audited.** Every researched candidate with a
   concrete (market, outcome, probability) gets a forecast — especially the
   no-edge and market-agrees skips; that's where the calibration data is
   richest. Deep retros reconcile funnel researched entries against
   forecasts.jsonl: an estimate-bearing skip with no forecast row is a
   finding. Benchmark-unreachable skips must NOT invent an estimate.
2. **Honest-belief rule applies identically.** est_prob is your genuine
   probability, formed before anchoring on the price. Gaming is pointless by
   construction: the score is brier_*delta* vs the market, so padding with
   near-certainties on near-resolved markets scores ~0.
3. **Mid baseline, separate section.** Forecasts benchmark against the mid
   at record time (no fill occurs); bets benchmark against the ask they
   filled at. The two brier_deltas are NOT comparable — never merge them in
   a retro.
4. **Forecast before place.** A bet candidate's forecast (`--skip-reason
   bet`) is recorded before `ledger.py place`, committing the estimate
   before the fill attempt.
5. **What this buys you:** `by_skip_reason` will show whether your
   market-agrees skips actually hold up, whether your no-edge reads are
   calibrated, and whether bet candidates are better-estimated than skips —
   selection grading with n in the hundreds instead of n=19.
