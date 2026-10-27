# Archived playbook settlement updates (moved DEEP-2026-10-27)

Verbatim from strategy/playbook.md. Settlement narrative only, no live rules.

## 2026-09-30 18:57Z update: two `outside-view-veto` rows settled (Alibaba best Chinese AI model, Musk 40-64 tweets) (RETRO-20260930-1857)

| Alibaba best Chinese AI model (`f41e0b09f084`, OVV, supersedes `1e0944b4f952`) | 0.65 / 0.935 | No | +0.29 | No | **+66.43** |
| Musk 40-64 tweets Sep28-30 (`16af5b16fa0c`, OVV) | 0.85 / 0.675 | Yes | +0.18 | Yes | **+2.35** |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
outside-view-veto`): 186 rows, 76W/102L, +$134.99 (was +$66.20;
66.20+66.43+2.35=134.98, rounding ✓), dBrier +0.0311 (was +0.0343). Side:
no +$102.10 (35.67+66.43=102.10 ✓); yes +$32.88 (30.53+2.35=32.88 ✓).
Ruling: no boundary change — both are single new rows in already-populated
groups (ai-leaderboard n=1 event overall; countable-metric carve-out bar
still not met per RETRO-20260930-1857). The Alibaba row is notable because
it is the first settlement in the "fading a >0.90 consensus" family (July
twin losses, RETRO-20260731-1912/2211) to go the other way — the declined
No bet would have won big instead of losing — but n is still 1 for this
exact market and far below the ~15-settlement floor for acting on it.

## 2026-10-01 09:39Z update: one outside-view-veto row settled (FULL tick, RETRO-20261001-0939)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| NK exactly 2 tests Sep (`71aef6acf4eb`, OVV) | 0.47/0.32 | Yes | +0.140 | Yes | **+10.15** |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
outside-view-veto`): 194 rows, 79W/107L, +$121.63 (was
193/78W-107L/+111.48; 111.48+10.15=121.63 check), dBrier +0.0316 (was
+0.0327). Side split: No +$98.60 (unchanged); Yes +$23.03 (was +$12.88,
12.88+10.15=23.03 check).

Ruling: no boundary change. The NK count family (4+, exactly 3, exactly
2) landed own-closer on all three legs, but it is one draw on a
first-use Poisson rate; the count model stays `unvalidated-method`
until it grades on at least five independent months or families.

## 2026-10-01 19:18Z update: one wide-spread-veto row settled + one backfill (FULL tick, RETRO-20261001-1918)

**Backfill:** `a7a4bdb5c92f` Iran Sanctions EO settled on the 11:51Z
LIGHT tick and was graded narratively in RETRO-20261001-1151 without
the same-commit table row (DEEP-2026-08-23). Entered here.

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Iran Sanctions EO Sep30 (`a7a4bdb5c92f`, WSV, backfill) | 0.04/0.215 | No | +0.040 | No | **+0.43** |
| Kraken NPM HIGH 13B Sep30 (`cb37130b62a6`, WSV) | 0.02/0.209 | No | - | No | refused (no bid at record) |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
wide-spread-veto`): 39 rows, 32 trd, 7 refused, 19W/13L, -$33.62 (was
37/18W-13L/-34.06; -34.06+0.43=-33.63, 0.01 rounding), dBrier -0.0033
(was -0.0011). Side split (question frame): No -$28.97 over 19 trd.

Ruling: no boundary change. Both rows were thin-book spread-artifact
mids ($26 and $330 liquidity) where the veto cost little either way.

## 2026-10-01 23:36Z update: two `wide-spread-veto` rows settled, both refused (LIGHT tick, RETRO-20261001-2336)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Biggest earthquake Sep30, 5.3-5.4 (`0112790db6f8`, WSV) | 0.01/0.079 | Yes | -0.003 | No | refused (entry 0.013, outside [0.02, 0.95]) |
| Stripe NPM LOW $155B by Sep30 (`7607dc6c9caa`, WSV) | 0.01/0.101 | No | - | No | refused (no bid at record) |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
wide-spread-veto`): 41 rows, 32 trd, 9 refused, 19W/13L, -$33.62
(unchanged -- both new rows are refused, not fillable), dBrier -0.0033
(unchanged).

