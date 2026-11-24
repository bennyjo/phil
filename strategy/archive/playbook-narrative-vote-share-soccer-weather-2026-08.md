# Archived playbook narrative (DEEP-2026-11-24 compaction tranche 2)

Moved verbatim from strategy/playbook.md. The binding one-line restatements live in the playbook's "Live rules (compacted)" section.

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
to re-derive it. Zambia was the first out-of-sample test of whether the
bar's logic generalizes beyond primaries. **Settled (2026-08-18 18:16Z,
RETRO-20260818-1816): Yes, market right (ask 0.93), model's 0.87 discount
wrong — same evidence shape (qualitative "expected to win" framing, no
numeric poll) as the primaries, same result (market beat the discounted
estimate).** n=1 out-of-sample, consistent with but not by itself proof of
generalization; the extension rule stands, confirmed rather than untested.
Elections WITH credible
numeric polling (Afrobarometer/Ipsos-class, or an Economist/YouGov
tracker) are outside the bar and go through the normal estimation path;
the WI lesson (market-agrees is no safe harbor) still applies there.
Settled record of that carve-out (RETRO-20260907-1006): n=2 instances,
both correct. Kazakh Auyl/Respublica (Aug 23, three converging polls,
market-agrees, 2W/0L) and Sachsen-Anhalt AfD majority (Sep 6, dawum
tracker + politpro seat model, bet WON, brier_delta -0.0315; see §First
bet in 13 days for the seat-model family ruling). The carve-out stands
as written; two instances do not widen it.

**Another confirming instance of the durable bar itself (RETRO-20260916-0621):**
RI Governor GOP primary (Sep 8, 2026), category-bar declined on both
legs off the same Aug 3-11 poll (Pelino 37 / Guckian 17 / undecided 44,
n=857): `1d37368ed8f2` Pelino Yes est 0.80 vs mkt 0.905 **LOST**;
`09bc7a9861e8`/`ee25da18db9d` Guckian Yes est 0.09 vs mkt 0.098 **WON**.
The market itself was pricing the eventual loser at 0.905 the night
before the vote — same shape as the WI Hong/Crowley miss that founded
this rule (large undecided share, market wrong too, not just the
poll-derived estimate), at zero bankroll cost because the bar kept both
legs forecast-only. No rule change; the bar keeps calling this correctly.

**Price-inside-the-model-range rule (RETRO-20260921-0633, numeric-polling
elections and any other self-built model):** when my model prints a RANGE
across defensible input choices (poll weighting, recency window, error sd)
and the market price lies inside that range, the claimed edge is an input
choice, not a disagreement: record `no-edge` and do not bet. A bet needs the
price outside the WHOLE range by at least `min_edge`, and the forecast note
must quote the range. Evidence: Berlin Linke-most No `7ec71e307f12` LOST
−$5 (MC 0.55 recency-weighted to 0.665 newest-poll-only, price 0.665, own
0.60 picked mid-range, "edge" 0.05); all six Berlin Linke/CDU reads sat on
the CDU side of a deep 0.01-spread book and all six lost to the mid
(dBrier +0.005 to +0.114, one draw). Counter-instance where the test passes:
MV AfD `506bc4c8087e` (sd sweep 0.80-0.96 vs ask 0.77, won). Corollary
(label consistency): a market declined as `unvalidated-method` stays
declined on that method until a settled row validates it; a smaller edge
days later is not new evidence (Sep 14 decline at edge 0.06, Sep 18 bet at
0.05, same Gaussian). Keep counting, not yet a rule: in both Sep 20 states
my precedent adjustment (Berlin-2023 CDU bonus, Brandenburg-2024 SPD
consolidation) shaded AWAY from the poll leader and the poll leader won
(n=2 elections, one night). n=3 (RETRO-20261025-0815): BC Oct 24, my
2024-NDP-seat-efficiency shade lifted NDP-most-seats to 0.21 against the
models' 0.15-0.18 core, Conservatives (poll leader) won; both rows were
forecast-only (dBrier +0.031, +0.010). Still counting: three elections, no
paired test yet.


## First bet in 13 days: the AfD Sachsen-Anhalt audit (DEEP-2026-08-24)

