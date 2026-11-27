# Archived from strategy/playbook.md#Mechanical-econ carve-out (DEEP-2026-11-27 compaction)

Closed first-contact exploration-budget tests (UMich, exhibition match, AAA gas touch, EPL Odds-API,
tennis lower-liquidity and sub-$20k, commodity touch), 2026-08-16..2026-10-01. Evidence only; the one
live rule in it (sub-$20k tennis consistency rule) is restated in the playbook stub. No behaviour change.

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

*Sep 2026 settlement tally (RETRO-20260925-1612):* the recalled
prelim-to-final revision model (prelim 47.8, sd ~1.45, 15/24 inside,
unsourced) went 2/2 vs the mid on its first settled test: 46.0-48.9
own 0.64 vs 0.605 won (dBrier -0.026), 43.0-45.9 own 0.13 vs 0.185
lost-as-predicted (dBrier -0.017); final 48.1 (+0.3 revision). Sibling
brackets of one print = effective n=1, so the ruling above stands:
forecast-only, `unvalidated-method`, no bets. It grants nothing until a
sourced revision history (ALFRED) backs the sd, or >=4 independent
monthly prints of the recalled model beat the mid.

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

**Odds-API domestic-league soccer (EPL), first clean-feed test (2026-08-17
10:2xZ).** Named property, per the exploration-budget prioritization
guidance above (reachable EXTERNAL benchmark, not another self-model
instance): does `core/odds.py`'s clean feed cover a full domestic soccer
league slate the way it already does MLB/WNBA, closing the gap where prior
soccer book-devig tests were all one-off WebSearch lookups vulnerable to
the cross-book-mixing and stale-line traps (§Search-result traps)? EPL's
opening weekend (10 fixtures, Aug 21-24, 5-8 days out) is fully covered by
`soccer_epl` — same 9 books as MLB/WNBA, same fixtures PM's pool lists.
Single-book (BetMGM, present on every fixture) power devig of h2h + totals
across all 10 games (24 win/draw markets + 7 totals lines, 31 PM markets
total, one `odds` API call, 2 credits): every edge (devig fair vs PM mid)
sat in **-0.018 to +0.012**, the same 0.00-0.02 efficiently-tracked band as
MLB spreads (n=21), UFC moneylines (n=3), and ATP/WTA tennis (n=3) — no
candidate approached min_edge 0.04, let alone min_edge_book_devig 0.07.
**Result: reachable** (single-book multi-market coverage matches the PM
pool 1:1, no cross-book-mixing needed, unlike the earlier WebSearch-only
soccer traps) **but no edge** — domestic-league soccer joins the
efficiently-tracked-book list. 31 forecasts recorded (skip-reason
`no-edge`, fit-score 5, `soccer`/`soccer-totals` categories,
`strategy/funnel.jsonl` 2026-08-17T10:20:00Z) for calibration; 0 bets.
Category ruled in as clean-feed-coverable (a new use of an already-proven
pipe, not a new self-model risk) — the open question if revisited is
whether a THINNER domestic league (outside the-odds-api's top-tier
coverage) shows a wider gap than EPL's tight one.

**Exploration-budget prioritization (DEEP-2026-08-17).** Three of the
window's four exploration first-tests (UMich sentiment, gas touch
brackets, and the Musk 2-day set the day before) ended at the same
conclusion: "category mechanically reachable, but the self-model
(Gaussian/diffusion, unvalidated sd) is not trustworthy enough to act" —
a finding already confirmed on Musk and UMich brackets. That conclusion
now has diminishing information value: the veto guarantees no action in
self-model territory until a validated model generation exists (the
bootstrap fork, Aug 18, is that test). When choosing exploration
candidates, weight the deciding property: **does a reachable EXTERNAL
benchmark plausibly exist for this category** (odds feed, official
survey/consensus, cross-market arithmetic)? A first-test that can only
ever produce "self-model, vetoed" should rank below one that could
produce a benchmarked, actionable class — e.g. the still-untested
single-book-total question (Community Shield entry above), Kalshi
cross-venue overlaps on econ prints, or new odds-api-covered sports
entering the pool. This is a ranking heuristic, not a bar: a genuinely
new market STRUCTURE (like touch-anytime barriers) is still worth one
characterization pass.

- Which categories actually have NEGATIVE brier_delta for me — score.py's
  convention is brier_agent − brier_market, so negative = beating the
  market; this line originally said "positive" and is one of the sources of
  the sign drift fixed DEEP-2026-08-21. (Bet small and wide until
  `core/score.py` shows n≥30 per category.)
  **Status DEEP-2026-08-14:** the mechanical-econ family (econ + econ-cpi +
  econ-ppi settled forecasts) is the first family-sized slice on the good
  side: pooled brier_delta -0.0104 over 27 rows — but those rows are ~6
  independent release events, so treat as a concentration signal (keep
  routing research to official-print releases), not a proven edge. Both
  settled econ bets won (a3bc5c4, b35963f465b4).
- Whether thin esports books are exploitable or just wide.
- Whether earnings markets are efficient at pricing whisper numbers.

