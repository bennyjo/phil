# Research tier: can a prior from Phil's own record pick better markets?

Written 2026-09-08 by an overnight gnhf run, against the operator's question:
the research slot is the scarce resource, so can the forecast ledger itself say
where research beats the price, and can that be turned into a re-ranking of the
screened pool? Every statistic here comes from `core/screen_value.py`,
`core/screen_replay.py`, `core/counterfactual.py` and `core/replay.py`. The
out-of-sample permutation test is `core/screen_value_check.py`; the other
scratch scripts are under `work/` and gitignored, so this file is where the
tables live.

Nothing in the live cycle changed. `CYCLE.md`, `core/screen.py prepare` and
`core/screen.py collect` are untouched, the divergence ranking is still the
escalation list, and `strategy/screener-prompt.md` stays frozen. The new code
path is dormant and nothing calls it.

## Decision

Keep divergence. Do not switch the escalation list to the prior, and do not use
the prior as a tie-break either, because it cannot break a tie: on the live pool
of 2026-09-08 it takes 17 distinct values over 300 markets and decides 0 of 15
slots outright, with all 15 sitting in one tie group of 75. Three numbers carry
the verdict. First, research is at par with the price it is handed: over 542
settled rows and 394 events the mean `brier_delta` is +0.0080 +/- 0.0091, so
there is little edge to allocate and the tables below are a search for a subset
that has one. Second, the feature that looks best in that search is the one that
fails hardest out of sample: an empirical-Bayes prior on family ranks held-out
rows WORSE than a coin flip, lift +0.0196 at p 0.996 against 4,000 permutations
of each fold's own scores, and the same ordering holds at a top-10% cut. Only
the market-age term leans the right way, at p 0.087, and it moves in exactly one
of four folds. Third, the historical replay's one apparent win is a single fold:
the prior's top 15 holds 23 of the 187 researched rows attributable to a collect
run, those rows read -0.0102 +/- 0.0432 against the divergence
list's +0.0219 +/- 0.0248, and the whole difference lives in fold 1, where the two lists overlap
most (11 rows at -0.0444, against 12 rows at +0.0212 over folds 2 to 5). That is
agreement with divergence being scored, not the prior's own ordering. A
family-level slot allocator was tested on its own and fails too: dropping the
two families the training folds rank worst leaves a held-out lift of +0.0021,
and in one fold of four the training fit named sports moneyline and sports line
as the two worst, which is the reverse of what the full journal says. The family
term changes sign as the window moves. The finding that does survive is not a
ranking at all: research done EARLIER in a market's life is worse, not better
(+0.0425 on the young half against -0.0060 on the old half, n 102 each, z
-2.36), and the watch tier's 50 fires bought 32 forecasts and 4 bets at -0.0167
+/- 0.0399, which is a tier worth keeping but not worth widening. Switch when
the bar below is met, and until then spend the slot as the cycle spends it now.

## What the evidence is, and what is missing from it

The unit is a settled, non-superseded forecast row with a market price at record
time: 542 rows over 530 markets, from `journal/forecasts.jsonl`, record ts
2026-08-09T19:27:28Z to 2026-09-08T12:39:27Z. `brier_delta` is
`(est - won)^2 - (market_prob_at_record - won)^2`, so NEGATIVE means research
beat the price it was handed. Intervals are `screen_replay.mean_se`, the
event-clustered sandwich, and the clustering is anti-conservative on this cut:
376 of the 530 markets sit in a gamma event with another market and 154 cluster
alone. Counterfactual pnl is `core/counterfactual.py` over the declined rows,
and `held` is the walk-forward part, folds 2 to 5 of `core/replay.py`'s cut.

Two features named in the question are not in the tables, and both omissions are
recorded rather than papered over:

- **Liquidity and 24h volume at record time do not exist for most rows.** They
  live only in the 16 local collect runs' batch briefs, which cover 103 of the
  542 rows; `work/screen-replay/gamma-static.jsonl` carries question, description
  and end_date and no liquidity or volume column. Fitting on a fifth of the
  evidence would be worse than not fitting, so the feature is dropped, not
  proxied with a current gamma value.