The 2026-08-24 03:11Z cycle placed de95e5168de3 ($5 No @0.66, edge 0.05,
edge_class other, politics-general) on the AfD absolute-majority-of-seats
market (2244513), ending a 13-day placement drought. Deep-retro verdict:
**compliant on every written rule, and the write-up is the right shape**
— numeric-polling carve-out correctly invoked (dawum/wahlrecht tracker +
politpro seat model with an explicit 29% majority probability, not
qualitative "expected to win" framing), edge 0.05 clears min_edge 0.04 and
sits under the 0.10 outside-view boundary, spread 0.01, forecast
f37cee91366b recorded before placement, watch item added same commit,
single-source risk on the 29% figure self-flagged in the note. Two things
the rules did NOT catch, now pre-registered on the watch item rather than
legislated at n=0:

1. **Horizon.** This is the longest-dated position the book has ever
   held: 13 days entry-to-settlement vs ~2 days max for every prior bet.
   Nothing in risk.json prices the staleness of an entry-time estimate
   over two weeks of poll movement, and the ledger has no revision
   mechanism (open proposal). Not adding a max-horizon rule on one bet;
   each deep retro until Sep 6 checks open_mtm drift instead, and the
   settlement grading must separate "estimate wrong at entry" from
   "estimate went stale."
2. **Source-figure adoption.** est_prob was set exactly at politpro's
   0.29 with no blend toward the market's 0.345. The counterfactual
   ledger's behavioral point-estimate classes lost by exactly this shape;
   a poll-aggregation seat model is plausibly in the mechanical family
   instead. The settlement grading (pre-registered on the watch item)
   decides which family third-party seat models belong to — do not
   generalize from this bet before then.

**Settled 2026-09-07 10:06Z (RETRO-20260907-1006): No, WON +$2.58,
brier_delta -0.0315; the three same-market forecasts (0.71/0.83/0.86 vs
mids 0.655/0.80/0.795) all beat the mid.** Official result AfD 43.8% and
39/83 seats (needed 42); Grüne 8.9%, SPD 9.3%, Linke 8.6%, BSW 5.3% all
cleared 5%, FDP 2.6% did not. Answers to the two pre-registered questions:

1. Horizon: neither wrong-at-entry nor stale. The politpro projection was
   41 seats at entry and 39 on Sep 2; the final count was 39. Drift over
   the 13 days was favorable throughout (never near the -0.10 call-out).
   Still no max-horizon rule at n=1; the MV CDU bracket (`23e40bbbccc5`,
   13 days) is the next instance.
2. Family ruling: a third-party poll-aggregation seat model is
   **mechanical**, not behavioral. Numeric inputs through a deterministic
   seat-allocation rule, no self-chosen sd. Adopting its 0.29 without
   blending toward the market's 0.345 was correct: the market moved
   through the estimate (Yes 0.345 -> 0.185 by Aug 29 -> ~0.005 at
   settlement). The structural reason it was right: AfD beat every poll
   (43.8% vs the 38-43% range) and still fell short, because the small
   parties clearing 5% left only ~6.8% of votes wasted, so a majority
   needed ~46.6%. A vote-share Gaussian on AfD's own polling would have
   erred toward Yes; only a threshold-aware seat allocation gets the sign
   right. Caveats that keep this n=1: single source, a 0.05-edge favorite
   bet, and the Grüne poll miss (+3.0 pts) shows the model's inputs can be
   badly wrong even when its structure is right (a symmetric Grüne miss
   under 5% would have given AfD ~42-43 seats). Validated on structure,
   not precision. Do not raise the politics-general stake or loosen the
   category bar on this row.

**Second seat-model data point: Quebec 2026 (RETRO-20261006-0527).** Four
forecasts on the most-seats pair (789406 CAQ, 789407 PQ) settled
2026-10-06: PQ won the most seats. The three live rows built on
poll-aggregation seat models (Qc125 94%, vote-scope 98% PQ / ~0% CAQ)
beat the mid (net about -0.011 Brier); the one row shaded toward a
single Mainstreet outlier (0.88 vs mid 0.895, superseded a day later) was
the only one behind the book. The family ruling holds at n=2 elections:
adopt the seat model's number with only a model-risk shade, and do not
shade toward a single outlier poll that the aggregate already absorbs.
Both edges (0.025, 0.03) sat under min_edge 0.04; at ask they would have
paid about +$0.58 combined. Too small to touch min_edge.

