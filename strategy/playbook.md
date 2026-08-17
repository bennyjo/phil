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
   **Multi-source verification standard (DEEP-2026-08-12, enacting the
   DEEP-2026-08-02 pre-registration now that both pair legs have settled
   lost — `b21e42c123a1` 2026-08-04, `d2dd24206542` 2026-08-12):** "the fact
   is already public" requires at least one non-party primary source (wire
   service Reuters/AP/AFP, host-government official statement, or the
   resolver's own named source) — a consensus composed entirely of state
   media of the parties to the event (PressTV, Mehr, TASS, Xinhua on the
   Iran-vs-Gulf-states claims) does not qualify on its own, however many
   outlets repeat it or how internally consistent they are. This is now a
   general condition of the class, not just the spread-rule exception
   below (which already applied a narrower version of this to
   `b21e42c123a1` alone, DEEP-2026-08-05). Both pair legs lost on
   state-media-only corroboration of a contested Iran-conflict claim: the
   reporting was plausible and mutually consistent, and the resolver still
   read the fact the opposite way on both legs.
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

Info-race status (updated DEEP-2026-08-12): the class is **2W/4L by
decision** — wins on mechanical/final facts (`2dc417ed68f6` official
print, `1e8dec1078ba` cross-market), losses on provisional or
interpretation-dependent ones (ai-leaderboard pair as one decision,
`84ec821167d5`, `b21e42c123a1` settled LOST -$5 on 2026-08-04 via a normal
UMA flow: est 0.90 on state-media-sourced claims, resolver waited out the
market's 3-day conflicting-reports clause and resolved No, and now
`d2dd24206542`, the sibling leg, settled LOST -$5 on 2026-08-12 — 12 days
past end date with no UMA proposal ever submitted, book decayed to
bid/ask 0.001/0.002 and never recovered). Both legs of the
DEEP-2026-08-02 pre-registered pair are now settled losses: the rule is
**enacted**, not a caution — see the multi-source verification standard
under edge class 1 above. Net effect of this one Iran-conflict pair on
the info-race record: -$10, 2 of the 4 losses.

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

**Same-day index/ETF direction, first instance (2026-08-10):** SPX/SPY
"up or down today" markets (resolve on official close vs prior close,
same-day) score N on property 3 — a directional call with ~100min to
resolution is a reaction-speed contest on the world's most liquid feed, the
same architecture problem operator-notes 2026-08-05 ruled out for info-race.
A naive Brownian-bridge model (vol scaled by sqrt(session-time-remaining))
claimed a large edge (SPX Down priced 0.78-0.805 ask vs model ~0.57-0.59) —
exactly the "large claimed edge in an efficient market" shape that's 0W/5L
elsewhere in the record; treat any such reading as a modeling gap, not
alpha, and decline regardless of size. Recorded as forecasts
(skip-reason `architecture-mismatch`) for calibration only, not researched
as bet candidates going forward absent a property-3 change.

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

**Skip-reason taxonomy rule (DEEP-2026-08-11):** `outside-view-veto` may
appear in a funnel row ONLY when a forecast row exists for that
market+outcome (link its forecast_id) — the veto blocks *bets*, never
*estimates*; a vetoed candidate by definition had a concrete estimate,
and unrecorded vetoed estimates are exactly what makes the veto
unfalsifiable. When research concluded no honest independent estimate
could be formed (contradictory sources, interpretive-inference-only,
no credible poll), the skip reason is `benchmark-unreachable`, whatever
made research stop — the estimate-bearing/estimate-free line is what the
coverage audit reconciles against forecasts.jsonl. Evidence of the blur
this fixes: MN-Gov (2026-08-10 04:16Z) and SC round-1 (07:33Z) both
logged `outside-view-veto` with no forecast (estimate never formed),
while SC round-1 (14:39Z) logged the same reason WITH forecasts — same
label, opposite auditability. Also: every researched funnel entry
carries its forecast_id(s) inline (the 2026-08-11 02:21Z entry omitted
them; coverage was verified clean, but only by market_id
reconciliation, which does not scale).

**Taxonomy addition (DEEP-2026-08-13): `category-bar`.** A decline whose
operative reason is a playbook category bar (contested primaries; the
general-election extension below) uses skip reason `category-bar`, not
`outside-view-veto` — the veto is specifically the >0.10-claimed-edge
numeric boundary, and its settled record (6-for-6 pre-registered, n=3
officially settled at brier_delta +0.1109) is only interpretable if the
label stays coextensive with the definition. Evidence of the blur this
fixes: fa185b55a5c3 (Zambia, 2026-08-13 04:18Z) logged `outside-view-veto`
"by extension" at claimed edge ~0.05 — a principled decline under the
election bar, but under the wrong label; at settlement it would pollute
the veto slice with a row the veto never fired on. Same forecast-row
requirement as the veto: an estimate was formed, so a forecast row is
mandatory and its forecast_id goes in the funnel line.

**Taxonomy addition (DEEP-2026-08-14): `wide-spread-veto`.** A decline
whose operative reason is the max_spread rule (book spread > 0.06 blocks
the bet regardless of apparent edge) uses skip reason `wide-spread-veto`,
not `outside-view-veto`. Evidence this split is load-bearing, not
pedantry: of the 8 settled rows labeled `outside-view-veto`, the 5
self-generated-model rows (SC Fry, MN Craig/Flanagan, Musk 120-139 and
140-159) settled at mean dBrier **+0.118 — market better on every row**,
while the 3 wide-spread rows (PPI 5.3%/5.4%/≥6.0%, mechanical base-effect
model, ids 5ad483698a95/169b4fd6c04a/4908388c9fd7) settled at mean dBrier
**-0.010 — agent better on every row**. One label was averaging two
mechanisms with opposite settled signs, which corrupts both instruments:
the veto's "N-for-N" record only means something over rows where the veto
actually fired on estimate quality, and the spread rule's *cost* (edges
foregone to illiquidity, which the PPI rows show can be real) is invisible
unless its rows are separable. Same forecast-row requirement as the other
estimate-bearing labels. When both apply (self-model edge AND wide book),
use `outside-view-veto` — estimate distrust dominates, since the estimate
would be blocked at any spread.

**Taxonomy clarification (DEEP-2026-08-15): blanket category bars at
sub-boundary edges.** When a category carries a blanket self-model bar
(contested primaries/elections; social-media-postcount) and a leg's
claimed edge is ≤0.10, the decline's operative reason is the bar, not the
numeric veto — label it `category-bar`. `outside-view-veto` stays
coextensive with the >0.10 boundary (DEEP-2026-08-13), otherwise the
veto's settled ledger accumulates rows the veto never fired on. Instance
that prompted this: the 2026-08-15 04:18Z Musk weekly set labeled all 5
legs `outside-view-veto` though three (70331099597c, c24926a5c9d7,
7808b6f5a4ef, claimed edges 0.025-0.045) were sub-boundary. Recorded rows
are immutable (core writes forecasts.jsonl), so the reading rule: at
settlement those three rows grade the bootstrap model, NOT the veto —
exclude them from any veto-record claim.

**Skip calls get graded against outcomes by the deep retro** once the
skipped market resolves — the funnel line is the durable record and the
deep retro is the carrier. (First pass DEEP-2026-08-06: CRCL/OXY
market-agrees skips both resolved as priced — correct calls. The
DEEP-2026-08-05 watch item asking hourly cycles to grade them on
resolution day was never executed; watch items alone are not a carrier
for deferred obligations, the same lesson as the b21 settlement-retro
drop.)