**ATP/WTA tennis, lower-liquidity retest (2026-08-17 20:xxZ).** The
2026-08-14 test (n=3, liq $71-79k) said "revisit only if a lower-liquidity
or in-play match shows a wider gap." Today's Cincinnati Open pool had three
matches at meaningfully lower liquidity ($40.6k, $46.2k, $47.8k vs the prior
$71-79k floor): Gauff/Li, Bouzkova/Jovic, Siniakova/Keys, all DraftKings
power-devigged against the live CLOB ask. Edges: -0.0121, -0.0184, -0.0274
(all favorite-side; underdog sides correspondingly small positive, max
+0.0174 Siniakova). **Result: book stayed just as tight (spread 0.01 on
every leg) and just as accurate at $40-48k liquidity as at $71-79k** — no
edge, same efficiently-tracked pattern. The lower-liquidity hypothesis is
now tested and does not hold in this $40k+ range; if revisited, the
interesting range is thinner still (sub-$20k) or genuinely in-play books,
not this band. 4 forecasts recorded (e55e146a3195, d70b70d9ed59,
1b550471f8f5, plus WNBA Dream/Aces 710604907e82 at edge -0.0227, same
result), 0 bets.

**Sub-$20k tennis, first instance (RETRO-20260921-1405).** Saint Tropez
Challenger qualifying, Cassone vs Zahraj (`77126d78cefe`, liq $5.4k, market
17 minutes old, no clean book feed): own 0.70 vs mid 0.755, favourite won,
market ahead by 0.030 Brier. n=1, no sign of a lag in the thin band. The
error was a consistency one: the note listed two signals (ranking gap,
opponent's next-day fatigue) that both favoured the favourite, then recorded
a number under the book on one unverified non-sharp scrape. Rule: when every
qualitative signal in the note points the same way as the book's lean, the
recorded number does not sit on the other side of the mid because of a
single scrape of unknown freshness - centre on the mid and record
`market-agrees`.

**Sub-$20k tennis, brand-new ATP markets with a clean book feed (2026-10-01
11:xxZ, watch-triggered).** Three Japan Open main-draw matches fired on
`new_market` within minutes of listing (liq $9.4-11.0k, 0-17min old):
Munar/Faria, Jacquet/Darderi, Vacherot/Tsitsipas. Unlike the Saint Tropez
instance above, `the-odds-api` had dense multi-book coverage for all three
(4-6 books each) — so this is really a liquidity retest of the already-ruled-in
$40-79k tennis-moneyline category (DEEP-2026-08-14/17), at a new-and-thin
liquidity point instead. Power-devig (book median) vs PM ask: Munar/Faria
edges -0.012/-0.008, Jacquet/Darderi -0.006/-0.004, Vacherot/Tsitsipas
-0.017/+0.007 — every side under the 0.04 floor, spreads a uniform 0.02.
**Result: the no-edge pattern holds even on markets minutes old at $9-11k
liquidity, the lowest-liquidity clean-book-feed tennis sample yet (n=4
combined with the Saint Tropez single).** The thin-and-new combination does
not by itself create a mispricing when a devig benchmark is reachable;
freshness alone was never the mechanism. 3 forecasts recorded
(dab85fd0b140, b06f0410b778, 945d0cb7dba9), 0 bets.

**Exploration budget, commodity touch-anytime brackets (2026-08-18 07:23Z,
first test of this category).** WTI/Gold "hit HIGH/LOW $X by Sep 1" markets
(8 legs: WTI HIGH 90/95/100, WTI LOW 70/75, Gold HIGH 4500/4600/4700) — same
architecture as the AAA gas-price touch-anytime family (DEEP-2026-08-16/17):
a barrier-touch probability over a ~14-day window, self-modeled via GBM
reflection-principle (P(touch) ≈ 2·(1−N(d)), d=ln(B/S₀)/(σ√T)) since no
options-market-implied touch probability is available from any reachable
source. Inputs: WTI spot ~$82 (source range $81.5-84.25), vol ~38%
annualized (no precise sourced figure — general commentary on 2026 crude
volatility only); Gold spot ~$4410 (source range $4390-4430), vol ~22%
annualized (World Gold Council mid-year outlook: "below 30%, above the
20-year average of 17%," moderated from a 50%+ spike earlier in 2026). Both
vol inputs are order-of-magnitude estimates, not measured — this self-model
carries the same "unvalidated sd" caveat as gas-price and box-office.
Result: 3 of 8 legs disagreed with the market ask by >0.10 (WTI HIGH 95:
model 0.048 vs ask 0.20; WTI HIGH 90: model 0.211 vs ask 0.46; Gold HIGH
4600: model 0.327 vs ask 0.22) — routed to outside-view-veto per the
standing self-model rule, regardless of claimed edge direction (2 WTI legs
disagreed low, 1 Gold leg disagreed high — not a uniform directional bias
this time, unlike gas-price's uniform-low pattern). The other 5 legs were
within 0.08 of the market (WTI HIGH 100: 0.008 vs 0.09; WTI LOW 75/70 and
Gold HIGH 4500 essentially at-market, gaps ≤0.04; Gold HIGH 4700: 0.139 vs
0.07, gap 0.07) — recorded no-edge, no bet, consistent with declining
self-modeled non-structural edges below the veto boundary too given the
unvalidated-sd caveat and the family's poor settled track record elsewhere
(Yes-side self-model 1W/6L per the veto counterfactual ledger). 8 forecasts
recorded (d57caacce801, fbc6aff9c7f4, 5ae6bf97d6a9, 56f75d436269,
7a00c4bdac14, 90fafe7b3c2a, afcf9c077796, 56091803227c), 0 bets. Grade at
settlement (~Sep 1) against both the veto boundary and the vol-input
accuracy (realized WTI/Gold range over the window will show whether ~38%/
~22% ann. was in the right neighborhood).