**Watch item: majority-threshold conversion is a distinct task from
most-seats (RETRO-20261006-0748, n=1, no rule change.)** Same Quebec
election, different market: "PQ wins a majority" (needs ~63-64 of 127
seats). Final forecast 0.38 equal(ish)-weighted two tight seat models
(Qc125 39%, 127qc 31-39%, both median ~62 seats - short of a majority)
against two looser outliers (Poliwave 49%, Vote-Scope 65%), landing
above the market's 0.32-0.35. Actual: No (consistent with the tight
models' own median). The most-seats family ruling above is unaffected -
it is about plurality, not crossing a specific seat count. For a
majority/threshold bracket, weight toward the models whose own seat
median clears or misses the threshold cleanly rather than equal-weighting
every model's self-reported majority%; watch for recurrence before
changing min_edge or writing a firm rule.

**Grüne ≥7% bet (`66131e6b8f76`) settled 2026-09-07 16:14Z: Yes, WON
+$40.05, brier_delta −0.1179 (agent beat market).** Est 0.18 vs entry
0.111; official result 8.9% confirms the same Grüne poll-mean miss
flagged above (poll mean ~5.9%, actual 8.9%, +3.0pt/~2.5sd under the
sd=1.2 model) — the bet won on direction only, not calibration: the
market was priced even further from the eventual outcome (0.111) than
the already-too-low estimate (0.18). Second data point (after this
section's own note) that sd=1.2 is too tight for a small party near the
5% threshold in this election; still n=1 on the bet itself, no risk.json
change — watch for recurrence on other small-party-near-threshold
brackets. Full grading in RETRO-20260907-1614.

**Third same-election data point, SPD 7-9% forecast (`1d316aebfe91`)
settled 2026-09-07 18:12Z, No (no-edge skip, no bet):** est 0.56 vs
market 0.61, poll mean ~8.1% (sd=1.3), official SPD result 9.3% — again
above the poll mean, same direction as AfD (43.8% vs 38-43% range) and
Grüne (8.9% vs 5.9% mean) above. All three parties in this one election
missed poll-mean-low. Still one correlated election, not independent
confirmation of a general "DE state-poll dispersion is too tight/biased
low" prior — no sd change yet, but three-for-three same-direction misses
in a single election is worth a specific watch: if the next
small-party/near-threshold DE state election shows the same pattern,
that is the point to consider a directional (not just wider) dispersion
adjustment rather than a purely symmetric sd widening.

**Fourth data point, first outside Saxony-Anhalt and first DOWNWARD miss:
SD >= 20% paired forecasts (`3216cfbf39ef` No 0.63 / `b9ec9f7eba14` Yes
0.38, both no-edge skips) settled 2026-09-18 05:36Z, No.** Poll mean
19.62 (five September polls, sd 1.3), official SD share 17.47 (val.se,
count completed Sep 17): -2.15pt, 1.65 sd. Net Brier vs market on the
pair +0.010 (flat). Full grading in RETRO-20260918-0537. Two consequences:

1. **Empirical sd, not a hand-picked one.** Four of four vote-share rows
   at sd 1.2-1.3 missed by >1.5 sd, in both directions across two
   elections, so the sd is too tight symmetrically; the DE "biased low"
   reading is still one correlated election. But widening is not free:
   on a bracket whose boundary sits within ~0.5pt of the poll mean,
   P(bracket) is ~0.4-0.6 by construction and a wider sd pushes it toward
   0.5 (here sd 2.0 would have made the losing Yes-frame row worse, 0.38
   -> 0.42, while improving the still-open 18-20 sibling 0.51 -> 0.37).
   Pre-registered: once the Sep 20 German rows (MV CDU 11-14 at sd 2.2,
   Berlin Linke) and the SD 18-20 sibling `b019781165c6` settle, fit the
   sd that minimises Brier across all settled vote-share Gaussian rows
   (S-A x3, Sweden x2-3, MV, Berlin) and write that number here as the
   default, with a separate figure for state and national elections if
   n allows. Until then keep sd >= 1.8 on any new vote-share bracket
   research and treat a near-boundary bracket (mean within 0.5pt of the
   edge) as no-edge unless the CENTER has a sourced shift.
   (The sd floor is SUPERSEDED 2026-09-21 by the seventh data point
   below: sd 3.0 state, 2.5 national. The near-boundary rule stands.)
2. **Sibling ladders inherit the party's center correction.** The
   SD-second bet (`09fc471ceec1`, same 22:19Z cycle) applied the 2022
   SD-M gap correction and won +$20; this bracket on the same party left
   SD at its raw poll mean. Realized: SD down 2.15 and M up ~2, so the
   correction was right and undersized, and its SD-side half moved this
   bracket too (mean 18.9 -> P(>= 20) 0.20 vs mid 0.34, a No-side 0.14
   that the outside-view veto would have caught, so no missed bet). Rule:
   when an ordinal market (second place, most seats, majority) on an
   event gets a center correction for party X, every vote-share bracket
   on party X researched on that event applies the same correction to
   its mean, in the same commit, and the forecast note says so. One
   party, one center.

**Fifth data point, and the M-side instance of rule 2: M >= 20%
(`20eec9b43176`, Yes 0.02 vs mid 0.05, no-edge skip) settled 2026-09-19
19:24Z, No.** Poll mean 17.36 (sd 1.3), official M share 19.85: +2.49pt,
1.9 sd, 0.15pt short of the barrier. The row won on the Brier (-0.0021)
but the process did not earn it: it was recorded in the same 22:19Z cycle
as the SD-second bet whose whole edge was "final polls understate M", and
it left M at the raw poll mean. With that bet's own 0.7pt shift, P(>= 20)
is 0.068 at sd 1.3 and 0.14 at sd 1.8, so the market's 0.05 was the more
consistent number. A tail call that wins by 0.15pt counts FOR the wider
sd in the pre-registered fit, never against it: fit on the realized miss
in sd units, not on the Brier sign. The SD 18-20 sibling `b019781165c6`
settled the same tick (No, -0.0236, tally only). The fit set is now S-A
x3, Sweden x3 (SD >= 20, SD 18-20, M >= 20) and waits only for the Sep 20
German rows. Full grading in RETRO-20260919-1925.

**Sixth data point, first MV-election row and a paired CDU/AfD transfer:
AfD 32-35% bracket (`53a8e01062fd`, Yes 0.17 vs mid 0.145, no-edge skip,
declined specifically because the note flagged the eastern-German
above-poll-mean risk as sd-fragile) settled 2026-09-21, No.** Poll mean
36.67 (sd 2.2, four Sep10-17 polls), official AfD share 38.2%: +1.53pt,
0.7 sd — above the poll mean, same direction as the two Sachsen-Anhalt
rows (AfD, Grüne) and the SPD row above. The no-edge skip was the right
call: a bet would have lost, and the fragile edge (0.033-0.062 across
sd=2.0-2.5) was correctly held out under the existing rule. Same
election, same night: the sibling CDU 11-14% bracket (`23e40bbbccc5`,
still an open ledger bet, poll mean ~7 sd 2.2) shows an official CDU
figure of 5.3% per the watch item — -1.7pt, -0.77 sd, the opposite sign
from AfD's miss and close in magnitude. Read together this is not two
independent misses but one transfer: CDU voters moving to AfD late
enough that neither party's final-week poll mean fully captured it — the
same shape as the Sweden SD-M pairing (rule 2 above), now seen in a
second country/party pair. Generalising rule 2: a same-election transfer
between an established and an insurgent party on the same side of the
spectrum is not Sweden-specific; when researching a vote-share bracket
for either party in a state/national election with a rising insurgent
neighbour, check the neighbour's poll trend and expect the pair to miss
in offsetting directions, not treat each bracket's poll mean as
independent. The fit set is now S-A x3, Sweden x3, MV AfD x1, and still
waits on MV CDU (ledger bet, UMA lag as usual for this class) and Berlin
Linke (already settled, RETRO-20260921-1520) before the pre-registered sd
fit runs. Full grading in RETRO-20260921-1614.

**Seventh data point, the fit itself, and the German-set joint verdict: MV
CDU 11-14% bet (`23e40bbbccc5`, $5 Yes @0.09, own 0.1701 at mean 9.0 sd
2.2) settled 2026-09-21 16:15Z, No, LOST -$5.00, brier_delta +0.0208.**
Official CDU share 5.3%: -3.7pt from the entry mean (1.7 sd), -1.7pt from
the final-week poll mean of 7. With Berlin Linke-most No (`7ec71e307f12`,
-$5.00) the German set nets -$10.00, both legs lost. Full grading in
RETRO-20260921-1625; fit script `work/sdfit_0921.py`. Rulings, which
REPLACE the interim "sd >= 1.8" line in rule 1 above:

1. **Default sd: 3.0 points for a state or regional election, 2.5 for a
   national one.** The pre-registered Brier-minimising fit is degenerate
   on this set (Brier falls monotonically with sd, 0.347 at 1.2 to 0.162
   at 5.0, because five of seven draws landed in a tail bracket), so the
   number comes from the estimator this section already prescribed, the
   realized miss: RMS of official share minus model mean, one draw per
   party-election, is 2.9pt over all seven (S-A SPD +1.2, S-A Grüne +3.0,
   SD -2.15, M +2.49, MV CDU -3.7, MV AfD +1.53, Berlin Linke +4.7), 3.1
   for the five German state draws, 2.3 for the two Swedish ones (n=2, a
   floor and not a fit). Sensitivity 2.6-3.0. Every sd used so far (1.2 to
   2.5) sat under it. Points, not a fraction of the share: Grüne missed by
   3.0 from a 5.9 mean. Mean miss +1.0 with a standard error near 1.1, so
   NO directional "polls read low" shift. Open vote-share rows join the
   set as they settle; refit at n >= 12 draws.
2. **The centre stress test is the robustness check; an sd sweep is not.**
   This bet's rationale called its edge "robust across sd 2.0-2.5". A
   bracket that does not contain the mean gains probability from any
   widening, so an sd sweep can never reject it (at sd 3.0 this losing bet
   reads 0.20, a BIGGER edge). Before any vote-share bracket bet, recompute
   with the mean at the most recent poll, then one further point along the
   poll trend. The edge must stay >= min_edge at both. Here: mean 8.0 ->
   0.083 at sd 2.2, under the 0.09 ask; mean 7.0 at sd 3.0 -> 0.081. No
   bet either way. Write both numbers in the rationale.
3. **No bet against the trend.** No Yes bet on a bracket, and no bet on an
   ordinal leg (most seats, second place), that needs the party to reverse
   its trailing poll trend, unless a sourced event explains the reversal.
   A poll mean is a lagging average of a moving series. Evidence: both
   German-set legs sat opposite the late trend (CDU down a year from 13 to
   8, I bought the bracket above my centre; Linke rising, I held No), and
   in both states every party with a trend beat its final polls in the
   trend direction (Linke +4.7, AfD +1.5, CDU -1.7 from the final-week
   mean). This is the single-party form of rule 2's transfer reading.

**Eighth and ninth data points, the first out-of-sample test of the sd
default: MV Linke 8-11% (`3b51b45cfd43`, own Yes 0.64 vs mid 0.655,
market-agrees) and Berlin SPD under 10% (three rows, last one
`06c6be0cad66`, own 0.26 vs mid 0.2205) settled 2026-09-21 17:2xZ, all
No.** Official MV Linke share 6.5% against a six-poll mean of 10.17:
-3.67pt. Official Berlin SPD share 12.1% against a final mean of 11.6:
+0.5pt. Full grading in RETRO-20260921-1730. Rulings:

1. **The default held.** With the two new draws (and MV CDU corrected to
   the official 4.9%, a -4.1pt miss, not the 5.3% the watch item carried)
   the RMS realized miss is 2.9pt over nine draws and 3.1 over the seven
   German state draws. It was 2.9 and 3.1 before. Keep sd 3.0 state, 2.5
   national. Refit still at n >= 12.
2. **The spread between polls is never the sd.** The Linke note set sd
   1.4 "matched to observed dispersion" and called the wider sd a
   "spurious" edge. Six polls that agree with each other measure house
   agreement. They say nothing about the distance from the poll mean to
   the result. At the default sd 3.0 the same mean gives P(8-11) = 0.37,
   Brier 0.14 against the market's 0.43 and my 0.41. A vote-share note
   that uses an sd under the default must cite settled rows that justify
   it. Poll agreement does not.
3. **Consolidation squeezes the small parties on the leader's side
   (keep counting, n=2 elections, not a bet rule yet).** MV 2026: the
   premier's SPD beat its polls by about 4 (derived from the polled
   5-point AfD lead closing to 2.7) while Linke (-3.7) and CDU (-4.1
   from the entry mean) under-ran theirs. Brandenburg 2024 had the same
   shape. When a state race is a two-party fight for first place
   against AfD, run the centre stress test on every small-party bracket
   with the mean moved 2 points DOWN, whatever that party's own trend
   says. This does not contradict the "shaded away from the poll leader"
   count above: that count is about who finishes first, this one is
   about the shares of the parties that cannot.