**Operational trap (2026-08-15 17:1xZ): `forecast.py record --outcome` takes
the outcome you name, not "the side I have an opinion about" — a mismatch
silently records the complement of the intended belief.** Recorded a
Canada-GDP "less than 0.0%" bracket forecast intending est_prob 0.11 for
the market's stated Yes side (matches market's own Yes=0.107), but passed
`--outcome "No"` with that same 0.11 value — the row now reads "I believe
P(No)=0.11" i.e. P(Yes)=0.89, the opposite of the intended belief, and
disagrees with market by ~0.78 instead of ~0. Forecast rows are immutable
(only core writes forecasts.jsonl); this one (fe954ed9f325, market 3388182)
stays on the books as recorded and will score as a large miscalibration
when it settles — flag it in that retro as a labeling bug, not a belief
failure, so it doesn't get read as evidence about econ-bracket calibration.
Rule going forward: state the target outcome string in the note/reasoning
BEFORE the CLI call, and sanity-check the returned `mid`/`delta_vs_mid`
against the intended direction immediately after recording, since the tool
prints exactly the number needed to catch this before moving on.

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

**Anti-loophole (DEEP-2026-08-10):** an exploration candidate must test a
rubric PROPERTY not yet characterized, not a new instance of a
characterized one. A new league/competition fed through already-measured
edge machinery does not qualify: the 2026-08-09 21:15Z cycle spent its
exploration slot on Leagues Cup/Brasileirão 3-way devig via odds.py —
the same book-devig pipe whose clean-feed profile (~0.00-0.02 edges vs
tight PM books) was already confirmed across ~40 devigged markets over
the prior 3 days — and predictably re-found the known result. Contrast
the 08-09 05:15Z weather probe (new property: "official forecast JSON as
benchmark — reachable? resolvable?"), which is the intended shape. Before
charging a candidate to the exploration budget, name the property being
tested and why existing evidence doesn't already answer it.

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

**Odds-API integration (2026-08-08, operator-notes re-open):** `core/odds.py`
(keyed the-odds-api client) is now the benchmark of record for book-devig
arbitration on any sport it covers — prefer it over WebSearch multi-book
consensus there, since it returns decimal lines straight into `devig.py`
without the recurring "stale/wrong-day/reverse-line/contradicting-sources"
search traps documented below (§Search-result traps). Rules for spending it:
1. **Discovery order, not discovery source.** Run `sports` (free) once per
   cycle to see what's in season, but spend `odds`/`scores` calls only on
   candidates that already passed the funnel filters (coverage precondition,
   favorite-framing pre-filter, date/starter pinning) — the ~10-12
   credits/day budget (450/month local cap, `journal/odds-quota.json`,
   `quota` subcommand shows state) is for confirming a benchmark on a
   pre-qualified candidate, not for browsing. The 10-minute cache makes
   within-cycle re-checks free.
2. **`min_edge_book_devig` (0.07) now gets real tests against a clean feed**
   instead of only WebSearch-derived lines — grade the floor with this
   evidence specifically, separate from the WebSearch-sourced book-devig
   record above, once enough settlements accumulate.
3. **WebSearch multi-book consensus stays valid** for sports/markets the API
   doesn't cover — cite which channel (`core/odds.py <sport_key>` vs.
   WebSearch) the rationale used, so retros can tell them apart.
4. **Tennis status is back in scope** via `scores` where the API lists the
   tour — the 2026-08-04 "visible but untradeable" gate no longer applies
   there; still gate on `sports` actually listing the relevant tennis key
   before spending research on a tennis candidate.
If the key is missing or the budget is exhausted, `core/odds.py` exits with
a clear message — log it and fall back to WebSearch, never work around the
guard.
5. **Confirmation-sweep cap (DEEP-2026-08-10).** The clean-feed finding is
   now CONFIRMED, not provisional: across 3 days and ~40 devigged markets
   (MLB -1.5 slates 08-09 08:15Z/11:15Z/14:19Z/04:16Z, WNBA h2h+spreads,
   Leagues Cup/Brasileirão 3-way), every power-devig edge vs a tight PM
   book landed in 0.000-0.020 — under even min_edge, nowhere near
   min_edge_book_devig. Re-demonstrating this daily is cheap in credits
   (cache) but not in research minutes: the 14:19Z cycle re-ran the same
   slate researched 3h earlier to "confirm unchanged". Cap: at most ONE
   sports devig confirmation sweep per day, and only when the slate's
   composition actually changed (new games, not the same games re-checked);
   log it as `cheap-confirmation`, not research. The marginal research
   minutes go to independent-benchmark candidates (econ prints, polls,
   countable metrics) — the only stream that generates scoreable
   disagreements (see Forecast ledger, below).
   **Cap tightened DEEP-2026-08-13: at most ONE sports devig confirmation
   sweep per WEEK per feed, as a drift spot-check.** The daily cap's own
   evidence condition is met and exhausted: mlb-spreads settled forecast
   n=21 at brier_delta -0.0003, stable across three consecutive slates
   (n=12 → 18 → 21, delta -0.0003/-0.0004/-0.0003; RETRO-20260813-0211
   and -0311 are the second and third confirmations). Every additional
   at-market row adds ~zero information about the only open question
   (disagreement calibration) while spending odds credits and research
   minutes. A weekly one-slate spot-check is enough to detect feed drift;
   anything more is re-demonstrating a solid null. If a spot-check ever
   shows a clean-feed edge ≥ min_edge on a tight book, that is NEW
   information — revert to daily sweeps and say why.

**First clean-feed sweep result (2026-08-09 02:12Z, DEEP-2026-08-09):** the
feed's first working cycle devigged 7 favorite-framed MLB -1.5 spreads and 2
WNBA markets (2+2 credits, 9 books deep): max nominal edge **0.018** at the
mid (MLB, Pirates), 0.025-0.035 (WNBA) — all under base min_edge 0.04, let
alone min_edge_book_devig 0.07. Every prior "big" sports-devig edge in the
settled record came from scraped/stale/wrong-day lines (the 0/7 graveyard);
with a clean, current line the measured gap to tight PM books is ~0.02.
Allocation consequence (one slate, small-n, but it agrees with the whole
settled record): sports devig is now a CHEAP CONFIRMATION step (a couple of
credits, minutes), not a place to spend the research hour. The marginal
research hour goes to mechanical-resolution non-sports — the CPI cluster
(Aug 10-12, FRED/BLS direct), econ-tag markets, post-count brackets near
period end — where the settled evidence (mechanical facts 2W-0L) and the
architecture argument (operator-notes 2026-08-05) already pointed. Run the
sweep, log it, move on; a sports bet now needs the feed to hand you ≥0.07
on a current line, which day 1 suggests is rare.

**Cloud-runner caveat (found first cloud use, 2026-08-08 ~22:1xZ):**
`api.the-odds-api.com` is EGRESS_BLOCKED from the cloud runner specifically
— both urllib and the curl fallback get `CONNECT tunnel failed, response
403` from the sandbox proxy, distinct from a "key not provisioned" exit or
an API-side 401/422. Check which failure you got before logging: a clean
`sys.exit` naming the key/budget is the guard working as designed; a
`Tunnel connection failed`/`curl: (56)` traceback is the egress block —
log "odds EGRESS_BLOCKED (cloud runner)" and fall back to WebSearch, same
as the clevelandfed.org/macromicro.me pattern above. Filed as a proposal
(journal/proposals.md 2026-08-08) — re-check `sports` each cycle in case
the allowlist changes.

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