Ruling: no boundary change. Both rows were unfillable (price outside the
[0.02, 0.95] band / no bid at record), so neither adds a trade to the
ledger -- the veto's cost is zero on these two by construction.

## 2026-10-02 00:41Z update: one `wide-spread-veto` row settled, fillable (FULL tick, RETRO-20261002-0041)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Trump "Made in America" at Peterbilt Oct1 (`486cacf5edf4`, WSV) | 0.85/0.53 | Yes | +0.22 | Yes | **+2.94** |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
wide-spread-veto`): 42 rows, 33 trd, 9 refused, 20W/13L, -$30.69
(was -$33.62; +2.94, 0.01 rounding), dBrier -0.0080 (was -0.0033).
Side split (question frame): Yes -$1.72 over 14 trd, No -$28.97 over
19 trd.

Ruling: no boundary change. The veto lost $2.94 here, but the Yes side
is near break-even over 14 trades and the 0.85 estimate cited a
sibling phrase's hit count, not its own.

## 2026-10-02 15:45Z update: two `outside-view-veto` rows settled (Tesla Q3 deliveries) + Musk backfill (FULL tick, RETRO-20261002-1545)

**Backfill:** `a6a6ed8790b0` Musk Sep25-Oct2 200-219 tweets settled on
the 11:03Z LIGHT tick; RETRO-20261002-1103 graded it but said the table
was unchanged. Declined OVV forecasts are this table, so it is entered
here.

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Musk 200-219 tweets (`a6a6ed8790b0`, OVV, backfill) | 0.38/0.655 | No | +0.27 | No | **+9.29** |
| Tesla Q3 475k-500k (`a3ef8fda3cc9`, OVV, superseded) | 0.47/0.60 | No | +0.12 | Yes | **-5.00** |
| Tesla Q3 475k-500k (`6fa8dd2218cf`, OVV) | 0.70/0.905 | No | +0.19 | Yes | **-5.00** |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
outside-view-veto`): 197 rows, 80W/109L, +$120.92 (was
194/79W-107L/+$121.63; 121.63+9.29-10.00=120.92 check), dBrier +0.0307
(was +0.0316). Side split: No +$97.88 (was +$98.60; 98.60+9.29-10.00 =
97.89, 0.01 rounding); Yes +$23.03 (unchanged).

Ruling: no boundary change. The veto saved $10 on the two Tesla rows.

**Unexplained-move tracking, n=3 (2-for-3 market right).** The Tesla
book climbed 0.22 (Sep 28) to 0.93 (Oct 2) with no source found; actual
486,532 landed in the bracket. Tally: Opus (Sep 21, sudden jump that
reversed, discounting right), Trump renames AI (Sep 29, multi-day
climb, market right), Tesla (Oct 2, multi-day climb on a liquid book,
market right). Split to watch: sudden jump versus gradual multi-day
drift on a liquid book. Still a tracked observation, not a rule, until
it has far more settlements. **n=4 (RETRO-20261007-2215): Haiku 4.6+ by
Oct 7 (`d603bfb03fc2`, WSV), sudden 0.10->0.80 jump on a ~$750 book with
no public release at my check, ~11.5h before a same-day cutoff; I held
0.55, it resolved Yes (dBrier +0.164). Tally 3-for-4 market right;
sudden-jump split 1-1. On a by-date release market, a sudden jump plus
the same-day-deadline timing rule above means re-check near the cutoff
or record near the market, not a mid-session discount.**
**n=5 (RETRO-20261009-1240): Kuleba Nobel Peace (`637034`), sudden
0.055->0.25 climb in the ~9h before a sealed 09:00Z committee
announcement, no source; I shaded 0.05->0.10->0.15 toward it, Navi Pillay
won (net dBrier -0.066 on 4 Nobel rows, but each shade toward the move
cost Brier vs my prior). Tally 3-for-5 market right. Sudden-jump split
now 2-1 discount-right, and the one market-right sudden jump (Haiku) was
a by-date release whose event could already have happened. Observation
to test, not yet a rule: on a SEALED-decision market (committee/jury
announcement, outcome not knowable before the reveal), hold the prior
instead of shading toward an unsourced late jump. Still no fade bet
(n=5 << 15).**