- **Market age is readable on 204 rows.** The proxy is hours since the market
  first appears in `journal/screener.jsonl`. 239 rows have a first appearance and
  35 of those come back negative, because the screener journal starts 2026-08-25
  and those markets were researched earlier. A negative age is a missing
  observation, not a young market, so it is scored as unbanded.

`strategy/funnel.jsonl` carries `tick_type` on 101 of 258 cycles, starting the
same day the watch tier does, so its absence is absence of a trigger. Joining on
(market_id, UTC day) gives 19 TRIGGERED settled rows against 523 FULL. Question
2 is thin by construction and says so.

The agent's own category labels number 56 distinct strings. The deterministic
title-and-slug mapper in `strategy/screener-value.json` collapses them onto the
nine families with 0.956 agreement (518 of 542) against a hand map of those
labels. Most of the residual is the agent label being loose rather than the
mapper being wrong: nine rows labelled `soccer-moneyline` or `nfl-preseason`
have titles reading `Spread: ...` or `O/U 34.5`, and `news` is a grab bag of
transfers, net-worth brackets and geopolitics.

## Question 1: where research beats the price

Reproduce every table in this section with `python3 core/screen_value.py fit`.

By family. `pnl` is counterfactual, `held` its walk-forward part:

| family | n | events | brier_delta | +/- | z | pnl | held |
|---|---|---|---|---|---|---|---|
| sports moneyline | 173 | 124 | -0.0042 | 0.0095 | -0.86 | -21.15 | +9.81 |
| sports line | 86 | 84 | -0.0105 | 0.0117 | -1.76 | +0.17 | -5.09 |
| econ print | 87 | 45 | +0.0082 | 0.0194 | 0.83 | +78.28 | +52.94 |
| other | 62 | 44 | +0.0229 | 0.0291 | 1.54 | +75.36 | +77.05 |
| politics | 32 | 19 | +0.0061 | 0.0355 | 0.33 | -1.50 | +11.39 |
| weather | 32 | 31 | +0.0558 | 0.0550 | 1.99 | -35.07 | -39.89 |
| ai and tech | 31 | 25 | +0.0804 | 0.0844 | 1.87 | +4.74 | +22.21 |
| crypto | 24 | 17 | -0.0087 | 0.0289 | -0.59 | +72.48 | +3.22 |
| entertainment | 15 | 10 | -0.0273 | 0.0828 | -0.65 | -13.01 | -6.77 |

Entertainment (n 15), crypto (n 24), politics (n 19 events) and weather and
ai-and-tech (n 31 and 32, both with an interval wider than their own mean) are
too thin to read on their own. No family is convincingly negative. The best
cell, sports line at -0.0105, sits inside its own interval.

By market price band at record, on the side research actually took:

| price band | n | events | brier_delta | +/- | z | pnl | held |
|---|---|---|---|---|---|---|---|
| under 0.05 | 19 | 12 | +0.0025 | 0.0068 | 0.72 | +94.17 | +99.17 |
| 0.05-0.20 | 109 | 87 | -0.0029 | 0.0169 | -0.33 | +63.61 | +91.42 |
| 0.20-0.40 | 120 | 97 | +0.0239 | 0.0200 | 2.34 | -53.67 | -45.56 |
| 0.40-0.60 | 132 | 127 | +0.0006 | 0.0177 | 0.07 | +31.25 | +22.88 |
| 0.60-0.80 | 89 | 88 | +0.0032 | 0.0147 | 0.42 | -9.97 | +6.01 |
| 0.80-0.95 | 64 | 63 | +0.0218 | 0.0445 | 0.96 | +44.90 | +43.20 |
| 0.95 and over | 9 | 9 | +0.0008 | 0.0007 | 2.41 | -10.00 | -5.00 |

The record has a longshot tilt: 248 of 542 rows took a side priced under 0.40
against 162 above 0.60. The two cells past |z| 2 are both losses and both
fragile. The 0.95-and-over cell holds 9 rows and its z comes from an interval of
0.0007, which is nine near-certain markets, not a finding.

By hours to resolution at record:

| hours band | n | events | brier_delta | +/- | z | pnl | held |
|---|---|---|---|---|---|---|---|
| under 6h | 94 | 69 | +0.0032 | 0.0135 | 0.46 | +19.84 | +42.29 |
| 6h-24h | 174 | 149 | +0.0128 | 0.0169 | 1.49 | +4.74 | +17.11 |
| 24h-72h | 108 | 58 | +0.0050 | 0.0210 | 0.47 | +173.59 | +161.86 |
| 72h-168h | 80 | 56 | -0.0058 | 0.0258 | -0.44 | -42.24 | -60.97 |
| 168h and over | 86 | 75 | +0.0204 | 0.0253 | 1.58 | +4.36 | +44.16 |

Nothing here is readable. Every cell sits inside its own interval.

By market age at record, on the 204 rows the proxy reaches:

| age band | n | events | brier_delta | +/- | z | pnl | held |
|---|---|---|---|---|---|---|---|
| under 6h | 80 | 76 | +0.0445 | 0.0319 | 2.73 | +12.00 | -65.95 |
| 6h-24h | 43 | 40 | +0.0394 | 0.0551 | 1.40 | +43.39 | +54.36 |
| 24h-72h | 52 | 45 | -0.0284 | 0.0412 | -1.35 | +27.49 | -19.48 |
| 72h and over | 29 | 18 | -0.0015 | 0.0119 | -0.24 | +24.79 | +47.10 |
| (no reading) | 338 | 229 | +0.0019 | 0.0078 | 0.47 | +52.63 | +58.28 |

This is the strongest cell in question 1 and it points the wrong way for the
objective: research on markets under 6 hours old is worse against the price, not
better. Question 2 shows most of it is composition rather than timing.

By cycle type:

| tick | n | events | brier_delta | +/- | z | pnl | held |
|---|---|---|---|---|---|---|---|
| FULL | 523 | 376 | +0.0088 | 0.0093 | 1.86 | +162.05 | +182.31 |
| TRIGGERED | 19 | 19 | -0.0138 | 0.0495 | -0.55 | -1.76 | -1.76 |

The title-shape classes in `strategy/screener-filters.json` are not a separate
table here. They are what the `sports line` family is: the filters fire on
spread, over/under, handicap and half-time shapes, and those rows carry the one
family with a negative mean. `journal/screener-rank-decision.md` already
measured that regex against the subagent's own behavior.

## Question 2: does speed pay?

Reproduce with `work/value/q2.py` (gitignored; the tables are here).

TRIGGERED against FULL research, the same rows as question 1:

| arm | n | events | brier_delta | +/- |
|---|---|---|---|---|
| TRIGGERED | 19 | 19 | -0.0138 | 0.0495 |
| FULL | 523 | 376 | +0.0088 | 0.0093 |
| difference | | | -0.0226 | 0.0491 (z -0.90) |

Median splits, the continuous read of the same question:

| split | median | below | n | above | n | difference | z |
|---|---|---|---|---|---|---|---|
| hours to resolution | 25.6h | +0.0095 | 271 | +0.0066 | 271 | -0.0029 | -0.31 |
| market age | 11.8h | +0.0425 | 102 | -0.0060 | 102 | -0.0485 | -2.36 |

Research further from resolution does not beat the price by more. Research
earlier in a market's life is worse, and the sign is stable enough to state: the
young half of the age-readable rows holds 25 weather and 19 ai-and-tech rows,
the two worst families, against 7 and 9 in the old half, while the old half
holds 32 sports moneyline and 19 econ print. So the age effect is largely which
markets appear young in the screener journal, not timing itself. Any age term in
a prior is partly re-reading the family term.

Watch tier yield, from `journal/watch-triggers.jsonl`:

| stage | count |
|---|---|
| trigger fires | 50 |
| distinct markets (38 new_market, 7 price_move, 5 calendar) | 43 |
| markets that produced a forecast | 32 |
| markets that produced a bet | 4 |
| settled forecast rows on fired markets | 25 |

Those 25 rows read -0.0167 +/- 0.0399 against +0.0092 on the 517 never-fired
rows, a difference of -0.0260 at z -1.27, with counterfactual pnl -6.76 on the
fired markets. The tier converts fires into forecasts well and its rows lean the
right way, but 25 rows cannot carry a decision.

