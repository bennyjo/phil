# Screening tier: can a formula replace the Haiku screen?

Written 2026-09-04 by an overnight gnhf run, against the question the operator
left in `journal/operator-notes.md` (2026-09-04): the Haiku screening tier adds
nothing over the mid it is handed, so does a no-model ranking do the same job
for free? Every statistic here comes from `core/screen_replay.py`. The scripts
are under `work/` (gitignored), so this file is where the tables live.

Nothing in the live cycle changed. `CYCLE.md`, `core/screen.py prepare` and
`core/screen.py collect` are untouched, the Haiku tier is still the screen, and
`strategy/screener-prompt.md` stays frozen as the object under measurement.

## Decision

Keep the Haiku tier, and take only the formula's filters. The evidence does not
support the swap and does not support leaving the list alone either. Neither
ranking reads anything the price does not already say: on the pooled live cut
the divergence ranking buys no surprise at all over a random 15 of a run (lift
-0.008 to +0.011, every |z| under 1.8), and the uncertainty formula's large
apparent win (+0.13 to +0.16, z 2.5 to 4.4) is entirely the mids null, whose
excess is +0.006 to +0.011 at z 0.13 to 0.17. What separates them is what each
list contains. A 2p(1-p) ranking on the 2026-09-03 scan escalates 15 markets
priced between 0.475 and 0.525, fourteen of them sports or esports tossups, and
it loses precision@15 at z -2.6 to -5.5 because a nearest-0.5 ranking can never escalate
the longshot that comes in, which is where the biggest realized upsets are. The
one rule in `screener-prompt.md` with a measurable footprint is the hard rule on
line-constructed markets, and it is a title regex: it holds bookmaker shapes to
3.4 of 15 slots against 6.8 to 7.8 under the bare formula, and the regex
reproduces the subagent's own behavior on 88% to 91% of matched rows against a
0.561 baseline. So run the filters in `strategy/screener-filters.json` as a
pre-filter and keep the model ranking the survivors, which also removes most of
the tier's own worst habit: 199 lazy 0.50/0.50 answers reached the divergence top
15 across 75 collect runs, 2.65 slots per list, and 74% of them are the filtered
shapes, so the pre-filter cuts that to 0.84 slots. The number that would change this is the research
label, and it is not close to readable: 178 of 9,407 screened markets ever
reached research, 140 settled, 5 produced a bet, and every Brier cell holds 8 to
49 rows with its excess inside its own standard error. Switch the ranking when a
divergence arm and an uncertainty arm each carry 30 or more settled forecasts
and the uncertainty arm's Brier against the market is lower.

## Where the escalation cut is taken

`core/screen.py` line 722 sorts every row of a collect run together and prints
the top 15 overall. A run is about 15 batches and about 285 gradeable rows.
`screen_replay.escalation` ranks per batch of 20 instead. Both are honest reads,
but the pooled one is the list the cycle researches from, and the two disagree.
Rows of one collect run share the `ts` that collect stamps on them, so re-keying
`batch_id` to `ts` runs the same escalation code over the live cut. Tables that
say "pooled" use that re-keying.

## Question 1: surprise

Ranking by uncertainty is ranking by `item["surprise_mid_null"]`, because
`mid_null_surprise` on a binary market is 2p(1-p). The arm swap is one field.
The mids null, the tie-averaged weights, and the event-clustered standard errors
are the same code in both arms.

Per batch of 20, which is `screen_replay`'s own cut:

| prompt_rev | batches | surprise lift, divergence | surprise lift, uncertainty | mids null | excess (z) |
|---|---|---|---|---|---|
| f055b035 | 523 | +0.0059 | +0.0598 | +0.0559 | +0.0038 (0.89) |
| 341771ea | 186 | +0.0064 | +0.0522 | +0.0499 | +0.0024 (0.55) |
| ce4bfcd2 | 81 | -0.0010 | +0.0461 | +0.0412 | +0.0048 (0.92) |
| f7ddad12 | 64 | +0.0008 | +0.0311 | +0.0321 | -0.0010 (-0.21) |

Pooled live cut, top 15 of a whole run. Run counts differ from the tables that
follow because a run enters here only through its resolved rows:

| prompt_rev | runs | surprise lift, divergence (z) | surprise lift, uncertainty (z) | precision lift, divergence (z) | precision lift, uncertainty (z) |
|---|---|---|---|---|---|
| f055b035 | 36 | -0.0080 (-0.29) | +0.1635 (4.36) | -0.0072 (-0.61) | -0.0517 (-5.52) |
| 341771ea | 13 | +0.0107 (0.24) | +0.1523 (3.06) | +0.0279 (0.97) | -0.0534 (-3.40) |
| f7ddad12 | 11 | -0.0225 (-0.58) | +0.1306 (2.75) | -0.0214 (-1.04) | -0.0787 (-3.84) |
| ce4bfcd2 | 7 | -0.0607 (-1.79) | +0.1649 (2.55) | -0.0379 (-1.69) | -0.0590 (-2.64) |