## 2026-10-02 18:57Z update: one `outside-view-veto` and one `wide-spread-veto` row settled, post-count pair graded (FULL tick, RETRO-20261002-1857)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Musk 220-239 tweets Sep25-Oct2 (`89733920b201`, OVV) | 0.56/0.345 | Yes | +0.21 | Yes | **+9.28** |
| Trump 200+ Truth Social Sep25-Oct2 (`50d4af915a81`, WSV, superseded) | 0.55/0.425 | Yes | -0.05 at ask 0.60 | No | **-5.00** |

OVV ledger: 198 rows, 81W/109L, +$130.20 (was +$120.92; 120.92+9.28),
dBrier +0.0293 (was +0.0307). Side split: Yes +$32.31, No +$97.88.
WSV ledger: 43 rows, 34 trd, 9 refused, 20W/14L, -$35.69 (was -$30.69),
dBrier -0.0050 (was -0.0080). Side split: Yes -$6.72 over 15 trd, No
-$28.97 over 19 trd. Ruling: no boundary change on either.

**Unshaded post-count bootstrap (RETRO-20260925-1812), two more
independent events.** Musk Sep25-Oct2 (all windows 0.56, won, -0.235)
and Trump Sep25-Oct2 200+ (all windows 0.414, lost, +0.069): latest
rows net -0.167 vs the mid. The rule stands. Watch item: the Trump miss
came with a visible slowdown (16 posts in the 15h before record) that
only the aligned windows (0.333, n=6) carried. If two more independent
events miss the same way, revisit "all windows when aligned n<20".
**Tally (RETRO-20261009-1815): 1 of 2.** Trump Oct2-9 28h-out pair
(8839a85fa21a 0.58 / d51845662a3e 0.37, all windows) lost the mid by
+0.051 net while the written drift view (0.85/0.12, last 48h 8-9/day)
would have won by ~0.22. One more such miss triggers the revisit.

**Label slip:** `89733920b201` (Musk tweets) was recorded as
`countable-metric`; tweet counts are `social-media-postcount`.

## 2026-10-08 02:15Z update: Iran/Arab-country, Amapa, TX rally Cartel/Toyota veto rows settled (FULL tick, RETRO-20261008-0215)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Iran targets Arab country Sep30 (`1715cc4fdf88`, WSV) | 0.03/0.14 | No | +0.060 | Yes | **-5.00** |
| Lula most votes Amapa (`ffc04c6d6ead`, OVV) | 0.62/0.755 | No | +0.080 | Yes | **-5.00** |
| Trump TX "Cartel" (`993d9f58cf3d`, WSV) | 0.45/0.495 | No | -0.080 | Yes | **-5.00** |
| Trump TX "Toyota" (`7d24a6d253da`, WSV) | 0.45/0.71 | No | +0.160 | Yes | **-5.00** |

Mechanical ledger (`core/counterfactual.py ledger`): OVV 235 rows, 227
trd, 98W/129L, +$192.40, dBrier +0.0264; side split No +$128.02 (154
trd), Yes +$64.38 (73 trd). WSV 61 rows, 51 trd, 10 refused, 28W/23L,
-$49.36, dBrier -0.0029; side split No -$69.23 (32 trd), Yes +$19.87
(19 trd). Tool totals, not hand re-sums.

Ruling: no boundary change; all four vetoes saved the stake. Say-the-word
note for the next deep retro (n=2, Egg + Toyota): a word tied to the host
venue's local industry should not be anchored on the rally-only transcript
base; the market's venue read beat it both times.