**Third moneyline test + first props test (2026-08-16 00:21Z), same
Makhachev/Garry fight, ~3.7h pre-fight via odds.py's clean feed:** h2h
power devig 0.7585/0.2415 vs live ask 0.74/0.27, edges +0.0185/-0.0285 —
n=3, still no-edge, the class stays efficiently-tracked even this close to
first walk. **Exploration budget, single-book method-of-victory props
(first test, named property: does UFC prop coverage have complete
single-book lines the way moneylines do?):** WebSearch surfaced DraftKings
decision/submission odds for both fighters (Makhachev Dec +120/Sub +200,
Garry Dec +450/Sub +3300/KO +1100) but Makhachev's own KO/TKO price was
never quoted by DraftKings in any result — only a FanDuel range (+850/+950)
that the source itself flagged as merely "expected to be similar" on DK,
not an actual DK number. Completing the 6-way distribution would require
substituting a different book for the one missing leg, which is the
cross-book-mixing trap (Boca/Estudiantes precedent) applied to a prop
market instead of a 1X2. Declined rather than mix; **result: UFC props are
only PARTIALLY single-book-coverable from WebSearch (2 of 3 methods per
fighter found on one book, the KO/TKO leg missing) — treat any UFC
method-of-victory candidate as benchmark-unreachable unless a single
source quotes all methods for both fighters from the same book.**

**Exploration budget, ATP/WTA tennis moneylines (2026-08-14 09:1xZ, first
test of this category).** Hypothesis: same shape as UFC-moneyline — dense
multi-book coverage (the-odds-api `tennis_atp_cincinnati_open`/
`tennis_wta_cincinnati_open`, 5-8 books per match) might leave PM lagging or
loose. Three Cincinnati Open matches today, all high-liquidity ($71k-$79k):
Royer/Tsitsipas (8 books, power devig fair 0.231/0.769 vs PM ask 0.24/0.77,
edges -0.009/-0.001), Machac/Carreno Busta (8 books, fair 0.523/0.477 vs PM
ask 0.53/0.48, edges -0.007/-0.003), Zandschulp/Griekspoor (8 books, fair
0.516/0.484 vs PM ask 0.52/0.49, edges -0.004/-0.006). Result: **reachable**
(dense book coverage confirmed, same as UFC) but **no edge** on any of the
6 sides across 3 matches, all |edge| < 0.01 — PM tracks the devigged
consensus about as tightly here as on UFC and MLB. Category ruled in, not
out (n=3 matches, all no-edge, same efficient-market pattern as every other
liquid PM sports book tested so far); revisit only if a lower-liquidity or
in-play match shows a wider gap.

**Politics-primary sensing fix + outside-view veto applied live (2026-08-09
05:xxZ, MN Governor GOP primary, `907983`/`907993`).** The 2026-08-08 18:11Z
cycle logged this candidate benchmark-unreachable ("polls inconsistent across
weeks/sources"). Re-checked with `predictionedge.com/elections/governor/<state>/<race>`
(a poll aggregator that tables each poll by pollster AND date) instead of raw
WebSearch snippets: the apparent inconsistency was a house-effects artifact —
three same-house SurveyUSA waves (Jun 11-16, Jul 15-20, Jul 29-Aug 4) show a
consistent, if narrowing, Lindell lead (27/22, 35/26, 34/28 — gap 5, 9, 6
points), while the "contradicting" numbers came from different, less
frequent houses (Big Data Poll, MN Private Business Council). **Sensing
lesson: when WebSearch snippets on a poll-heavy race look contradictory,
check for a dedicated poll aggregator (predictionedge.com covers US
gov/senate primaries; RealClearPolling for general races) before concluding
benchmark-unreachable — it separates trend-within-house from
house-effect-noise, which raw search summaries conflate.** This is a
methodology fix, not a one-off: add aggregator lookup as a first step for any
multi-poll US primary/general candidate.
Having a clean benchmark, the substantive read: as of Aug 4 polling (7 days
pre-primary, Aug 11), Lindell led the vote-share polling by 6 points with
Qualls drawing ~17% and ~21% undecided; PM prices the WIN probability the
other way (Demuth Yes 0.565 vs Lindell Yes 0.43) — the aggregator's own
"market-implied" panel turned out to just be quoting a prediction market
back, confirming it is not an independent cross-check. **Declined to bet
despite a >0.10 apparent gap**, applying the DEEP-2026-08-07 outside-view
veto: the SurveyUSA trend is public and as available to PM traders as to
this agent, so "my vote-share-to-win-probability read disagrees with the
market's win-probability read" is the same interpretive-forecast shape that
went 0/5 before, not a fact the market structurally couldn't have priced
(unlike an official print or cross-market arithmetic). Logged for the deep
retro to grade once the primary settles Aug 11: if Lindell wins, this is a
foregone-edge data point for loosening the veto on well-evidenced polling
divergences in low-candidate-count primaries; if Demuth wins, it is
confirmation the market/undecided-breakdown knows something a raw
vote-share extrapolation doesn't (matches the Wisconsin Governor primary
precedent, where the market also correctly reflected the polling leader).

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