State the selection biases plainly. Only escalated or watched markets were ever
researched, so nothing here says what research would have found on a market the
screen never sent it. The categories were chosen by the agent, so a family's
cell reflects both the family and the agent's appetite for it. And TRIGGERED
attribution rests on a (market_id, UTC day) join over the 101 cycles that carry
`tick_type`.

## Question 3: the prior, and why it does not survive its own test

The prior is an empirical-Bayes shrinkage. Each level of each feature is pulled
toward the global mean by `offset = B * (level mean - global)`, with `B = tau2 /
(tau2 + se^2)`, `se` the event-clustered standard error above, and `tau2` the
between-level variance left after subtracting sampling variance (method of
moments, floored at zero). A market's expected edge is the global mean plus the
offset of every feature it can read.

Empirical Bayes answered the feature-selection question by itself. On the full
journal `tau2` is exactly 0 for price band and for hours to resolution, so those
two features produce no ordering at all no matter how their cells look. Price
band 0.20-0.40 reaching |z| 2.34 in question 1 survives no shrinkage. What
remains is family (tau2 4.91e-04) and market age (tau2 5.49e-04):

| feature | level | n | events | raw | +/- | B | offset |
|---|---|---|---|---|---|---|---|
| family | sports line | 86 | 84 | -0.0105 | 0.0117 | 0.932 | -0.01729 |
| family | sports moneyline | 173 | 124 | -0.0042 | 0.0095 | 0.954 | -0.01165 |
| family | crypto | 24 | 17 | -0.0087 | 0.0289 | 0.693 | -0.01161 |
| family | entertainment | 15 | 10 | -0.0273 | 0.0828 | 0.216 | -0.00763 |
| family | politics | 32 | 19 | +0.0061 | 0.0355 | 0.599 | -0.00119 |
| family | econ print | 87 | 45 | +0.0082 | 0.0194 | 0.834 | +0.00012 |
| family | other | 62 | 44 | +0.0229 | 0.0291 | 0.690 | +0.01025 |
| family | ai and tech | 31 | 25 | +0.0804 | 0.0844 | 0.209 | +0.01514 |
| family | weather | 32 | 31 | +0.0558 | 0.0550 | 0.384 | +0.01834 |
| age | 24h-72h | 52 | 45 | -0.0284 | 0.0412 | 0.554 | -0.02021 |
| age | 72h and over | 29 | 18 | -0.0015 | 0.0119 | 0.937 | -0.00893 |
| age | 6h-24h | 43 | 40 | +0.0394 | 0.0551 | 0.410 | +0.01285 |
| age | under 6h | 80 | 76 | +0.0445 | 0.0319 | 0.674 | +0.02455 |

### The out-of-sample test, with its null proved by simulation

Five contiguous walk-forward folds. For each held-out fold the prior is fitted
only on the earlier folds, then used to order that fold's rows. The statistic is
the lift of the top quartile: mean `brier_delta` of the rows the prior ranks
best, minus the fold mean, so negative is good. Ties are averaged over with
`screen_replay.top_k_weights` rather than broken. The null is 4,000 permutations
of each fold's own scores, which keeps both marginal distributions and destroys
only the pairing.

| model | lift (top 25%) | p(null) | lift (top 10%) | p(null) | per-fold lift (top 25%) |
|---|---|---|---|---|---|
| null (constant) | -0.0000 | - | +0.0000 | - | +0.0000 -0.0000 +0.0000 -0.0000 |
| family | +0.0196 | 0.996 | +0.0252 | 0.998 | +0.0202 -0.0041 +0.0000 +0.0638 |
| age | -0.0083 | 0.087 | -0.0110 | 0.123 | +0.0000 -0.0000 +0.0000 -0.0343 |
| price | +0.0066 | 0.787 | +0.0131 | 0.876 | +0.0000 +0.0145 -0.0340 +0.0473 |
| hours | -0.0000 | 1.000 | +0.0000 | 1.000 | +0.0000 -0.0000 +0.0000 -0.0000 |
| family + age | +0.0050 | 0.749 | +0.0071 | 0.733 | +0.0202 -0.0041 +0.0000 +0.0038 |
| all four | +0.0010 | 0.539 | +0.0054 | 0.650 | +0.0202 +0.0026 -0.0340 +0.0159 |