## 2026-10-08 14:20Z update: TX rally / Musk / PEP veto rows settled (FULL tick, RETRO-20261008-1420)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Musk Oct5-7 <40 (`a17f658eef54`, OVV, superseded) | 0.52/0.575 | No | +0.050 | No | **+6.63** |
| Musk Oct5-7 <40 (`7a60de0b5d33`, OVV, superseded) | 0.76/0.71 | Yes | +0.040 | No | -5.00 |
| Trump TX "Data Center" (`a39826fe4c4f`, OVV) | 0.42/0.565 | No | +0.120 | No | **+5.87** |
| Trump TX "Gulf of America" (`1a4a4d0f0ec8`, OVV) | 0.50/0.695 | No | +0.150 | Yes | -5.00 |
| Trump TX "1776" (`4b4fbbe5dea1`, OVV) | 0.60/0.895 | No | +0.250 | Yes | -5.00 |
| PEP beat (`791f6d9d1bbb`, OVV) | 0.62/0.825 | No | +0.190 | Yes | -5.00 |
| Trump TX "Fascism" (`c11f064720f9`, WSV) | 0.20/0.355 | No | +0.080 | Yes | -5.00 |
| Trump TX "Mental Institution" (`f51c6e816257`, WSV) | 0.65/0.79 | No | +0.020 | No | **+10.15** |
| Trump TX "Alamo" (`232b304e2f22`, WSV) | 0.55/0.455 | Yes | -0.030 | Yes | +3.62 |
| Trump TX "Cartel" (`d71d861b9512`, WSV) | 0.40/0.495 | No | -0.030 | Yes | -5.00 |

Mechanical ledger (`core/counterfactual.py ledger`): OVV 241 rows, 233
trd, 100W/133L, +$184.90, dBrier +0.0269 (was 235 rows, +$192.40). WSV
66 rows, 56 trd, 10 refused, 31W/25L, -$40.59, dBrier -0.0030 (was 62
rows, -$44.36). Tool totals, not hand re-sums.

Ruling: no boundary change. The three largest live OVV fades (Gulf of
America, 1776, PEP; all fading a mid >= 0.69) lost; the veto saved $15.
- **Venue-local words tally (rule above): n=4, 4/4 for the rule.** Gulf of
  America (TX, faded 0.50 vs 0.695, lost, dBrier +0.157) and Alamo (TX,
  recorded above the mid, won, -0.095) join Egg and Toyota. Re-grade at
  n=5 unchanged.

## 2026-10-09 14:30Z update: Holborn & St Pancras Green-share WSV ladder settled (FULL tick, RETRO-20261009-1430)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Holborn Grn 35-40 (`07bd55f592fd`, WSV) | 0.15/0.075 | Yes | +0.030 | No | -5.00 |
| Holborn Grn 30-35 (`2a7809f09927`, WSV) | 0.32/0.40 | No | -0.050 | Yes | -5.00 |
| Holborn Grn 25-30 (`817e680fd58f`, WSV) | 0.30/0.29 | Yes | -0.190 | No | -5.00 |

Mechanical ledger (`core/counterfactual.py ledger`): WSV 70 rows, 60 trd,
10 refused, 31W/29L, -$60.59, dBrier -0.0010 (was 66 rows, -$40.59; the
fourth new row is 306eb6a66967, graded in RETRO-20261009-1015). OVV
unchanged. Tool totals, not hand re-sums.

Ruling: no boundary change; the veto saved $15. Recording rule (n=1,
cannot create a bet): on a vote-share ladder with several independent
projections, set the model sd from the projections' own dispersion
(floor 4 pts), not a round 6 — the sd-6 model put the right centre on
the wrong width (modal leg 0.32 vs book 0.40, dBrier +0.102). Re-grade
at the next share ladder.

## 2026-10-09 20:15Z update: Kyiv Oct-9 daily-target WSV row settled (FULL tick, RETRO-20261009-2015)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Russia target Kyiv Oct 9 (`e5f7ac9f6cbd`, WSV) | 0.70/0.854 | No | +0.088 | Yes | -5.00 |

Mechanical ledger (`core/counterfactual.py ledger`): WSV 71 rows, 61 trd,
10 refused, 31W/30L, -$65.59, dBrier -0.0000 (was 70 rows, -$60.59).
OVV unchanged. Tool totals, not hand re-sums.