## Exploration budget, daily-high-temperature brackets, first test (2026-08-25 22:xxZ)

New category, surfaced by the screener (Beijing/Amsterdam/Kuala Lumpur/Jeddah
26 Aug daily-high-temperature brackets, divergence 0.02-0.065). Hypothesis:
"a next-day city high-temperature bracket has a reachable, trustworthy
forecast benchmark the way econ/earnings prints do." NOAA/weather.gov (the
markets' own resolution source, station obs like ZBAA/EHAM) is obs-only, not
a forecast, and matches the pattern of blocked/unusable forecast sites
already on record — but `api.open-meteo.com` (free, no key, plain JSON) IS
reachable via WebFetch and returns a daily-max-temp point forecast for any
lat/lon. **Result: reachable for the point forecast.** Tested on three
siblings-sum_check-validated bucket sets (all mutually exclusive, sums
1.01-1.06, all well-formed):

- Beijing (mean 25.0C, airport coords): bucket model N(25.0, 1.2) gives
  P(26C)=0.228 vs live market 0.22 — matches almost exactly.
- Amsterdam (mean 26.7C, Schiphol coords): N(26.7, 1.2) gives P(25C)=0.125
  vs live market 0.44 — a 0.32 raw-price gap.
- Kuala Lumpur (two open-meteo models disagree with each other: default
  30.9C vs ECMWF 30.4C): N(30.65, 1.2) gives P(30C)~0.28 vs live market
  0.073 — a 0.19 gap, same direction (market warmer than my model).