The two lists barely overlap on the cut that matters. Tie-averaged overlap of
the two top 15s is 0.010 to 0.042 pooled, against 0.788 to 0.869 per batch. The
comfortable per-batch figure is an artifact: at a batch of 20 the top-15 cut
falls inside the divergence-0.0 tie group, so both rankings are forced to agree
on three quarters of the slots. A switch replaces 14 or 15 of the 15 markets on
the morning list.

Both readings, stated. On surprise lift the formula wins by an order of
magnitude and the model ranking buys nothing. On precision@15 the formula loses,
and the reason is structural rather than noise: its top 15 has mean surprise
0.499, the arithmetic maximum, because it is 15 markets priced at 0.50. A market
priced 0.02 that wins scores surprise 0.98, and a nearest-0.5 ranking can never
reach one. Neither ranking's excess over the mids null is distinguishable from
zero on any revision or either cut.

## Question 2: the label that matters

Only escalated markets were ever researched, and only a few of each list of 15
were worked at all. Nothing here says what research would have found on a market
the screen never sent it. The unit is an escalation event, meaning a screener row
in the hard top 15 of its batch by divergence: 16,530 events over 7,717 markets
and 3,667 clusters. Labels join to `journal/forecasts.jsonl` on `market_id`
within 2 hours of the screening `ts`.

Reached research:

| bucket | n | rate | se |
|---|---|---|---|
| divergence 0 to 0.05 | 15,668 | 0.0033 | 0.0005 |
| divergence 0.05 to 0.10 | 408 | 0.0931 | 0.0165 |
| divergence 0.10 to 0.20 | 222 | 0.1532 | 0.0247 |
| divergence 0.20 and over | 232 | 0.1638 | 0.0256 |
| uncertainty 0 to 0.20 | 3,445 | 0.0084 | 0.0017 |
| uncertainty 0.20 to 0.35 | 3,349 | 0.0146 | 0.0023 |
| uncertainty 0.35 to 0.45 | 3,560 | 0.0096 | 0.0019 |
| uncertainty 0.45 and over | 6,176 | 0.0079 | 0.0012 |
| confidence high | 163 | 0.0491 | 0.0179 |
| confidence medium | 2,524 | 0.0218 | 0.0033 |
| confidence low | 13,842 | 0.0071 | 0.0010 |

This table is not evidence about the predictors. Divergence is the sort key of
the list the researcher works down, so its 50x gradient is mechanical.
Confidence inherits the same confound, because mean divergence is 0.0755 on
`high` rows against 0.0089 on `low` ones. Uncertainty is flat because it was
never the selection variable.

Brier against the market on settled rows. `beat` is
`brier(est_prob) - brier(market_prob_at_record)`, so positive means research lost
to the price it was handed. `null` is `(est - mid)^2`, the toll for disagreeing
at all, and `excess` is `beat - null`:

| bucket | n | beat | se | null | excess |
|---|---|---|---|---|---|
| divergence 0 to 0.05 | 49 | +0.0012 | 0.0088 | 0.0105 | -0.0093 |
| divergence 0.05 to 0.10 | 32 | +0.0476 | 0.0252 | 0.0187 | +0.0289 |
| divergence 0.10 to 0.20 | 29 | +0.0175 | 0.0444 | 0.0521 | -0.0346 |
| divergence 0.20 and over | 30 | +0.1005 | 0.0460 | 0.0541 | +0.0464 |
| uncertainty 0 to 0.20 | 26 | +0.0160 | 0.0066 | 0.0104 | +0.0056 |
| uncertainty 0.20 to 0.35 | 39 | +0.0002 | 0.0243 | 0.0357 | -0.0355 |
| uncertainty 0.35 to 0.45 | 31 | +0.0824 | 0.0448 | 0.0354 | +0.0470 |
| uncertainty 0.45 and over | 44 | +0.0484 | 0.0328 | 0.0337 | +0.0147 |
| confidence high | 8 | +0.0377 | 0.0608 | 0.0435 | -0.0057 |
| confidence medium | 44 | +0.0468 | 0.0327 | 0.0423 | +0.0045 |
| confidence low | 88 | +0.0312 | 0.0179 | 0.0231 | +0.0081 |

Every cell holds 8 to 49 rows and every excess sits inside its own standard
error, so the three predictors cannot be ranked against each other. The one thing
the column does say, in all twelve cells, is that research's mean Brier is worse
than the mid it was handed, and that most of the gap is the disagreement toll
rather than direction.