Ruling: no boundary change; the veto saved $5. Recording rule (n=1,
cannot create a bet): on daily "Will Russia target Kyiv on <date>"
markets, absence of a reported strike before the Kyiv evening is weak
evidence (launches cluster at night, reports lag) — in a high-tempo month
shade at most ~0.05 below the base rate on absence alone; the 0.15 shade
cost dBrier -0.069. Re-grade at the next settlement in this family
(open: af505e60c020, 4e1fe00a7371, bf588ea82108, all Oct 12).

## 2026-10-10 00:15Z update: Zelenskyy Oct 2-9 80-99 WSV row settled (FULL tick, RETRO-20261010-0015)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Zelenskyy X posts Oct 2-9 80-99 (`029d793933c6`, WSV) | 0.60/0.825 | No | +0.200 | Yes | -5.00 |

Mechanical ledger (`core/counterfactual.py ledger`): WSV 72 rows, 62 trd,
31W/31L, -$70.59, dBrier +0.0018 (was 71 rows, -$65.59). OVV unchanged.
Tool totals, not hand re-sums.

Ruling: no boundary change; the veto saved $5. **Extension of the
"book beats visible counter" rule (4th event; Trump TS Sep18-25, Musk
Oct1-3, Musk Oct2-9 tail, Zelenskyy Oct2-9):** when my own note
diagnoses WHY the tracker counter is wrong (capture gap, missing
language twins, import lag, backfill) and the resolution rules name a
fallback source the book is visibly pricing, record est_prob within 0.10
of the mid and write the tracker-literal read as "api view: X" in the
note — regardless of the sibling's liquidity. Shading toward a counter I
have already explained away cost dBrier +0.129 here. Re-grade at the
next postcount settlement where the counter and the book disagree.

## 2026-10-10 18:15Z update: MrBeast plN7JMbadRg wk1 veto rows settled (FULL, RETRO-20261010-1815)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| wk1 207-215 (`ed4024a9d4c7`, OVV, superseded) | 0.50/0.705 | No | +0.190 | No | **+11.13** |
| wk1 215-223 (`4b593e57d185`, WSV, superseded) | 0.42/0.24 | Yes | +0.150 | Yes | **+13.52** |
| wk1 207-215 (`73c80f107bab`, OVV, superseded) | 0.43/0.775 | No | +0.330 | No | **+15.83** |
| wk1 207-215 (`fc349be56b8a`, OVV, final) | 0.55/0.355 | Yes | +0.180 | No | -5.00 |
| wk1 215-223 (`d72d87152a63`, OVV, final) | 0.45/0.635 | No | +0.180 | Yes | -5.00 |

Net this batch, all five rows: **+30.48** (3W/2L). The final rows alone
come to -10.00, so the veto saved $10 there. The family cost is $40.48
of foregone wins on the earlier peak-hours reads. Mechanical ledger
(`core/counterfactual.py ledger`): OVV 237 fillable, 102W/135L, +$201.86,
dBrier +0.0252. WSV 63 fillable, 32W/31L, -$57.07. Those are the tool's
totals, not hand re-sums. Ruling: no boundary change at n=1 event. The
failure was in the method: the final flip extrapolated a trough-hours
pace. The diurnal-matched pace rule (above) fixes that.

## 2026-10-11 20:15Z update: PMO Dem Senate Oct-9 WSV rows settled (FULL, RETRO-20261011-2015)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| PMO Dem Senate 64-66 Oct 9 (`8ab87e366ec4`, WSV) | 0.03/0.32 | No | +0.210 (No @0.76) | No | +1.58 |
| PMO Dem Senate 60-62 Oct 9 (`88d1b2dd9235`, WSV) | 0.30/0.2165 | Yes | -0.099 (Yes @0.399) | Yes | +7.53 (negative-edge side; not a trade the gates would take) |

Mechanical ledger (`core/counterfactual.py ledger`): WSV 75 rows, 65 trd,
34W/31L, -$47.96, dBrier -0.0045. Tool totals, not hand re-sums. Ruling:
no boundary change. Both books were 0.16-0.37 wide on $100 liquidity;
the driftless resolver-series recording rule (RETRO-20260925-2015) scored
the family -0.132 dBrier vs mid, but a mid in a book that wide is not a
fillable price. Recording rule stands; category bar stands.