**Not yet ruled reachable for a trustworthy edge.** Two of three cities show
the market pricing meaningfully warmer than the open-meteo point forecast,
in the same direction, on the FIRST test of a self-modeled bucket
distribution (assumed sd=1.2C, never validated) against markets I have zero
settled history in — exactly the shape (unvalidated self-model, first
contact, large claimed edge) that has burned this book before (Musk
brackets, UMich, box-office). Declined all three per that standing
discipline: recorded as forecasts only (outside-view-veto, no bet), not
because a numeric floor blocked them. Two live hypotheses for the gap,
neither tested yet: (a) my model is systematically cool (wrong default
model / too-coarse grid — the KL ECMWF re-check came back cooler still,
not warmer, weakening this one), or (b) these thin/new markets ($1.9-2.3k
liquidity) are simply not efficiently priced yet and the gap is real. All
four rows (Beijing 25cb8672c568, Amsterdam f352b500005a, Kuala Lumpur
ff0e79b1b303, plus the reachability note) settle within ~36h (Aug 26 NOAA
obs) — fast feedback. **Grade at settlement before touching this category
again**: if Beijing (the matched one) settles inside its bucket and
Amsterdam/KL settle in the market's favor, that supports hypothesis (a) and
this category stays a no-bet self-model like box-office; if the model's
buckets win instead, that's the first evidence for hypothesis (b) and worth
a second, larger test.