A bet was placed on 5 of 16,530 escalation events, and 8 bets exist in the whole
journal. Every cell holds 0, 1, 2, or 4 bets. Do not quote a bet rate from this
data.

## Question 3: what the prompt does that a formula does not

The title regex for the shapes the hard rule names covers `spread`, `(-N.5)` and
`(+N.5)`, `O/U`, `over/under`, `exact score`, `halftime` and `1st half`, and
`handicap`. The rule records that the post-fix spread-shape share of rows with
divergence at or above 0.10 fell from 63% to 22%. The regex reads 0.651 on
341771ea, before the rule, and 0.222 on f7ddad12, after it, which is the same
pair of numbers.

Footprint of each measurable rule on the pooled live cut:

| rule | prompt_rev | runs | matched rows | pool share | share of divergence top 15 | share of uncertainty top 15 |
|---|---|---|---|---|---|---|
| line-constructed shape | f055b035 | 36 | 4,303 | 0.404 | 0.265 | 0.406 |
| line-constructed shape | f7ddad12 | 19 | 1,992 | 0.350 | 0.211 | 0.467 |
| line-constructed shape | 341771ea | 13 | 1,587 | 0.407 | 0.651 | 0.374 |
| line-constructed shape | ce4bfcd2 | 7 | 747 | 0.359 | 0.152 | 0.324 |
| lazy 0.50/0.50 answer | f055b035 | 36 | 312 | 0.029 | 0.070 | 0.417 |
| lazy 0.50/0.50 answer | f7ddad12 | 19 | 138 | 0.024 | 0.196 | 0.239 |
| lazy 0.50/0.50 answer | 341771ea | 13 | 269 | 0.069 | 0.462 | 0.492 |
| lazy 0.50/0.50 answer | ce4bfcd2 | 7 | 51 | 0.025 | 0.143 | 0.314 |
| mids exactly 0.500 | f055b035 | 36 | 68 | 0.006 | 0.009 | 0.126 |
| mids exactly 0.500 | f7ddad12 | 19 | 31 | 0.005 | 0.007 | 0.109 |
| crypto up or down | f055b035 | 36 | 172 | 0.016 | 0.022 | 0.004 |
| crypto up or down | f7ddad12 | 19 | 95 | 0.017 | 0.007 | 0.007 |

Mids that miss 1.0 by more than 2% appear on 1 row in 22,333, so the overround
tell in the "thin or exotic" bullet has no footprint on Polymarket mids. Drop it.

Confidence does no work at all. `core/screen.py` sorts on divergence only, so the
instruction to output confidence `low` has zero mechanical effect on the
escalation list. Only the paired instruction to output divergence 0.0 moves
anything.

A lazy 0.50/0.50 answer scores divergence `|0.5 - mid|`, so it manufactures the
largest gaps on the markets the price is most sure about:

| lazy rows | n | mid within 0.05 of 0.50 | mid 0.20 or more from 0.50 | mean divergence |
|---|---|---|---|---|
| all in the pool | 770 | 0.740 | 0.114 | 0.0566 |
| in the divergence top 15 | 199 | 0.111 | 0.442 | 0.1876 |

The formula cannot produce this failure, because it never reads a probability.
The pre-filter removes most of it from the model tier as well: 74.4% of the 199
lazy rows in a divergence top 15 are filter-matched shapes, so running the
filters first drops the lazy load from 2.65 to 0.84 slots per list.

An exact 0.500 mid is a placeholder tell, not an even contest:

| row group | markets | resolved | rate |
|---|---|---|---|
| all screened | 9,514 | 7,972 | 0.838 |
| mids exactly 0.500 | 97 | 40 | 0.412 |
| mids within 0.02 of 0.500 | 783 | 551 | 0.704 |
| line-constructed titles | 4,800 | 4,192 | 0.873 |
| crypto up or down titles | 90 | 71 | 0.789 |

The exact-0.500 group is small, at a median of 1 row per run and a maximum of
14 against 15 slots, so it never decides a whole list on the tie break. It is
worth a filter anyway because it sits at the arithmetic maximum of 2p(1-p).

Does a deterministic filter reproduce what the subagent did? Rates are over the
rows each filter fires on. The baseline for comparison is every non-matching row
on the two revisions that carry the hard rule: divergence 0.0 at 0.561 and
confidence `low` at 0.923, on 5,039 rows:

| filter | prompt_rev | fires on | divergence 0.0 | confidence low |
|---|---|---|---|---|
| line-constructed shape | f7ddad12 | 1,992 | 0.881 | 0.999 |
| line-constructed shape | ce4bfcd2 | 747 | 0.908 | 0.996 |
| line-constructed shape | 341771ea | 1,587 | 0.227 | 0.651 |
| line-constructed shape | f055b035 | 4,303 | 0.274 | 0.772 |
| crypto up or down | f7ddad12 | 95 | 0.663 | 0.958 |
| crypto up or down | ce4bfcd2 | 49 | 0.592 | 0.939 |

The two revisions carrying the rule agree with the regex on 88% to 91% of
matched rows, which is 32 percentage points over the baseline. The two revisions
without the rule do not, which is the check that the regex is reading the rule
rather than the shape.

Slots a filtered shape holds in a 15-slot list, counting line-constructed,
crypto up or down, and exact-0.500 mids together:

| prompt_rev | runs | divergence ranking | uncertainty ranking | uncertainty, filtered |
|---|---|---|---|---|
| f055b035 | 36 | 4.36 | 6.78 | 0.00 |
| f7ddad12 | 19 | 3.37 | 7.84 | 0.00 |
| 341771ea | 13 | 9.85 | 6.08 | 0.00 |
| ce4bfcd2 | 7 | 2.71 | 6.43 | 0.00 |

The filtered list still fills to 15 in every run.

Four candidate extensions to the regex were tested and rejected, because their
divergence-0.0 rate does not clear the 0.561 baseline or their footprint on the
list is negligible: both teams to score (220 rows, 0.582 against baseline),
esports map or game winner (341 rows, 0.627), best-of-3 or best-of-5 titles
(1,306 rows, 0.638), and score-first markets (41 rows, 0.909 but 0.000 of the
uncertainty top 15). Only `after N innings` clears the baseline convincingly, at
0.933 on 20 rows, and it holds 0.0036 of the list.

Rules with no measurable footprint on a screener row: "liquid and well-defined",
"a named official print", "a stale price", "thin or exotic", "a fact I would have
to look up", "a generic category base rate", and the four traps. The journal
carries no liquidity, volume, or resolution-source field, and the rest live in
free text. Dropping the model tier drops those judgments outright. That is the
cost of a full switch, and it is not measurable from this data.

## Question 4: the dormant rank mode

`core/screen_rank.py rank` takes the same scan input, applies the same strata
through `core/screen.py`, and writes one `journal/screener.jsonl` row per market
in the same schema. Nothing calls it.

- `model` is `formula:mid-uncertainty-2p1p-v1`.
- `prompt_rev` is the git blob hash of `strategy/screener-filters.json`, the rule
  file it reads, not of `screener-prompt.md`, because no model ran.
- `probs` is the mids verbatim: the formula's estimate for a market is its price.
- `divergence` stays null and the ranking lives in `rank_score`, so
  `core/screen.py collect` and `screen_replay.select` skip these rows instead of
  reading the formula as a model opinion.
- `screen_error` says why the divergence is null, which is what
  `core/validate.py` asks of an unscored row.
- `filtered_by` lists the deterministic filters that fired, and `stratum` records
  the lane.

`strategy/screener-filters.json` holds the filters and is agent-editable. It
carries the two title patterns validated in question 3, the exact-0.500 mid drop,
and a binary-outcome guard. A pattern that fails to compile is skipped on stderr
and the rest still apply.

Dry run against `work/scan.json`, the 2026-09-03 scan of 994 candidates: 300
markets ranked, 115 filtered as 110 line-constructed, 4 crypto up or down, and 3
exact-0.500 mids with 2 rows firing two filters, and 15 escalated. Counts move by
a few rows between runs because `stratify` reseeds the random tail on the run
stamp, which is the same behavior `prepare` has.

The write path was exercised against a scratch log rather than
`journal/screener.jsonl`, which this run was not permitted to touch: 300 rows
written, 0 errors against `core/validate.py`'s screener contract, 0 rows graded
by `screen_replay.select`, and 0 rows rankable by `core/screen.py collect`.

The escalated 15 all scored between 0.49875 and 0.49995, meaning mids between
0.475 and 0.525. Fourteen were sports or esports matchups and one was an ETF
price threshold. That list is the decision in one screen: a formula that ranks by
2p(1-p) hands the researcher an hour of coin flips.

## How to switch it on

1. Read this file and `journal/operator-notes.md` for 2026-09-04.
2. To take the filters only, port the patterns in
   `strategy/screener-filters.json` into `core/screen.py stratify` as a drop
   step, and leave the Haiku tier ranking the survivors.
3. To take the whole formula, replace the `prepare`, fan-out, and `collect`
   steps in `CYCLE.md` with one `python3 core/screen_rank.py rank` call. The
   screener batch quota then goes unused.
4. Either way, record the switch in `journal/operator-notes.md` so the
   `prompt_rev` break in `journal/screener.jsonl` is explained.