## 2026-10-13 03:58Z update: Trump Youngstown "Border" 10+ settled (TRIGGERED, RETRO-20261013-0358)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Trump Youngstown "Border" 10+ (`7ddc5e13d346`, OVV) | 0.50/0.675 | No | +0.175 (No @0.325) | Yes | -5.00 |

Mechanical ledger: OVV 249 rows, 241 fillable, 103W/138L, +$194.68. Ruling:
n=1, no boundary change — the transcript-count model landed 0.50 with no
venue-local bump on a 3/5-historical threshold while two sibling words from
the same rally (Steel, Columbus) got one; the veto was mechanically correct
to fire on the >0.10 claimed edge, it just lost this draw. Cumulative dBrier
not recomputed this cycle (row-level recompute deferred to next deep retro);
dollar/W-L counts above are exact.

## 2026-10-14 04:15Z update: AK rally + China CPI veto rows (FULL, reconcile.py check 5; graded in RETRO-20261014-0415)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| China CPI 0.9-1.0% (`fc10ca9ae3bb`, OVV) | 0.50/0.62 | No | +0.110 | Yes | -5.00 |
| Trump AK "AI" (`a56e574d6076`, OVV) | 0.38/0.23 | Yes | +0.140 | No | -5.00 |
| Trump AK "SI" 3+ (`9531522c6c7e`, OVV) | 0.35/0.225 | Yes | +0.110 | No | -5.00 |
| Trump AK "Israel" (`aff10b42cb3a`, OVV) | 0.50/0.37 | Yes | +0.110 | No | -5.00 |
| Trump AK "Spoiler" (`4daedc7531c7`, WSV) | 0.30/0.595 | No | +0.150 | No | +4.09 |

OVV saved $20 (0W/4L). WSV missed +$4.09 at a 0.40-spread book. No rule change.

## 2026-10-14 14:25Z update: BAC beat WSV row settled (FULL, RETRO-20261014-1425)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| BAC beat GAAP EPS >1.16 (`a9e6f62303e4`, WSV) | 0.04/0.305 | No | +0.130 (No @0.83, spread 0.27) | No | +1.02 |

WSV missed +$1.02. The estimate was right (dBrier -0.091) and the fill was poor.
Earnings WSV group: 2 rows, 2W, +$1.71. No rule change at n=2.

## 2026-10-14 16:20Z update: Sep CPI ladder + PortWatch Oct 5-11 weeks settled (FULL, RETRO-20261014-1620)

- **feed-days-gate, first settlement.** The gate has its own counterfactual slice:

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Mandeb Oct5-11 190-209 (`706ab3d9b265`, feed-days-gate) | 0.50/0.405 | Yes | +0.080 (@0.42) | Yes | +6.90 |

  The gate's trigger bet 9b7c41da79ac cost -$5.00. One each way, so the gate stays.
  Re-grade it at 5 settled gate rows.