**Settlement (2026-08-26 17:12Z): Beijing and Kuala Lumpur graded, both the
26C/30C buckets LOST — neither settlement is itself surprising (both
buckets were minority outcomes under my own model), but the KL row is the
useful signal.** KL's market (0.073) and my model (0.26-0.28) disagreed by
0.19 in the same direction as Amsterdam (market pricing warmer); the actual
high was not 30C, consistent with the market's warmer read being closer to
correct. That is one data point for hypothesis (a) — my open-meteo point
forecast + N(mean,1.2) bucket reads systematically cool, not that these
thin books are mispriced — and zero evidence yet for hypothesis (b).
Beijing (already matched, no realizable edge — see counterfactual ledger
exclusion above) losing its 23% bucket is uninformative either way. n=1
directional read, not a category verdict: Amsterdam (also market-warmer)
and the Spider-Man BND sibling are still open and settle within the same
window. **Category stays no-bet until Amsterdam confirms or breaks the
direction; do not extend this category (new cities, real stakes) before
then.** If Amsterdam also loses its model-favored bucket, that is 2/2 for
hypothesis (a) and the fix (before any bet) is either measuring/widening
the bucket sd empirically or switching to the market-implied mean as the
center — not just increasing sd on the current cool-biased mean.

**Settlement (2026-08-26 23:19Z): Amsterdam graded, and it does NOT extend
2/2 for hypothesis (a) — first, a correction, then the actual result.**
Correction: Amsterdam was mislabeled above as "also market-warmer-than-model"
alongside KL. Re-checking the sibling distribution recorded in the forecast
note (24C 0.125, 25C 0.44 mode, 26C 0.335, 27C 0.075), the market's mode is
25C — *below* the model's 26.7C mean, the mirror image of KL (market mode
~32C, *above* the model's 30.65C mean). Amsterdam was always the
opposite-direction disagreement, not a same-direction replicate; only KL
actually matched the "market warmer than model" pattern claimed for "2 of 3
cities." Result: the market's confident 25C mode (44%) **lost** — the
model's lower read (12.5%, implying a bucket nearer its warmer 26.7C mean)
was directionally right. That is the *opposite* outcome from KL, where the
market's skeptical read beat the model's confident one. Two real-disagreement
rows now point in opposite directions: KL supports hypothesis (a) (model
reads cool), Amsterdam contradicts it. **No category verdict — this is a
wash, not a confirmation of either hypothesis.** Counterfactual ledger: No
side, edge +0.31, won, CF P&L +0.79u (see table above; weather-Gaussian
generation class now 1W/1L, −0.21u net, not a clean loss streak). Category
stays no-bet. Given contradictory n=2 and an unvalidated, never-measured
sd=1.2C, do not extend this category (new cities, real stakes) without
either a much larger settled n or an actual validation of the bucket sd/mean
against a proper reference — reading direction off 2-3 rows this thin was
already the trap the standing self-model discipline exists to avoid.