Held-out fold sizes and means: n 109 at +0.0098, n 109 at -0.0024, n 109 at
+0.0101, n 106 at +0.0155.

Nothing beats the null, and the family prior is worse than random. Age is the
only hint, and its lift comes from one fold, because its `tau2` shrinks to zero
in the three earlier training windows.

### The family allocator, tested on its own

A reader might keep divergence as the sort key and still use the family table to
cap or drop slots. That is a different rule from a ranking, so it gets its own
test. Fit the prior on the earlier folds, drop the two families with the largest
positive offset, and read the mean `brier_delta` of what is left in the held-out
fold. The null draws the same number of rows out of that fold at random, 4,000
times.

| fold | n | dropped | kept mean | fold mean | lift | p(null) | families dropped |
|---|---|---|---|---|---|---|---|
| 1 | 109 | 28 | +0.0075 | +0.0098 | -0.0023 | 0.293 | other, politics |
| 2 | 109 | 22 | -0.0017 | -0.0024 | +0.0008 | 0.617 | politics, other |
| 3 | 109 | 47 | +0.0324 | +0.0101 | +0.0223 | 0.984 | sports moneyline, sports line |
| 4 | 106 | 24 | +0.0080 | +0.0155 | -0.0075 | 0.189 | ai and tech, other |

Row-weighted lift over the held-out folds: +0.0021. Fold 3 is the finding. On
the first 218 rows the family offsets rank sports moneyline and sports line as
the two WORST families; on the full journal they are the two best. A term that
flips sign as the window moves cannot allocate a scarce slot.

One methodological note, because it nearly produced a false positive. With a
stable sort a CONSTANT score scored a top-quartile lift of -0.0069, the size of
every real lift in the table, because it selects the earliest rows of each fold
and `brier_delta` drifts within a fold. `top_k_weights` removes that, and the
constant model then reads exactly 0.0000 with null sd 0.0000, which is the
estimator validating itself. Any future selection statistic in this repo must
average over ties rather than break them.

### The replay against history

For each of the 111 collect runs in `journal/screener.jsonl`, the run's screened
pool is ranked by a prior fitted only on rows that had SETTLED before that run's
ts, and its top 15 is compared with the divergence top 15 the cycle actually
saw. The label joins on market_id within 2 hours of the run ts, which is where
187 of the 203 rows with any preceding run in the log fall; the median gap is 5
minutes. That gives 187 distinct researched rows over 180 markets and 78 of the
runs, counted 203 times in the per-run table below because 16 rows fall inside
two runs' windows. 86 of the 180 markets have a negative settled `brier_delta`,
96 with the same double count.

Say the selection bias out loud: the label exists only on markets that were
researched, and those were chosen by the divergence list itself. The divergence
arm is therefore scored on the markets it picked, and the prior arm only on the
subset it happens to share. The `beat` columns below are not a fair race, and
the `shared` column is why.

| fold | runs | researched markets | beat markets | prior escalates | divergence escalates | prior pnl | div pnl | mean prior, prior list | mean prior, div list | shared slots |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 23 | 41 | 25 | 7 | 19 | +44.36 | +213.02 | -0.00966 | +0.00003 | 5.52 |
| 2 | 23 | 45 | 20 | 3 | 16 | +6.41 | -31.35 | -0.02311 | -0.00201 | 0.96 |
| 3 | 23 | 41 | 19 | 1 | 19 | -1.67 | -40.69 | -0.02222 | +0.00469 | 0.74 |
| 4 | 23 | 66 | 28 | 2 | 17 | -7.94 | +17.79 | -0.02562 | +0.00788 | 1.26 |
| 5 | 19 | 10 | 4 | 0 | 4 | -5.00 | -15.45 | -0.02799 | +0.00838 | 2.11 |
| all | 111 | 203 | 96 | 13 | 75 | +36.16 | +143.32 | -0.02149 | +0.00363 | 2.12 |