- **0-published-days PortWatch weeks: est_prob at most half the gap from the mid**
  (tightening only, provisional n=3 weeks). Mandeb Sep 28 (bet lost, book skew high,
  right), Mandeb Oct 5 (35bfaf72496e 0.47 vs 0.23, +0.168, book skew high, right) and
  Hormuz Oct 5 (model below the book's 25-29 centre, 3 rows +0.115, book right). When no
  in-window day is published, the book sees AIS that I cannot. Put the raw model in the
  note and record est_prob no more than half the raw gap from the mid. When the week has
  >= 3 published days, the existing model applies unchanged.
- **Sep CPI ladder: at market** (22 rows, +0.0041/row; the 6 gate-2 unsourced-sd rows
  net -0.001). No change to gate 2.

## 2026-10-15 00:15Z update: AZ rally say-the-word + PGR OVV row settled (FULL, RETRO-20261015-0015)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| PGR Q3 combined ratio 86-89% (`bfe4b4889c74`, OVV) | 0.45/0.595 | No | +0.140 (No @0.41) | Yes | -5.00 |

OVV saved $5.00. The estimate projected a storm-month Sep from 2024-25 history in a quiet cat
quarter (n=1, note only).

- **Transcript-count side tally (pre-registered, not fired):** AZ rally Hormuz (0.42/0.34) and AI
  (0.33/0.22) Yes-side holds both resolved Yes. Above-side now 4/7 rows over 4 rallies, sum
  dBrier **-0.106** (was 2/5, +0.153). Below-side 7/12, -0.068 (Transgender 5+ knife-edge row
  lost its No lean again). Hold counterfactual this rally +$26.03 missed vs +$15 saved on AK.
  Gate unchanged until the 10-row trigger; at that read, report rows and rallies together.

## 2026-10-15 02:15Z update: AZ rally remaining say-the-word rows (FULL, RETRO-20261015-0215)

- **Transcript-count side tally (pre-registered, not fired):** Israel (0.40/0.29) Yes-side hold
  resolved No (+0.076, hold saved $5); SI 3+ (0.25/0.165) Yes-side hold resolved Yes (-0.135,
  CF +$22.78 missed). Above-side now **5/9 rows, sum -0.165**, 4 distinct rallies (AZ = 4 of
  the 9 rows). Below-side unchanged 7/12, -0.068. AZ hold CF net +$43.81 missed vs +$15 saved
  on AK. One row from the 10-row trigger; at that read report rows and rallies, and weight by
  rally (effective n ~5) before deciding the half-gap shade.

## 2026-10-15 20:15Z update: Dallas rain WSV row settled (FULL, RETRO-20261015-2015)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| Rain Dallas Oct 14 (`e3c1a45dc910`, WSV) | 0.04/0.11 bid-only | No | +0.070 (No @0.89) | No | +0.62 |

The WSV forfeited $0.62. Totals: 79 rows, 69 trd, 37W/32L, CF -$47.22 (-47.84+0.62 ✓). This is a
measured-print same-day weather row. No rule change at n=1.

## 2026-10-15 22:15Z update: IBKR beat OVV + WSV rows settled (FULL, RETRO-20261015-2215)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| IBKR beat non-GAAP EPS >0.70 (`8deb84c936d1`, OVV, superseded) | 0.60/0.48 | Yes | +0.110 (Yes @0.49) | No | -5.00 |
| IBKR beat non-GAAP EPS >0.70 (`9457a2d2b5b9`, WSV) | 0.45/0.335 | Yes | -0.010 (Yes @0.46) | No | -5.00 |

Both vetoes saved $5. WSV totals: 80 rows, 70 trd, 37W/33L, CF -$52.22 (-47.22-5.00 ✓).
OVV tool totals: 260 rows, 252 trd, 104W/148L, +$147.49. Earnings WSV group: 4 rows, 2W/2L,
-$8.29 (-3.29-5.00 ✓). IBKR printed adjusted $0.67 against a 0.70 line and ~0.67-0.68 consensus.

**Earnings line-above-consensus rule (n=2 today: SCHW `b0905f460b3c`, IBKR `9457a2d2b5b9`, both
estimated above the mid, both No).** When the market's line exceeds consensus, the estimate
starts from P(actual - consensus >= line gap), read from the issuer's sourced beat-SIZE history.
A beat COUNT may not move the estimate above the mid on its own. Without a sourced size history,
record at or below the mid and put any lean in the note as "shade view: X".

## 2026-10-16 00:15Z update: Moscow daily-target absence row settled (FULL, RETRO-20261016-0015)

| Row | own/mkt | skip | Result | dBrier |
|---|---|---|---|---|
| Ukraine target Moscow Oct 15 (`236e5dd959fa`) | 0.68/0.775 | no-edge | Yes | +0.052 |

**Daily city-target absence cap, generalised (n=2: Kyiv `e5f7ac9f6cbd` 0.70/0.854 Yes, Moscow
`236e5dd959fa` 0.68/0.775 Yes; both shaded below the mid on absence alone, both Yes).** The
RETRO-20261009-2015 Kyiv rule applies to every daily "<actor> target <city> on <date>" market,
not only Russia->Kyiv: while any evening/night hours of the local date remain, absence of a
report may shade the estimate at most 0.05 below the mid (or base rate, whichever is lower).
A larger shade needs a positive fact (announced pause, ceasefire, confirmed calm-night report),
not a failed search. Re-grade at the next settlement in this family.

## 2026-10-16 14:30Z update: Seahawks-Broncos 'Inch' WSV row settled (FULL, RETRO-20261016-1430)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| SEA-DEN announcers 'Inch/Inches' (`fbbba722cbb1`, WSV) | 0.80/0.505 | Yes | +0.170 (Yes @0.63) | Yes | +2.94 |

The WSV forfeited $2.94. Totals (`core/counterfactual.py ledger`): 81 rows, 71 trd, 38W/33L, CF -$49.29
(-52.22+2.94 ✓ to rounding). Settled 08:33Z but went ungraded through the 10:25Z and 12:16Z cycles
(resolve printed 0 because the 08:13Z cycle's run had already settled it); reconcile.py caught it.
No rule change at n=1: the announcer-series base rate (Laplace 0.79) was right, and the veto
cost is within the WSV ledger's running pattern (net still negative, so max_spread stays).

## 2026-10-19 00:15Z update: Kyiv Oct18 absence-fade rows settled Yes (FULL tick, RETRO-20261019-0015)

**City-target absence cap re-anchored on the base rate (n=3, all Yes after absence shades:
Kyiv `e5f7ac9f6cbd` Oct9, Moscow `236e5dd959fa` Oct15, Kyiv `d4914365f76b` Oct18).**
On Oct18 my supersedes (0.84 -> 0.65 -> 0.50 -> 0.42) each stayed within 0.05 of a mid
that was itself fading (0.845 -> 0.39) on no positive fact, and the market resolved Yes.
The "mid or base rate, whichever is lower" clause let me inherit the market's fade.
Replacement rule: while any evening/night hours of the local date remain, absence of a
report shades at most **0.10 below the month's base rate**, independent of the mid. A
larger shade still needs a positive fact (announced pause, ceasefire, confirmed calm-night
report). When the ask sits far below that anchor, record the gap honestly as a
forecast-only Yes candidate (skip-reason `unvalidated-method`) until n>=5 rows settle
under this anchor; a deep retro then decides whether it becomes a betting class.

## 2026-10-19 08:15Z update: China Q3 GDP OVV row settled (FULL, RETRO-20261019-0815)

| Row | own/mkt | Side | Edge | Result | CF pnl |
|---|---|---|---|---|---|
| China Q3 GDP 4.3-4.6 first read (`2ae729db32f5`, OVV, superseded) | 0.55/0.335 (No) | No | +0.190 (No @0.36) | Yes | -5.00 |

The veto saved $5. OVV tool totals (`core/counterfactual.py ledger --skip-reason
outside-view-veto`): 262 rows, 254 trd, 104W/150L, +$137.49. This was a pre-consensus
self-built nowcast, and the post-poll supersede (`cc9769b230bb`, 0.28 No) agreed with the
market. No boundary change.

## 2026-10-24 02:15Z update: Kyiv Oct17 daily-target rows settled No (FULL, RETRO-20261024-0215)

**What counts as a positive fact on daily city-target markets (n=1: Kyiv `cb75789e5935`
0.88/0.739 No, the first No after Oct1-16 16/16 Yes).** A secondary outlet's "capital under
drone attack / explosions heard" line, with the city administration (KMVA for Kyiv) posting
alerts only, is NOT a positive Yes fact: the resolver did not count it. A Yes read above the
mid needs an official city-administration post on AD over the city / debris / damage, or a
named-outlet strike report on the city itself. Converse (`e07028a1da26` 0.20/0.142 No): the
RETRO-20261019-0015 absence cap binds only while local evening/night hours remain; once the
local date has closed, official silence IS the positive fact the cap asks for. Not an
estimation rule (no slug): it says which evidence counts, not how to move a number.