**Exploration budget, social-media post-count brackets (2026-08-09 02:1xZ,
first test of this category).** Hypothesis: "post-count resolution is
mechanical AND the running count is published live by the resolver itself,
not just estimable" — a stronger reachability claim than any prior category
tested. Confirmed: Polymarket's stated resolution source for "Elon Musk #
tweets <period>?" markets is `https://xtracker.polymarket.com`, and its
public REST API (no auth) exposes the exact running count — `GET
/api/users/elonmusk?platform=x&stats=true` lists every open tracking period
by id, then `GET /api/trackings/<id>?includeStats=true` returns hourly
`daily` counts plus a `cumulative` total for that period. Tested on the
"August 4 - August 11" bracket set (PM brackets: 160-179 Yes=0.135, 180-199
Yes=0.385, 200-219 Yes=0.285, 220-239 Yes=0.095): at query time (4.42 days
of 7 elapsed) cumulative was 126, i.e. ~28.5/day; the API's own `pace` field
(176) is misleading — it divides by `daysElapsed` (5, apparently ceil'd),
not actual elapsed time, understating the run rate. The correct linear
extrapolation (126/4.42*7 ≈ 200) lands almost exactly on PM's 180-199/200-219
boundary, where PM already puts its two largest buckets (67% combined) —
**reachable (exact live source) but no edge**: PM's distribution already
tracks the true pace closely once you extrapolate correctly, and per-day
counts are volatile enough (18-37 across 4 observed full days) that no
single 20-wide bracket clears min_edge against that noise. Category ruled
IN as viable (the API is a stronger benchmark than anything else tested —
exact, live, resolver-authoritative) — worth rechecking near the end of a
period when daysRemaining is small (less extrapolation variance) or on a
bracket set whose current pace sits further from PM's mode than this one
did. **Caveat for reuse:** always compute pace from `cumulative / actual
elapsed days` yourself; do not trust the API's own `pace` field, which
undercounts a still-running partial day as a full one.

**Fat-tail mechanism found on near-end recheck (2026-08-13, RETRO-20260813-1707,
no forecast filed — both prior open forecast rows on this event, `b7a58fd571c8`
et al. from 2026-08-12, blocked a duplicate).** A Gaussian model of the
running count (mean from elapsed-days pace, sd from the daily-count series)
systematically UNDERSTATES the right tail relative to the market: on the
Aug7-14 Musk event at 23h remaining (cumulative 138, model N(159.74, 7.85)),
the model gave the 180-199 + 200-219 brackets combined ~0.6% while the book
(siblings.py, sum_check 0.9875 — a well-calibrated book) priced them at
8.85% combined. This isn't noise-sized: it's an order of magnitude, and it's
directional (Gaussian always under-weights tails vs. any real bursty count
process — a single high-volume posting day, retweet storm, or news-driven
spike). Consequence: the model's claimed edge on the modal brackets
(140-159 here, edge 0.133 vs the veto's 0.10 boundary) is inflated by the
same mechanism that starves the tail — probability mass the Gaussian denies
the tail has to go somewhere, and it lands in the bulk brackets, manufacturing
a fake edge there even when the true mean estimate is fine. This is the
same "large claimed edge in an efficient, information-rich market = modeling
gap, not alpha" pattern as the SPX Brownian-bridge case, now with an
identified mechanism specific to this category: **do not use a plain
Gaussian for these brackets near a boundary; either fatten the tail
(mixture, or empirical bootstrap off the observed daily-count series) or
treat any Gaussian-derived edge here as presumptively overclaimed and route
it through the outside-view veto regardless of nominal size.**

**Graded (DEEP-2026-08-14): the prediction above settled correct within
12 hours.** Both of the model's center-mass brackets resolved No — 120-139
(5ef2f363f039, est 0.165, RETRO-20260813-2130) and 140-159 (b7a58fd571c8,
est 0.64, the model's modal bracket, RETRO-20260814-0045). Together those
two legs carried ~80% of the Gaussian's probability mass; the count landed
above both, i.e. in exactly the right tail the model starved. Two
same-model, same-direction misses on the highest-mass legs is a mechanism
confirmation, not variance. The open 160-179 (market 0.385 vs model 0.189)
and 180-199 (0.095 vs 0.003) rows grade the market's side of the same
comparison at settlement.

**Graded again (2026-08-14 09:05Z, RETRO-20260814-0905): 160-179 also
settled No** (e06e9b2bea70, est 0.189). n=3 now, all same model instance,
all same direction — the count has landed above every bracket checked so
far, tracking the market's fatter-tail pricing rather than the Gaussian's.

**Fully graded (2026-08-14 19:16Z, RETRO-20260814-1916): 180-199 settled
Yes** (eb09f3632c5d, est 0.003) — the true count landed in 180-199 itself,
the exact bracket the Gaussian starved to 0.3%, not the 200+ tail beyond it.
All four same-model siblings on this event are now settled (120-139 No,
140-159 No modal-bracket miss, 160-179 No, 180-199 Yes), same direction
throughout: a plain elapsed-pace Gaussian is confirmed unusable for this
category's tail brackets (est 0.003 vs. an outcome the market's own book
priced around 9.5%) — not a one-off, a repeatable mechanism. The outside-view
veto correctly blocked a bet on this leg pre-settlement; no ledger loss. n=4
is still below the ~15-settlement floor-change threshold, so no numeric
min_edge change yet, but the modeling requirement (fatten the tail — mixture
or empirical bootstrap off the observed daily-count series — before trusting
any Gaussian-derived edge on this category's outer brackets) is now
confirmed rather than provisional. This event's sibling set is closed out;
next test is a fresh event/pace, not a re-check of this one.

**Test in progress (DEEP-2026-08-15, pre-registered reading).** The
2026-08-15 04:18Z cycle ran the required bootstrap (14-day empirical
daily-count resample) on two fresh events: the Aug11-18 weekly set (5
rows, 70331099597c…cf16f6424af7) and the first 2-day window Aug13-15
(10029a75295e, 53c5bf348303 — settles ~Aug 15 16:00Z; weekly settles Aug
18 16:00Z). The bootstrap still disagrees with the market by >0.10 on two
weekly legs (180-199 est 0.494 vs 0.325; 220-239 est 0.024 vs 0.145).
Reading committed BEFORE settlement: if the market again beats the model
on the large-disagreement legs, the verdict escalates from "wrong tail
shape" (fixed by the bootstrap) to "self-model class untrustworthy in
this category at any model sophistication" — i.e. a permanent category
bar like contested primaries, forecast-only. If the bootstrap materially
beats the market on those legs, the Gaussian, not the class, was the
problem, and the category stays estimate-bearing under the veto. Grade
same-tick at each settlement against exactly this fork.

**First settlement, off-fork (2026-08-15 18:12Z, RETRO-20260815-1812):** the
Aug13-15 2-day pair's 65-89 leg (`53c5bf348303`) settled No against a
bootstrap est of 0.501 and a market ask of 0.63 — model brier 0.251 vs
market brier 0.384, model beat market by 0.133 on this leg. This pair is
NOT the pre-registered fork (that's the weekly 180-199/220-239 legs,
settling Aug 18) — it's a useful early n=1 data point in the bootstrap's
favor but does not resolve the fork. The sibling 40-64 leg (`10029a75295e`)
is still open. No bet either way (outside-view veto still applied).

**Pair complete, still off-fork (2026-08-15 19:12Z, RETRO-20260815-1912):**
the sibling 40-64 leg (`10029a75295e`) settled Yes against a bootstrap est
of 0.499 and a market ask of 0.40 — model brier 0.251 vs market brier
0.372, model beat market by 0.121. Both legs of the Aug13-15 pair now agree:
bootstrap beat market (n=2). Still off-fork — the fork verdict is decided
only by the weekly 180-199/220-239 legs settling Aug 18. No bet either way.

**Counting caution (DEEP-2026-08-16):** the two legs of this pair are
complementary claims on the SAME realized count — once the count landed in
40-64, both "40-64 Yes" and "65-89 No" were decided by that single fact,
and the bootstrap's edge over the market on both legs is one insight
double-counted, not two replications. Treat the pair as n=1 independent
outcome in any fork or veto-record reasoning (the same convention the veto
ledger already applies to the weekly sibling sets).

**Cloud-runner egress note (2026-08-09 02:1xZ):** `api.the-odds-api.com`,
`gamma-api.polymarket.com`, `clob.polymarket.com`, `clevelandfed.org`, and
`xtracker.polymarket.com` were ALL reachable from the cloud runner this
cycle with no proxy errors — the 2026-08-08 EGRESS_BLOCKED entries
(journal/proposals.md) were evidently transient/flapping, not a standing
gap; re-verify reachability each cycle rather than assuming yesterday's
block still holds, and don't skip a source without trying it first.

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
     **Recheck stop rule (DEEP-2026-08-13):** after a market-confirms /
     no-edge log, a recheck is warranted only by NEW information (fresh
     guidance, a filing, a named headline) — never by elapsed time alone.
     Two consecutive rechecks concluding "no new information, book moved
     further toward consensus" close the candidate until resolution; log
     the closure once in funnel notes and stop touching it. Evidence:
     AMAT (`3347174`) was re-researched 4 times in 11h (17:20Z, 21:19Z,
     01:15Z, 04:14Z on 2026-08-12/13) with an unchanged est 0.90 and the
     identical conclusion each time — three of those touches bought no
     information and cost attention the disagreement-generating
     categories should have had.
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

**Exploration budget, AI model release-date markets (2026-08-11 02:xxZ, first
test of this category).** Hypothesis: "product release-date markets have a
reachable benchmark (official roadmap, credible leak) the way earnings/econ
releases do." Tested on `3206142` (Gemini Pro release by Aug 14, PM Yes
0.065). WebSearch surfaced only rumor-aggregator blogs (coursiv.io,
codersera.com, cometapi.com, felloai.com, androidinfotech.com) with mutually
conflicting rumored dates — none citing a primary Google statement with a
specific date. One credible secondary mention: Bloomberg reported the model
"months behind schedule", and Google itself said 2026-07-21 it is "currently
testing with partners" (still no ship date). Result: **not reachable for
date precision** — same shape as the esports-echo and tip-site traps, an
aggregator swarm around a real but vague signal — though the vague signal
(delayed) is directionally corroborated by Bloomberg and agrees with PM's
own low pricing. Recorded market-agrees, not benchmark-unreachable, since
the direction (not the date) was confirmable. Category ruled OUT for
date-precision bets absent a primary-source (official blog post, SEC
filing, named-exec statement) announcement with an actual date; revisit
only if one surfaces for a specific candidate.

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

## Forecast ledger: what it can and cannot test (DEEP-2026-08-10)

First scored window (2026-08-09/10): 54 forecasts recorded, 18 settled,
brier_delta +0.001 (z -0.15) — estimates that agree with the market settle
at market. Reassuring, and expected by construction. Three durable rules
from the window:

1. **The disagreement gap is the number to watch, not aggregate
   brier_delta.** Only 6 of 55 recorded rows carry ask-edge ≥ 0.02
   (3 politics, 2 econ, 1 earnings — ZERO sports), and none has settled;
   the threshold sweep is empty. Sports-devig forecasts structurally
   cannot test disagreement calibration: the estimate (devigged book
   consensus) and PM's price are downstream of the same books, so
   agreement is baked in. Only independent-source estimates — polls,
   official prints, consensus EPS, count extrapolations — produce rows
   where est and price genuinely differ. When allocating research
   minutes, weigh a candidate partly by whether it can ADD a
   disagreement row, since that is the only stream that will ever answer
   "are we calibrated when we disagree?".
   **No-side blind spot (DEEP-2026-08-14):** score.py's threshold_sweep
   simulates only the forecasted-outcome side at the recorded ask
   (operator note 2026-08-09), so a disagreement where the model sits far
   BELOW a wide market computes a negative Yes-edge and lands in no
   bucket. "Every sweep bucket negative ⇒ zero settled evidence of edge
   when disagreeing" is therefore a claim about the Yes-side stream only.
   The settled No-side disagreements to date (PPI 5.3%: est 0.036 vs mid
   0.171; ≥6.0%: 0.003 vs 0.042) both went the agent's way — n=2,
   event-correlated, proves nothing, but retros must not cite the sweep
   as if it covered this stream. Proposal for a No-side sweep slice filed
   2026-08-14 (journal/proposals.md).
2. **Record even when declining — especially when declining.** The
   outside-view veto (>0.10 claimed edge) would be unfalsifiable if
   declined estimates were never scored. The 2026-08-10 declines (PLBY
   claimed 0.14; WI Hong ≥30% bracket claimed 0.117) are both recorded
   as forecasts, so the veto gets out-of-sample grading at zero bankroll
   cost. **Pre-registered (grade in the next deep retros, explicitly):**
   WI Hong brackets (settle ~Aug 11) and PLBY (Aug 10 night) — declined
   side loses ⇒ veto validated; declined side would have won ⇒ first
   evidence the veto over-fires. CPI rows (Aug 12) grade the econ pivot.
   **PLBY graded (DEEP-2026-08-11): veto validated, instance one.** Yes
   resolved No; the declined bet (est 0.33 vs ask 0.19, claimed edge
   0.14) would have lost $5. Nuance worth keeping: the 04:16Z revised
   estimate (0.33) was WORSE against the outcome than the stale 00:23Z
   row (0.28) — a re-verification that "confirms a real signal" can
   still move the number the wrong way, which is why revised-away rows
   should be scored as their own slice if revision support lands
   (journal/proposals.md 2026-08-10). Still pre-registered, settling
   2026-08-11 night: WI Hong brackets (claimed edges to 0.117), SC
   Nordone (claimed 0.27) / Fry (claimed 0.196) / Norman, MN Craig
   (claimed 0.15) / Flanagan. The next deep retro grades EVERY one of
   these rows explicitly — each is veto-validated or veto-over-fires;
   an over-fire (Fry or Craig hitting) reopens the well-evidenced-
   polling-exception question at a measured foregone cost.
   **GRADED (DEEP-2026-08-12, provisional — on-chain prices near-certain,
   UMA resolution pending): zero over-fires; every decided disagreement
   went to the market. Row-by-row table and the durable primaries rule in
   the "Primary batch graded" section below.**
3. **A materially revised estimate deserves a row, but forecast.py holds
   one live row per market+outcome** (anti-flooding, by design —
   revision support is proposed, journal/proposals.md 2026-08-10). Until
   then: when a re-verification materially changes the estimate or the
   price has moved enough to change the decision (PLBY: ask 0.25 → 0.19
   between 00:23Z and 04:16Z), record the revised read in funnel.jsonl's
   note so the settlement grading can weigh the estimate that was
   actually current, not just the stale row.

**Exploration budget, low-media-coverage international elections (2026-08-10
~14:5xZ, first test of this category).** Hypothesis: "national elections
outside the US/UK/major-EU set have the same WebSearch-reachable polling
infrastructure as domestic races." Zambia's 2026-08-13 presidential election
(Hichilema vs Mundubile, PM prices Hichilema 0.91): every findable number was
either a self-selected Facebook/online poll (55/35, 50/45) or a partisan
domestic outlet's house prediction (Lusaka Times, Zambian Observer) — no
Afrobarometer, Ipsos, or comparable scientific-sample poll turned up.
Directionally unanimous (all sources favor Hichilema by a wide margin,
consistent with PM's price), but not precise or credible enough to
independently benchmark a specific probability — treated as
benchmark-unreachable, no forecast recorded (honest-estimate rule: don't
invent a number from unscientific sources). Category result: **reachable
only for directional confirmation, not for a point estimate** — the opposite
failure mode from the UK-GDP contradictory-single-sources case (there,
credible sources disagreed; here, only non-credible sources exist at all).
Revisit on an internationally-polled race (Afrobarometer-covered country,
or one with an Economist/YouGov country tracker) before generalizing further
to this category.

**UK Q2 GDP re-check, one day pre-release (2026-08-11 06:xxZ) — two new red
flags beyond the 08-08/08-10 contradictory-forecast finding.** (1) The
sibling set (`siblings.py` on event 486133, 7 legs: negative, 0-0.1%,
0.2-0.3%, 0.4-0.5%, 0.6-0.7%, 0.8-0.9%, >=1.0%) has unexplained GAPS —
0.1-0.2%, 0.3-0.4%, 0.5-0.6%, 0.7-0.8%, 0.9-1.0% have no corresponding
market at all, so a print landing in one of those bands would apparently
make every listed sibling resolve No simultaneously. Either Polymarket
defines an implicit rounding/bucketing rule not stated in any one market's
description, or the bracket set is genuinely incomplete — don't treat the
7-leg sum-check (1.0695, normal-looking vig) as informative until this is
understood, since a sum computed over a non-exhaustive partition means
nothing. (2) Each market's own resolution text says it resolves off the
**"Second quarterly estimate, UK"** release "scheduled for August 12,
2026," but links to the ONS's `gdpfirstquarterlyestimateuk` bulletin page,
and a fresh WebSearch (Berenberg's Andrew Wishart, named source, Q2 growth
"0.3% or 0.4%" barring a weak June) independently found the *first*
quarterly estimate is scheduled for **August 13**, not the 12th — first
vs. second estimate is a real distinction (different data vintage) and the
date named in the market contradicts external reporting on the actual ONS
calendar. Compounding: Berenberg's 0.3-0.4% point sits exactly in one of
the undefined gaps above. Two independent ambiguities (which release, and
whether the brackets even partition the outcome space) on top of the
already-known forecast disagreement — treated as `ambiguous-resolution`,
not `benchmark-unreachable` (the earlier framing): even a perfect
benchmark wouldn't tell me which bracket wins here. No forecast recorded.
If revisited after the release actually lands, check which day it
actually printed on and whether an off-grid GDP value produced a NO sweep
across all listed brackets — that would confirm or refute the gap-bucket
reading with real data at zero cost.

**Post-release grading (DEEP-2026-08-14) — test run, result inconclusive,
item CLOSED.** The hourly cycles dropped this watch item (no cycle after
2026-08-11 23:24Z touched it — third instance of the no-carrier failure,
see schedule.json `watch_items`); the deep retro ran it: event 486133 is
fully resolved, **0.4-0.5% bracket Yes, all six other legs No** (gamma,
umaResolutionStatus resolved on every leg). The print landed on-grid, so
the gap-bucket hypothesis (off-grid print ⇒ all-No sweep) was never
exercised — untested, not confirmed. The abstention cost nothing (no
bettable structure either way), and the first-vs-second-estimate date
ambiguity evidently did not prevent clean resolution. Carry the lesson,
not the item: bracket sets with undefined gaps stay `ambiguous-resolution`
until a listed bracket is priced wrong on its own terms.

## PPI YoY brackets: base-effect projection, first instance (2026-08-11)

New category, econ-ppi (never researched before this cycle; scan's econ-tag
query surfaced only 3 of the event's 10 sibling brackets, same
discovery-gap shape already seen repeatedly on CPI — full set only
recoverable by pulling the gamma event directly). Method for projecting
next month's YoY print from the current one: `YoY_next(NSA) ≈
YoY_current(NSA) × (1+MoM_next_consensus) / (1+MoM_sameMonthLastYear_actual)
− 1`. This works because the 12-month change is NSA but a same-calendar-
month seasonal factor cancels between the two years, so chaining forward
with SA consensus MoM figures (the only ones publicly forecast) is a valid
approximation, not a basis mismatch — confirmed by cross-checking the BLS
release text explicitly labels the 12-month change "not seasonally
adjusted" and MoM "seasonally adjusted" (bls.gov/news.release/ppi.nr0.htm).
Applied to July 2026: Jun26 YoY 5.5% NSA (BLS-confirmed) × Jul26 MoM
consensus +0.1% (tradingeconomics) / Jul25 MoM actual +0.9% (an unusually
hot print rolling out of the base) ⇒ central estimate ~4.7% NSA, wide of
the market's own apparent mode. Practical notes for reuse:

1. **Needs the actual (not just consensus-implied) same-month-last-year
   MoM** — this is where the edge came from (Jul25's atypical +0.9% MoM
   makes Jul26 YoY decelerate faster than a naive "MoM stays flat"
   read would suggest). Skipping this step is the most likely way to get
   the method wrong.
2. **SD calibration is thin** (n=2: May consensus-miss +0.4pp, June
   -0.3pp) — used sd=0.45pp, deliberately on the wide/conservative side.
   Revisit once more monthly misses are observed.
3. **This event's book was bumpy/non-monotonic across adjacent 0.1pt
   brackets** (Yes prices ...0.073, 0.168, 0.0485... not smoothly
   decreasing away from the mode) and summed to ~1.14 — a thinner,
   less-arbitraged book than the CPI event. Several legs showed large
   nominal model-vs-market disagreement (5.3%, 5.4%, ≥6.0% all >0.10
   apparent edge) but all had spread > max_spread 0.06 — wide-book veto
   applied and declined regardless of edge size, per the DEEP-2026-08-07
   large-claimed-edge caution. Only the `<=5.1%` leg had a tight book
   (spread 0.02) and a sub-0.10 edge (0.06) — that's the one bet placed.
4. **Pre-registered for grading**: settles with the Aug 13 08:30 ET BLS
   PPI release. First out-of-sample test of this technique — do not
   reuse it confidently on other econ-print brackets (CPI, PCE, etc.)
   until this one grades.

**Graded (DEEP-2026-08-13, RETRO-20260813-1707): WON.** July PPI printed
inside the ≤5.1% NSA YoY bucket as the projection estimated; the bet leg
(`b35963f465b4`, est 0.84 vs ask 0.78) settled +1.41, and all nine sibling
forecast legs (5.2% through ≥6.0%, est_prob 0.00-0.05) correctly resolved
lost, confirming the whole distribution shape, not just the one bucket.
n=1 event — this clears the pre-registration bar (reuse with the same
small-n caution as the sd=0.45pp calibration note above, not yet a proven
technique) but is not a track record; do not port to CPI/PCE brackets
without separately checking the sibling book's mode against the projected
central estimate each time.

**Correction (DEEP-2026-08-14) to RETRO-20260813-1707's counterfactual
claim.** That retro stated the two wide-spread-vetoed sibling legs (5.3%,
≥6.0%) "would have lost had they been bet, reconfirming that veto." Wrong
side: the model's apparent edge on both legs was **No-side** (the funnel
notes themselves say "large No-side edge"). Redone with fill arithmetic:
5.3% (5ad483698a95, bid/ask 0.133/0.209) — No ask 0.867 vs model No
0.964, realizable edge 0.097, and the bracket resolved No, so a $5 No bet
would have **WON ≈ +$0.77**; ≥6.0% (4908388c9fd7, bid/ask 0.003/0.08) —
No ask 0.997 vs model No 0.9973, edge ≈0.0003, **no realizable trade**
(the apparent edge vs the mid evaporates crossing the spread — which is
the actual justification of the spread veto on that leg). Net: the
wide-spread veto's settled counterfactual record here is 1 missed win +
1 correct non-trade, not 2 saves. Rule for future retros: counterfactuals
get the same arithmetic as real fills — side, realizable ask, spread —
never a narrative verdict.

## Primary batch graded (DEEP-2026-08-12, provisional pending UMA)

The largest pre-registered disagreement batch on record settled on-chain
overnight (WI/SC/MN primaries, 2026-08-11). Grading is against live gamma
prices at 04:4xZ Aug 12 — SC and MN legs are at 0.99+, effectively decided;
the WI *winner* is genuinely uncalled (Crowley +0.4pp with ~87% counted,
market ~0.90/0.07), but every margin bracket ≥5% is decided No regardless of
winner since the realized margin is under 1pp either way. Finalize at UMA
resolution; nothing below is expected to flip except possibly the WI winner
legs and the Hong-by-<5% bracket, which are explicitly NOT graded.

**Official settlements trickling in (DEEP-2026-08-13):** three
politics-primary forecast rows have now settled on-chain via resolve.py
(score.py politics-primary n=3, brier_delta +0.1109), including SC Fry
(officially LOST, matching the provisional grade). Every official
settlement so far matches its provisional grade; the batch's remaining
rows are among the 31 open forecasts. No re-grading needed unless a WI
leg resolves against its provisional call.

| Row (forecast est vs mkt at record) | Outcome | Verdict |
|---|---|---|
| SC Nordone round-1 No lean (0.33 vs 0.595, claimed 0.27 — largest ever) | Nordone WON (0.99) | veto validated #2: $5 No bet would have lost |
| SC Fry round-1 Yes (0.27 vs 0.0705, claimed 0.196) | Fry LOST (0.003) | veto validated #3 |
| MN Craig nominee Yes (0.45 vs 0.295, claimed 0.15) | Craig LOST (0.0005) | veto validated #4 |
| MN Flanagan nominee No lean (0.52 vs 0.715, claimed ~0.195) | Flanagan WON (0.9995) | veto validated #5 |
| WI Hong ≥30% margin Yes (0.23 vs 0.10, claimed ~0.12) | margin <1pp ⇒ No | veto validated #6 |
| WI Hong 25–30% / 20–25% (0.22 vs 0.135 / 0.24 vs 0.1845) | No | veto validated (same model, counted with #6) |
| MN Gov Lindell lean (no forecast row — declined to estimate, 2026-08-09 pre-registration) | Demuth WON (0.9995) | confirmation per its own pre-registration |
| SC Norman (0.32 vs 0.325, no-edge) | Norman LOST | at-market, no signal |
| WI low brackets <5%/5–10%/15–20% (est below mkt) | ≥5% ones No | agent leaned righter, but same model that missed everything else — no credit claimed |

Aggregate over the 13 forecast rows (provisional outcomes): agent brier
≈0.174 vs market ≈0.116, delta ≈ +0.058 — the market decisively better,
concentrated exactly in the large-claimed-edge rows. **The outside-view veto
is now 6-for-6 with zero over-fires (PLBY + these five), all at zero
bankroll cost.** The line-511 question ("well-evidenced polling exception in
low-candidate-count primaries?") is answered: NO exception. The SC internal
poll had Fry "narrowly ahead" — he got ~3% of the market's final price; the
two aligned WI polls had Hong +24 — realized margin under 1pp.

**The WI twist cuts deeper than "market right, agent wrong": the market was
wrong too.** PM had Hong ~0.89-0.92 to win from Aug 7 through Aug 10;
Crowley now leads. The polls-to-margin model normal(mean 24, sd 8) put est
0.01 on "Hong by <5%" — reality landed at ±0.5pp, a beyond-99th-percentile
miss of the model's own distribution. Low-turnout primaries are a category
where sparse polling has no predictive validity AND the market price itself
can be badly wrong — deference to the market here is not a safe harbor,
it's just a cheaper way to be wrong.

**Durable rule (contested primaries):** in contested-primary win/margin
markets, polling-derived independent estimates are not bettable at any
claimed edge (0-for-6 record above), and market-agrees positions are not
safe either (WI). The category is research/forecast-only — record forecasts
to keep measuring, never bet, unless the estimate has a mechanical anchor
(e.g. substantially-complete official count with the market lagging it).
Uncontested or landslide-polling primaries with the market already at 0.9+
stay in the no-edge bucket they already occupy.

**Extension to general elections (DEEP-2026-08-13, scope clarification —
not new evidence):** the bar applies to ANY election win/margin market
where the estimate has no numeric, methodologically-credible polling and
no mechanical anchor — qualitative "expected to win" framing, however
unanimous across outlets, is the same evidence shape that went 0-for-6 in
the primaries. The 04:14Z 2026-08-13 cycle already applied this by
extension on Zambia (fa185b55a5c3, est 0.87 vs ask 0.93, declined —
correct call, wrong skip label, see §Skip-reason taxonomy `category-bar`);
this paragraph makes the extension a rule so future declines don't need
to re-derive it. Zambia is the first out-of-sample test of whether the
bar's logic generalizes beyond primaries — grade it at settlement as a
test in progress, not as supporting evidence. Elections WITH credible
numeric polling (Afrobarometer/Ipsos-class, or an Economist/YouGov
tracker) are outside the bar and go through the normal estimation path;
the WI lesson (market-agrees is no safe harbor) still applies there.

## Outside-view veto: settled counterfactual ledger (DEEP-2026-08-15)

Per-row fill arithmetic over ALL settled `outside-view-veto` forecast rows
(flat 1u on the model's side at the recorded book; the discipline the
RETRO-20260813-1707 correction demanded). This table supersedes every
narrative "N-for-N" veto claim; future veto-record statements cite it and
extend it at each settlement.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| SC Nordone (57f222efb516) | 0.33 / 0.595 | No | +0.260 | Yes | −1.00 |
| SC Fry (e5666c235356) | 0.27 / 0.071 | Yes | +0.196 | No | −1.00 |
| MN Flanagan (75f2545a7a0e) | 0.52 / 0.715 | No | +0.190 | Yes | −1.00 |
| MN Craig (9ab914d80a5b) | 0.45 / 0.295 | Yes | +0.150 | No | −1.00 |
| PPI 5.3% (5ad483698a95) | 0.036 / 0.171 | No | +0.097 | No | **+0.15** |
| PPI 5.4% (169b4fd6c04a) | 0.027 / 0.049 | No | −0.019 | No | non-trade |
| PPI ≥6.0% (4908388c9fd7) | 0.003 / 0.042 | No | ~0.000 | No | non-trade |
| Musk 120-139 (5ef2f363f039) | 0.165 / 0.085 | Yes | +0.080 | No | −1.00 |
| Musk 140-159 (b7a58fd571c8) | 0.64 / 0.415 | Yes | +0.220 | No | −1.00 |
| Musk 160-179 (e06e9b2bea70) | 0.189 / 0.385 | No | +0.191 | No | **+0.61** |
| Musk 180-199 (eb09f3632c5d) | 0.003 / 0.095 | No | +0.087 | Yes | −1.00 |
| Musk 2d 40-64 (10029a75295e) | 0.499 / 0.39 | Yes | +0.099 | Yes | **+1.50** |
| Musk 2d 65-89 (53c5bf348303) | 0.501 / 0.62 | No | +0.109 | No | **+1.56** |
| Japan GDP 0.0-0.8% (d684f9caff81) | 0.2475 / 0.49 | No | +0.2125 | No | **+0.85** |

**Totals (2026-08-17): 12 realizable disagreement trades, 5W/7L, net
−2.33u (−$11.65 at $5 flat).** Sub-classes now split by MODEL GENERATION,
because the two 2026-08-15 additions are the first settled rows from the
14-day empirical bootstrap (every earlier self-model row was Gaussian or
naive): pre-bootstrap self-model 1W/7L (−6.39u); bootstrap 2W/0L (+3.06u)
— but the two bootstrap rows are complementary brackets on ONE realized
tweet count (40-64 landing makes both legs win by arithmetic), so this is
effectively n=1 independent outcome, off-fork, and buys no veto exception
by itself. Wide-spread rows: 1 realizable, won (+0.15u); the spread rule's
entire settled cost remains one foregone ~+$0.77 win. Side split: Yes-side
1W/4L (−2.50u); No-side 4W/3L (**+1.17u**) — the No-side stream has turned
positive and remains fully invisible to the current threshold sweep (see
the 2026-08-14 proposal, evidence updated again). Brier view: self-model
n=10 mean dBrier +0.068, market better 7/10.

**New sub-class, first instance (2026-08-17): mechanical-econ Gaussian
self-model.** Japan GDP 0.0-0.8% is a Gaussian model on an official macro
print (Normal around a named survey consensus, unvalidated sd), same model
generation as the pre-bootstrap SC/MN/Musk rows but a different domain —
those are behavioral/political predictions, this is a mechanical release
the way econ-cpi/econ-ppi bets already are (DEEP-2026-08-14 "Known
unknowns" mechanical-econ family, pooled brier_delta -0.0104 over 27
settled bets/forecasts). This one row won at +0.2125 realizable edge,
opposite the "0-for-multiple" framing the pre-bootstrap self-model rows
established — but n=1 in this specific sub-class is not evidence of
anything on its own (schedule.json's own guardrail: no category verdict
below ~15 settlements). Track separately going forward; do not fold into
the pre-bootstrap self-model 1W/7L line above, and do not grant a veto
exception on this single row.

**Decision implications:** (1) the 0.10 veto boundary stays — the full
ledger is still net −3.18u and the only positive sub-slice is one
correlated event pair from the new model; (2) whether the bootstrap
deserves different treatment is exactly the pre-registered fork
(§social-media-postcount), decided by the Aug 18 weekly legs — not here,
not on off-fork rows; (3) the path to more placements is still expanding
the mechanical/No-side realizable classes (econ prints, cross-market
arithmetic); (4) every counterfactual claim uses this table's arithmetic —
side, realizable ask, spread — never a narrative "would have lost/won".

**Exploration budget, UMich Consumer Sentiment brackets (2026-08-16 07:15Z,
first test of this category).** Hypothesis: mechanical monthly print (final
release Aug 28), same fact-finality profile as the econ-cpi/econ-ppi/econ-pce
family that's the only settled-positive family so far — but this print has a
PRELIMINARY release (Aug ~15) ahead of the final, so the open question is
whether the prelim-to-final revision is a reachable, model-able benchmark or
another self-model trap. Prelim August print (WebSearch): 51.0, down from
54.5 consensus / July final 55.2, on a broad-based deterioration narrative
(Hsu: short-term business-conditions expectations -11%, long-term -17%).
Tried to source a clean historical prelim-vs-final revision series to model
the Aug 28 final: FRED (`fredgraph.csv`), advisorperspectives.com, and
tradingeconomics.com's data table all 403'd/were unextractable from this
runner (same site-blocking pattern as the existing forebet/oddsportal/
Metaculus entries) — only WebSearch news summaries were reachable, n=3
recent months, one containing an internally-inconsistent arithmetic claim
("7.5-point increase" that didn't match the two cited numbers). **Result:
reachable for the point print (Yes) but NOT reachable for a trustworthy
revision-variance benchmark (No)** — property 2 fails on the model input,
not the headline fact. Built a deliberately fattened N(50.5, 3.5) anyway to
see the shape: it still couldn't reproduce the market's ~13% combined mass
on the >=58 brackets (own siblings.py sum_check 0.982, a well-calibrated
book) without an unreasonably large sd — the same Gaussian-tail-
underweighting mechanism already confirmed and fixed-via-bootstrap on the
Musk brackets (2026-08-13/14), now found in a second, unrelated bracket
category on first contact. Two brackets cleared the >0.10 outside-view
boundary on this admittedly-shaky model (below-49.0 edge +0.157, ALSO
spread-vetoed at 0.171; 49.0-51.9 edge -0.109, spread fine at 0.05) —
declined both per the veto. The two most liquid/tradeable brackets
(49-51.9 ask 0.43, 52-54.9 ask 0.27, spreads 0.05/0.01) showed only
sub-floor edges (-0.109 already counted, -0.030) once measured against the
live CLOB ask rather than gamma mid. Net: 0 bets, 7 forecasts recorded
(a5703b36d60a…d5dcc12cdabe). **Category ruled in as mechanically reachable
or the headline print, ruled out for self-modeling the revision without a
better vintage dataset** — if revisited, only with either (a) a reachable
prelim-to-final revision history (try `alfred.stlouisfed.org` specifically,
untried this pass — ALFRED vintages differ from the plain FRED series URL
that 403'd), or (b) treating the market's own book as the prior and looking
only for a genuine information edge on top of it, not a from-scratch
distribution.

**Exploration budget, one-off exhibition match via single-book WebSearch,
first test (2026-08-16 11:18Z).** Named property: does a one-off exhibition
fixture with no dedicated odds-api league feed still have a trustworthy
single-book line reachable by WebSearch (as opposed to the odds-aggregator
"best odds across bookmakers" trap already ruled a no-go, Boca/Estudiantes
2026-08-05), and does a 3-way h2h devig map cleanly onto a PM derivative
submarket when the pool has no plain moneyline submarket for the event? FA
Community Shield Arsenal vs Man City (today, not in the-odds-api's
`soccer_epl` fixture list — a separate exhibition, not a league match).
WebSearch surfaced a DraftKings-network article (dknetwork.draftkings.com,
DK's own staff analysis piece quoting DK's own line, not an aggregator) with
a clean 3-way moneyline: Arsenal +145 / Draw +240 / City +155 → power devig
fair Arsenal 0.3764 / Draw 0.2633 / City 0.3603. The PM pool for this event
has no plain "Arsenal wins"/"City wins" submarket, only derivative ones
(draw-yes/no, five O/U total lines, BTTS, neither-scores-first); of those,
only draw-yes/no maps directly onto a devigged h2h number without needing a
goals-distribution model. PM draw market (3449517) ask Yes 0.29/bid 0.28,
ask No 0.72/bid 0.71 — edges No +0.0167, Yes -0.0267, both well under
min_edge_book_devig 0.07. **Result: reachable** (single named-book source
held up, no aggregation-mixing needed) **and the devig-to-derivative-
submarket mapping works cleanly for a draw/no-draw split specifically** —
but **no edge**, the same efficient-market pattern as every other liquid PM
sports book tested (UFC, MLB, tennis). The O/U and BTTS submarkets on this
same event were left unresearched: matching them would require a total-
goals number from the same single book, which this source didn't provide,
and building one from a different book would repeat the cross-book-mixing
trap — a genuinely separate, still-untested question (does a single book
publish a matching total alongside its h2h for an exhibition fixture) if
revisited.

**Exploration budget, AAA gas-price touch-anytime brackets, first test
(2026-08-17 00:24Z).** New candidate class found in scan: "Will gas hit $X
(Low/High) by August 31?" (event 769509, 8 sibling legs, resolves Yes if the
AAA US national-average regular-gas price touches the threshold on ANY day
from market creation to end date — a barrier/touch condition, not a
point-in-time print). Named property: is a mechanical, officially-sourced
(AAA) commodity threshold, with weekly public data (AAA newsroom, EIA),
reachable and modelable the way the mechanical-econ family (CPI/PPI) has
been. Current price $4.0656 (Aug 16); the observed window since market
creation (Jul 27 $4.096 -> Aug 16 $4.0656, weekly n=4) stayed inside a tight
~$4.00-4.10 band. Built a no-drift diffusion/barrier-touch model (reflection
principle) off a daily sigma estimated from those 4 weekly deltas (~2.1c/day,
explicitly an UNVALIDATED small-n estimate, same caveat class as the Japan-
GDP and UMich-sentiment SD choices) — gives near-zero touch probability for
every one of the 8 thresholds (nearest legs $3.90/$4.25 at 3.5%/1.9%, the
rest <0.5%), while live asks price every leg at 9-29%. **Result: the
disagreement is large (>0.10) AND uniform across all 8 siblings
simultaneously** (not one outlier leg) — the same shape as the already-
documented siblings.py sum-check caveat (2026-08-05: thin/placeholder
pricing produces sum-check flags that are a data-quality tell, not an edge)
and a fourth instance of the Gaussian/diffusion-tail-underweighting failure
already confirmed on Musk brackets and UMich sentiment. Book quality was
mixed — the nearest leg ($3.90) actually has a real book (spread 0.02, ask
depth 200), so this isn't purely a thin-book artifact there, which makes the
uniform-gap read (self-model distrust) the operative reason over
wide-spread-veto; several other legs are separately thin (null bid, spread
up to 0.20). Declined all 8 as `outside-view-veto` (self-model + large
disagreement, both-apply case per the DEEP-2026-08-14 taxonomy rule —
estimate distrust dominates), 8 forecasts recorded (e2cbca37fe88, plus 7
siblings same batch), 0 bets. **Category ruled in as mechanically reachable
and worth tracking (public AAA/EIA source, new touch-barrier structure not
seen before) but the naive small-n diffusion self-model is not trustworthy
enough to act on here, exactly like the other self-model categories** — if
revisited, needs either a validated historical daily-price series (not just
4 weekly points) to get a real sigma, or evidence the 24h-volume=0 legs
specifically are seeded/placeholder (would explain the wide-leg gaps without
needing a sigma fix at all, leaving only the $3.90 leg's real-book gap to
explain).

## Known unknowns (to resolve with data)

- Which categories actually have positive brier_delta for me. (Bet small and
  wide until `core/score.py` shows n≥30 per category.)
  **Status DEEP-2026-08-14:** the mechanical-econ family (econ + econ-cpi +
  econ-ppi settled forecasts) is the first family-sized slice on the good
  side: pooled brier_delta -0.0104 over 27 rows — but those rows are ~6
  independent release events, so treat as a concentration signal (keep
  routing research to official-print releases), not a proven edge. Both
  settled econ bets won (a3bc5c4, b35963f465b4).
- Whether thin esports books are exploitable or just wide.
- Whether earnings markets are efficient at pricing whisper numbers.