Counts in that table are per run, so the `all` row carries the double count: 203
row-attributions over 187 distinct rows, and 96 beat-attributions over 86
distinct markets.

Normalized, which is the only comparison the overlap supports. Rows are
attributions again, with the distinct count beside them:

| list | rows held | distinct | markets | beat markets | beat rate | brier_delta | +/- | pnl | pnl per row |
|---|---|---|---|---|---|---|---|---|---|
| prior top 15 | 23 | 23 | 23 | 13 | 0.565 | -0.0102 | 0.0432 | +36.16 | +1.57 |
| divergence top 15 | 166 | 164 | 157 | 75 | 0.478 | +0.0219 | 0.0248 | +143.32 | +0.86 |

Difference, prior minus divergence, -0.0321 +/- 0.0440, z -1.43. That is the
prior's best-looking number in this whole memo, and it does not survive being
split by fold:

| fold | prior rows | brier_delta | div rows | brier_delta | shared slots per list |
|---|---|---|---|---|---|
| 1 | 11 | -0.0444 | 33 | -0.0264 | 5.52 |
| 2 | 4 | +0.0320 | 35 | +0.0371 | 0.96 |
| 3 | 2 | -0.0013 | 40 | +0.0382 | 0.74 |
| 4 | 5 | -0.0258 | 48 | +0.0195 | 1.26 |
| 5 | 1 | +0.2573 | 10 | +0.0746 | 2.11 |

Fold 1 holds 11 of the 23 rows at -0.0444; folds 2 to 5 hold 12 rows at +0.0212,
which is the divergence arm's own number. Fold 1 is also the fold where the two
lists agree most, at 5.52 shared slots against 0.74 to 2.11 afterwards. So the
apparent edge is concentrated in the period when the prior's list was closest to
the divergence list, which is agreement being scored rather than the prior's
ordering. The 23 rows are 11 sports moneyline, 4 entertainment, 3 weather, 3
crypto, 1 sports line and 1 ai-and-tech.

Family composition of the two lists, mean slots per list of 15:

| family | prior | divergence |
|---|---|---|
| sports moneyline | 7.57 | 4.04 |
| sports line | 3.99 | 3.14 |
| weather | 1.63 | 2.39 |
| other | 0.11 | 2.07 |
| entertainment | 1.20 | 0.51 |
| ai and tech | 0.05 | 1.00 |
| crypto | 0.17 | 0.77 |
| politics | 0.02 | 0.86 |
| econ print | 0.26 | 0.21 |

The prior's list is 77% sports, by construction: sports line and sports
moneyline are the two families with a negative offset and they are also the bulk
of the pool. Switching would hand the researcher a sports book, and would cut
econ print and politics, the two families where the counterfactual pnl is
positive and held up out of sample (+52.94 and +11.39).

## Question 4: the dormant path

`core/screen_value.py` has two subcommands and nothing calls it. It is not wired
into `CYCLE.md`, `prepare` or `collect`, and it writes no journal, no quota and
no marker.

- `fit` prints the tables in questions 1 and 3 from the current journal, with n,
  events, event-clustered intervals, counterfactual pnl and its held-out split.
  `--json` prints the same report as one object, `--folds` moves the walk-forward
  cut.
- `rank --run <collect ts>` re-ranks that run's screened pool by a prior fitted
  only on rows that settled before the run's ts, and prints the top 15 to stdout
  in the same JSON-lines shape `collect` prints, with `value_prior` and
  `value_features` added. The header goes to stderr and names the fit window, the
  features with no usable spread, the rows the prior could not score, the family
  mix, the overlap with the divergence top 15, and how many slots the prior
  decided outright. `--run` takes an exact ts or a compact prefix and defaults to
  the latest run. `--work-root` says where the batch briefs live, for `end_date`,
  and defaults to this repo's `reports/screener-work`.