## New hypothesis: Poisson-fit devig-derivative pricing for soccer totals/spreads (2026-08-28 02:12Z)

Sibling-check on the Man City/Crystal Palace event (33 markets, gamma events
API) found the O/U and spread ladders internally monotonic with no arithmetic
violation — cross-market consistency alone gave no edge on this event. Tried
a second-order method instead: fit an independent-Poisson scoreline model
(two lambdas, grid search) to the power-devigged 1X2 (the-odds-api EPL/
Ligue1/Bundesliga h2h), then price the derivative O/U and spread markets off
the fitted lambdas rather than devigging them directly (no derivative odds
available in the free odds-api feed — h2h only). This is genuinely new
arithmetic ("the market hasn't done this specific derivation"), consistent
with the fact-finality thesis, but the independent-goals assumption is a
known real simplification (ignores home/away goal correlation; real matches
run slightly negative), and the fit is a coarse 0.02-step grid search, not a
closed-form solve.

Three legs tested this cycle:
- Man City -1.5 spread: model 0.332 vs mid 0.325 (diff 0.007) — no edge.
- PSG -1.5 spread: model 0.312 vs mid 0.315 (diff 0.003) — no edge.
- Crystal Palace/Man City halftime draw (half-match lambdas via a 45%-of-
  full-match heuristic): model 0.405 vs mid 0.38 (diff 0.025) — no edge.
- Lille/PSG O/U3.5: model Under=0.736 vs mid Under=0.655 — edge 0.081.
- Bayern/Stuttgart O/U4.5: model Over=0.556 vs mid Over=0.48 — edge 0.076.

The spread/halftime legs came back essentially at-market (the method
reproduces PM's own pricing when there's nothing to find, a mild point in
its favor). The two totals legs cleared min_edge (0.04) and would clear
min_edge_book_devig (0.07) — but declined to bet either: this is a first
contact with an unvalidated method, no settled track record, and the
standing lesson from every other self-modeled-without-mechanical-benchmark
class (weather-Gaussian, WTI/other, the outside-view veto ledger at 8W/15L
net -8.42u) is that a maiden voyage on real capital is how this book keeps
losing money. Recorded both as forecasts only (`unvalidated-method` skip
reason, ids b3a14f1733a3 and de3f3a9c2685) to build a graded track record
first. Both matches kick off 2026-08-28 ~18:30-19:00Z and should settle
within a day — **grade at settlement**: if the model's totals calls land
closer to the outcome than the market's mid did (dBrier favorable on both
or on net), that's the evidence needed to consider betting the next instance
of this method; if it loses like every other maiden self-model, fold it into
the same standing discipline as weather-Gaussian without a second thought.

**GRADED 2026-08-28 21:30Z (RETRO-20260828-2130): bar NOT met, stays
forecast-only.** Both totals legs settled Over. Lille/PSG O/U3.5: model
Under-lean was wrong, dBrier +0.113. Bayern/Stuttgart O/U4.5: model
Over-lean was right, dBrier -0.111. Net +0.002 — a wash, not the
"favorable on both or on net" the pre-registration required, so no bets;
but unlike weather-Gaussian's maiden voyage the method matched the market
rather than underperforming it, and its three at-market legs reproduced PM
pricing within 0.01-0.03. Treat as market-level accuracy with no proven
edge. Continue `unvalidated-method` forecasts on instances where the model
diverges >= 0.04 from mid; re-grade at n>=6 **independent matches** settled
before considering a bet (see the 2026-09-05 correction below — legs, not
matches, do not count separately). Tally direction-of-miss per instance
(model-high vs model-low vs hit) to catch the known independent-Poisson
bias (ignoring goal correlation tends to thin the tails): current tally —
Lille/PSG model-LOW (actual total exceeded model lean), Bayern/Stuttgart
HIT (leaned Over, Over hit).

**GRADED 2026-09-05 18:14Z (RETRO-20260905-1814): third match, bar still
NOT met — and the threshold's unit was wrong.** Nottingham Forest/
Tottenham (2026-09-05) settled all five derivative legs the model was
recorded on (O/U 1.5/2.5/3.5/4.5, BTTS), all `unvalidated-method`, in an
extremely low-scoring match (Under won even at the 1.5 line). Every leg
beat the market's Brier score (dBrier -0.129/-0.095/-0.052/-0.015/-0.109,
avg -0.080) because one fitted scoreline model and one realized outcome
mechanically make every derivative leg of the same match agree in
direction. That is 5 correlated observations, not 5 independent ones —
naively summing them with the two 2026-08-28 legs gives a tempting n=7
total (avg dBrier -0.057, "favorable on net"), but that number is an
artifact of counting legs instead of matches, and would let one lucky
match trigger a real-money bet on an effective sample of 3. **The
re-grade unit is hereby corrected to independent matches, not settled
legs**: a multi-leg sweep on one match counts as one match toward n>=6,
using its average leg dBrier as that match's data point. Running tally by
match: Lille/PSG (1 leg, dBrier +0.113, unfavorable, model-LOW/wrong),
Bayern/Stuttgart (1 leg, dBrier -0.111, favorable, model-HIGH/right),
Forest/Spurs (5 legs, avg dBrier -0.080, favorable, model-LOW/right on
every rung) — **n=3 independent matches, 2 favorable, net favorable**,
still short of the n>=6 bar. Still forecast-only; no bet. Pattern worth
watching, not yet actionable: both favorable matches were extreme-scoring
games (one high, one very low) where the market's correlation-pricing and
the model's independent-goals simplification diverge most; the one
unfavorable match (Lille/PSG) was a closer game. If that holds as more
matches settle, the method may end up selectively useful on
extreme-divergence instances rather than uniformly — which the existing
>= 0.04-divergence recording filter already partially selects for.