`strategy/screener-value.json` is the one agent-editable file: the ordered,
first-match-wins family mapper (10 title and slug regexes onto the nine fixed
families) and the price, hours and age band edges. Bounds are code-enforced, the
same way `core/screen.py` loads `screener-strata.json`: an unknown family name,
a regex that does not compile, a bad `on` field, non-increasing or out-of-range
band edges, malformed JSON and a missing file each print a loud message on
stderr and fall back to the built-in defaults, and ranking continues.

Dry run against the latest local collect run, 2026-09-08T21:30:47Z, pool 300:

```
prior fitted on 542 rows / 394 events that settled before this run
no usable spread, contributing nothing: price_band, hours_band
rows the prior could not read, of 300: age_band 27
mean prior of the list -0.02382; families {'sports moneyline': 15}
markets also in the divergence top 15: 6
the prior takes 17 distinct values on this pool and decided 0 of 15 slots
outright; the other 15 sit in one tie group of 75 and were ordered by divergence
```

15 valid JSON lines on stdout, and the md5 of every `journal/*.jsonl` and
`strategy/*.jsonl` is unchanged across `fit` and `rank`. On the earliest run,
2026-08-25T00:22:51Z, the prior decides 9 of 15 with a tie group of 84. That
coarseness is a property of the prior, not a bug: with two live features it can
take at most families times age bands values, so the 15/16 cut lands inside a
tie group nearly always and divergence, the incumbent, orders the rest.

`python3 core/validate.py`, `ruff check --select E9,F core strategy` and a full
`ruff check core/screen_value.py` all pass.

`core/screen_value.py` is operator-owned. Per
`journal/screener-rank-decision.md`'s landing note, a new file under `core/`
survives `loop.sh`'s protected-boundary revert because `git diff HEAD` cannot
see an untracked file, so the live loop can sweep it into an agent commit and
the CI boundary guard then fails that push. Commit it with the `operator:`
prefix.

## The bar that would change this

Pre-registered, in the shape of the switch bar in
`journal/screener-rank-decision.md`. Switch the escalation list to the prior
when all three hold:

1. **Evidence.** `python3 core/screen_value.py fit` reports at least 1,000
   settled rows and 700 events, roughly double today's 542 and 394.
2. **Ordering.** The family-only walk-forward lift is NEGATIVE at p <= 0.05
   against the permutation null described above (five contiguous folds, top
   quartile of each held-out fold, ties averaged with
   `screen_replay.top_k_weights`, 4,000 permutations of that fold's own scores),
   and it moves the same way in at least 3 of the 4 held-out folds.
3. **Resolution.** `python3 core/screen_value.py rank` on a live pool reports at
   least 8 of 15 slots decided by the prior outright.

If 1 and 2 hold but 3 does not, the prior is real but too coarse to be a
ranking. Re-run the drop-the-worst-families test above first, and use the prior
as a family-level cap on the escalation list rather than as the sort key only if
that test now clears p <= 0.05 as well. If 1 and 3 hold but 2 does not, do
nothing: a prior that resolves the list but cannot beat a permutation of itself
is spending the scarce slot on noise with more confidence than before.

## How to switch it on

1. Read this file, `journal/screener-rank-decision.md` and
   `journal/operator-notes.md` for 2026-09-04.
2. Re-check the bar on the current journal:

   ```
   python3 core/screen_value.py fit
   python3 core/screen_value.py rank --work-root reports/screener-work
   ```

   `fit` gives condition 1 and the `tau2` inputs; `rank`'s last header line
   gives condition 3. Condition 2 is `python3 core/screen_value_check.py`, the
   permutation test described above, kept in core so the bar is re-checked with
   the statistic that set it.
3. To take the prior as the escalation list, change the sort in
   `core/screen.py collect` (the `ranked = sorted(...)` on line 889) from
   `r["divergence"]` to the prior score, importing `fit_prior`,
   `screened_features` and `prior_score` from `core/screen_value.py`, and keep
   divergence as the tie-break exactly as `rank_report` does.
4. To take it as a family cap instead, leave `collect` alone and cap slots per
   family from `strategy/screener-value.json`'s mapper after the divergence sort.
5. Either way, record the switch in `journal/operator-notes.md`, because the
   escalation list's composition changes and `journal/screener.jsonl` carries no
   field that would explain the break.
