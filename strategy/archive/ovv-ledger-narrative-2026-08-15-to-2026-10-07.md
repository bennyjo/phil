# Archived: OVV counterfactual-ledger narrative (playbook section, verbatim)

Moved out of strategy/playbook.md by DEEP-2026-10-22 (bloat control). This is the
section exactly as it stood at that commit, batch narratives included. The live rules
it contained, and every table row, were kept in the playbook section of the same name.

## Outside-view veto: settled counterfactual ledger (DEEP-2026-08-15)

Per-row fill arithmetic over ALL settled `outside-view-veto` forecast rows
(flat 1u on the model's side at the recorded book; the discipline the
RETRO-20260813-1707 correction demanded). This table supersedes every
narrative "N-for-N" veto claim; future veto-record statements cite it and
extend it at each settlement.

**Append discipline (DEEP-2026-09-02, bloat control):** this file crossed
3,300 lines and the dated multi-paragraph batch narratives in this section
are the fastest-growing block (+248 playbook lines in the 09-01→09-02
window alone; every line is re-read by every hourly cycle). From now on a
settled veto batch appends ONLY: its table rows, the one-line re-summed
totals + side split with the arithmetic check, and at most 2–3 sentences
of ruling. The full narrative (family history, method grading, lessons)
lives in that settlement's retro, referenced by filename — the retro is
already mandatory same-commit, so nothing is lost. Existing blocks stay
as-is for now; if growth continues the next deep retro should compact the
CLOSED-family narratives (Mythos, box-office Aug31, touch-family, AAA gas)
down to their tables + retro pointers.

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
| Musk 2d <40 (8f663df4a762) | 0.0146 / 0.195 | No | +0.175 | Yes | −1.00 |
| Oak Street 17-20m (f0672a1a69e7) | 0.29 / 0.455 | No | +0.140 | No | **+0.75** |
| Spider-Man <66m (9ad9a1e605a5) | 0.42 / 0.31 | Yes | +0.020 | No | −1.00 |
| Spider-Man 66-68m (db6bd4ff0cb7) | 0.31 / 0.54 | No | +0.190 | No | **+1.00** |
| Spider-Man 68-70m (64695326b358) | 0.19 / 0.0695 | Yes | +0.061 | No | −1.00 |
| HD earnings (65aea7cd91f4) | 0.68 / 0.84 | No | +0.130 | Yes | −1.00 |
| Musk wk 180-199 (99feadecc33b) | 0.494 / 0.325 | Yes | +0.164 | No | −1.00 |
| Musk wk 220-239 (cf16f6424af7) | 0.024 / 0.145 | No | +0.116 | No | **+0.16** |
| Musk wk 240-259 (cd3af116ed2a) | 0.16 / 0.2575 | No | +0.092 | Yes | −1.00 |
| Musk wk 280-299 (cc08840449e9) | 0.31 / 0.165 | Yes | +0.141 | No | −1.00 |
| TI VISION/Yandex (6b84771a3bd6) | 0.383 / 0.235 | Yes | +0.143 | No | −1.00 |
| BTC touch-$80k (fc4a9d5caace) | 0.5034 / 0.388 | No | +0.115 | Yes | −1.00 |
| WI Hong <5% (6a7decac51f2) | 0.007 / 0.0785 | No | +0.070 | No | **+0.08** |
| WI Hong 5-10% (7ae672a0a6db) | 0.031 / 0.096 | No | +0.051 | No | **+0.09** |
| WI Hong 15-20% (e6c093fc7660) | 0.178 / 0.209 | No | +0.023 | No | **+0.25** |
| WI Hong 20-25% (597ed3729e91) | 0.241 / 0.1845 | Yes | +0.052 | No | −1.00 |
| WI Hong 25-30% (1aab3bbe55be) | 0.224 / 0.135 | Yes | +0.084 | No | −1.00 |
| WI Hong ≥30% (aac304cdebf7) | 0.227 / 0.100 | Yes | +0.117 | No | −1.00 |
| KL 30C weather (ff0e79b1b303) | 0.26 / 0.0735 | Yes | +0.181 | No | −1.00 |
| Amsterdam 25C weather (f352b500005a) | 0.13 / 0.45 | No | +0.31 | No | **+0.79** |
| WI Crowley win (7dac557c4c19) | 0.0012 / 0.032 | No | +0.011 | Yes | −1.00 |
| PCE MoM 0.1% (381c3e38473c) | 0.219 / 0.129 | Yes | +0.070 | No | −1.00 |
| PCE MoM 0.2% (b6df56da3754) | 0.594 / 0.57 | Yes | +0.014 | Yes | **+0.72** |
| PCE MoM 0.3% (c07caa45a8dc) | 0.175 / 0.25 | No | +0.065 | No | **+0.32** |
| BoK hold (a8fa1e2ac41d) | 0.38 / 0.69 | No | +0.300 | No | **+2.13** |
| BoK hike 25bps (d102445cc5d5) | 0.60 / 0.32 | Yes | +0.270 | Yes | **+2.03** |
| UMich <49.0 (a5703b36d60a) | 0.334 / 0.177 | Yes | +0.157 | No | −1.00 |
| UMich 49.0-51.9 (fdfd9e781481) | 0.321 / 0.38 | No | +0.059 | Yes | −1.00 |
| GTA VI <10M views (9163ef072ce7) | 0.45 / 0.36 | No | +0.090 | Yes | −1.00 |

**2026-08-30 update (backfilled during a reconcile.py gap-remediation pass;
settled 2026-08-29 04:11Z, RETRO note already covered the settlement
narratively but the same-commit table duty was missed): GTA VI "Extended
Look" <10M-views-day1 (3943730) settled Yes (actual views came in under
10M).** The declined side was No (est No=0.45 vs ask 0.36, fill-price edge
+0.090); actual outcome Yes means the No bet would have **lost, −1.00u** —
the veto
correctly avoided this loss (same shape as BTC touch-$80k and the UMich
49.0-51.9 row). **Totals now 41 realizable trades, 16W/25L, net −12.01u.**
Side split re-summed row-by-row over the full table: **Yes-side unchanged
3W/15L, −10.75u**; **No-side 13W/10L, −1.26u** (adds this loss). Check:
−10.75 + −1.26 = −12.01 ✓.

**2026-08-31 update (DEEP-2026-08-31; both rows settled 04:41Z by the
deep-retro's own resolve.py run, graded same-commit per the DEEP-2026-08-23
rule): two touch-anytime veto rows.** BTC touch-$82k Aug24-30
(cbbeb134c438): model side Yes (est 0.45 vs mid 0.26), fill ask 0.27,
realizable edge +0.180, resolved No — **−1.00u** (another self-modeled
touch-anytime Yes-side counterfactual loss; guessed-vol input, one of the
three pre-registered touch-family gate rows). BTC touch-$80k
created-Aug28-window market (9618a7d0872d): model side No (est No 0.88 vs
mid 0.80), fill ask 0.82, realizable edge +0.060 — sub-0.10, declined on
the pending touch-family gate rather than the numeric boundary, but the
recorded label is outside-view-veto so it is on-ledger, same treatment as
the sub-boundary WI Hong No rows — resolved No, **+0.22u** win. That row
also grades the title-window≠resolution-window discipline note
(proposals.md 2026-08-30 14:12Z) a first win at n=1: the window-quirk
read was the whole edge. **Totals now 43 realizable trades, 17W/26L, net
−12.79u.** Side split: **Yes-side 3W/16L −11.75u; No-side 14W/10L
−1.04u.** Check: −11.75 + −1.04 = −12.79 ✓. Touch-family gate tally after
these: ETH dip-2400 measured-vol WON (est above market, right; RETRO-
20260831-0017), BTC-82k guessed-vol LOST (est above market, wrong), BTC
dip-75000 measured-vol still open (settles Sep 1 04:00Z) — mixed 1-1, so
the pre-registered "market wins all three → fix the vol input" branch
cannot fire; final grade lands with leg 3. Mech-vs-own-vs-market on
cbbeb134c438 (pre-registered on the schedule.json watch item): outcome No
→ market brier 0.0676 < mech v4 0.1024 < own 0.2025 — mech beat own,
nobody beat the market; own stayed 0.19 high even after two independent
~0.3 signals (mech 0.32, market 0.26) — anchoring on the self-model
after outside signals agree is the residual error shape here.

**2026-09-01 update (RETRO-20260901-0025; two rows from this cycle, one
backfilled compliance-gap row from the prior cycle):** Alphabet
3rd-largest-by-market-cap (6317c8ab11b1, settled 2026-08-31T22:15:15Z by
the previous cycle — flagged by `reconcile.py` as a same-commit-duty miss,
fixed here): est 0.62 / mkt 0.942, side No, edge +0.319, resolved Yes
(Alphabet was 3rd) — **−1.00u**. WTI HIGH $95 (fbc6aff9c7f4, settled this
cycle): est 0.048 / mkt 0.20, side No, edge +0.142, resolved No (didn't
touch) — **+0.23u**. WTI HIGH $90 (5ae6bf97d6a9, settled this cycle): est
0.211 / mkt 0.45, side No, edge +0.229, resolved No (didn't touch) —
**+0.79u**. Alibaba best-Chinese-model (a467140e14e7, settled this cycle):
est 0.78 / mkt 0.944, side No, edge +0.163, resolved Yes (Alibaba was #1)
— **−1.00u**. **Totals now 47 realizable trades, 19W/28L, net −13.77u.**
Side split re-summed row-by-row: **Yes-side unchanged 3W/16L, −11.75u**;
**No-side 16W/12L, −2.02u** (adds 2W/2L, net −0.98u this update). Check:
−11.75 + −2.02 = −13.77 ✓. Gold HIGH $4700's revised read (52650469b8d8,
category-bar, nominal edge 0.086 — under the 0.10 numeric boundary) is
excluded from this table per the sub-boundary taxonomy below, same
treatment as Musk wk 200-219 / Zambia. No policy change from this update
(RETRO-20260901-0025 grades the pre-registered touch-family test in full —
3-for-3 vetoed legs in the WTI/Gold Aug batch would have won their
counterfactual, but that argues variance on top of an already-flagged
unvalidated-vol family, not a boundary change at this n).

**2026-09-01 update (RETRO-20260901-0639; 5 rows — 4 sequential veto
snapshots on the same Mythos-class Aug31 market `2487205`, plus GTA VI's
post-trigger veto forecast):** each Mythos row is a separate real-time
book snapshot (re-researched independently as new information arrived),
graded like the BoK pair's original-record-time convention — all four
favored the No side (model diverged from market toward "not released"),
actual outcome No, all four WIN. Mythos No (4aceafc01b6b, Aug25 21:26):
est 0.95 vs ask 0.80, edge +0.150, **+0.25**. Mythos No (e35e582a4d22,
Aug26 17:25, flipped from its Yes=0.30 tracking to the favored No side):
est 0.70 vs implied ask 0.35 (=1−bid_yes 0.65), edge +0.350, **+1.86**.
Mythos No (5d388f8d5585, Aug27 16:23): est 0.65 vs ask 0.54, edge +0.110,
**+0.85**. Mythos No (c69958e0193a, Aug28 09:45, flipped from Yes=0.07):
est 0.93 vs implied ask 0.73 (=1−bid_yes 0.27), edge +0.200, **+0.37**.
GTA VI Yes (ce1727b53bd5, Aug27 16:43, the post-trigger re-veto after
`c6f16acc55d9`'s entry): est 0.55 vs ask 0.32, edge +0.230, actual No →
Yes side **lost, −1.00**.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Mythos No (4aceafc01b6b) | 0.95 / 0.80 | No | +0.150 | No | **+0.25** |
| Mythos No (e35e582a4d22) | 0.70 / 0.35 | No | +0.350 | No | **+1.86** |
| Mythos No (5d388f8d5585) | 0.65 / 0.54 | No | +0.110 | No | **+0.85** |
| Mythos No (c69958e0193a) | 0.93 / 0.73 | No | +0.200 | No | **+0.37** |
| GTA VI trailer (ce1727b53bd5) | 0.55 / 0.32 | Yes | +0.230 | No | −1.00 |

**Totals now 52 realizable trades, 23W/29L, net −11.44u.** Side split
re-summed row-by-row over the full table: **Yes-side 3W/17L, −12.75u**
(adds GTA VI's loss); **No-side 20W/12L, +1.31u** (adds the 4 Mythos
wins, +3.33u) — the No side crosses into cumulative positive territory
for the first time. Check: −12.75 + 1.31 = −11.44 ✓. This widens the
existing Yes/No asymmetry flagged since 2026-08-26/27 for a future deep
retro; not decided here (hourly cycles extend the table, they don't rule
on it).

**2026-09-01 update (RETRO-20260901-1350; 8 rows, AAA gas-price
touch-anytime set, all settled this tick).** All 8 legs (event 769509,
first recorded 2026-08-17 as `outside-view-veto`, self-model + uniform
large disagreement, 0 bets) resolved No — the national-average price
never touched any of the 8 thresholds. Model favored No on every leg
(est 0.01-0.035 vs live book 0.05-0.19); a clean directional sweep,
though highly correlated (one price path drove all 8 legs, not 8
independent draws) and still resting on the unvalidated 4-weekly-point
sigma the original note flagged. Fill reference = best_bid_at_record (ask
where no bid was posted); CF profit = 1/(1−ref) − 1 on the No side.

| Row | est vs ref | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Gas $3.90 Low (e2cbca37fe88) | 0.035 / 0.18 | No | +0.145 | No | **+0.22** |
| Gas $3.70 Low (9dffc25cddd9) | 0.01 / 0.04 | No | +0.030 | No | **+0.04** |
| Gas $3.50 Low (cca60b062716) | 0.01 / 0.01 | No | +0.000 | No | **+0.01** |
| Gas $3.25 Low (e45e186476b0) | 0.01 / 0.12* | No | +0.110 | No | **+0.14** |
| Gas $3.00 Low (38c726c1c695) | 0.01 / 0.01 | No | +0.000 | No | **+0.01** |
| Gas $4.25 High (d59e9243dfb4) | 0.019 / 0.09 | No | +0.071 | No | **+0.10** |
| Gas $4.50 High (59f65e95ed5e) | 0.01 / 0.10 | No | +0.090 | No | **+0.11** |
| Gas $4.75 High (9140e7f850f4) | 0.01 / 0.16* | No | +0.150 | No | **+0.19** |

\* no bid posted at record time; ask used as the conservative reference.

**Totals now 60 realizable trades, 31W/29L, net −10.62u.** Side split
re-summed row-by-row: **Yes-side unchanged 3W/17L, −12.75u**; **No-side
28W/12L, +2.13u** (adds this batch's +0.82u). Check: −12.75 + 2.13 =
−10.62 ✓. Second touch-family family (after WTI/Gold's 3/3
vetoed-would-have-won, RETRO-20260901-0025) where the self-model's
*direction* beat the market despite an unvalidated sigma — flagged for
the next deep retro's cross-family self-model review, not a policy
change at this n (correlated legs, still no sourced daily-price series).
No ranking/veto-boundary edit; AAA gas-price touch-anytime stays
outside-view-veto/forecast-only.

**2026-09-01 update (LIGHT tick 22:xxZ; 5 rows, the Mythos-class
"by-date" nested-deadline family, all settled this tick after the
official Anthropic announcement of Claude Mythos 5.1 / Fable 5.1
propagated on-chain).** Same underlying fact as the 4-row Mythos-No
batch already in this table (RETRO-20260901-0639, all 4 WON), but these
are the LATER snapshots — checked Aug29 through the actual release day —
and this time the model favored No on every leg and **all 5 LOST**: the
release the rumor pointed at actually happened Sep1, hours after the
last WebSearch check on several of these legs came back "no confirmed
announcement." Not 5 independent confirmations — one correlated signal
(same underlying release, five deadline windows) — but a clean reversal
of the earlier batch's direction as the true event got closer.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Mythos by-Sep9 No (1f20cadb2b53) | 0.85 / 0.27 | No | +0.580 | Yes | −1.00 |
| Mythos by-Sep1 No (720781176db9) | 0.20 / 0.68 | No | +0.480 | Yes | −1.00 |
| Mythos by-Sep1 No (237402dd3f1e) | 0.06 / 0.31 | No | +0.250 | Yes | −1.00 |
| Mythos exact-Sep1 No (4c648c2e6afb) | 0.03 / 0.29 | No | +0.260 | Yes | −1.00 |
| Mythos by-Sep2 No (f9a6e09224dd) | 0.12 / 0.55 | No | +0.430 | Yes | −1.00 |

(720781176db9 and 237402dd3f1e are sequential re-checks of the SAME
by-Sep1 market, same convention as the earlier Mythos No sequence —
both count as separate row-time snapshots, per the existing table
practice.) **Totals now 65 realizable trades, 31W/34L, net −15.62u.**
Side split re-summed row-by-row over the full table: **Yes-side
unchanged 3W/17L, −12.75u**; **No-side 28W/17L, −2.87u** (adds this
batch's 0W/5L, −5.00u — the No side's first net-negative turn since the
AAA gas batch pushed it positive). Check: −12.75 + −2.87 = −15.62 ✓.
Full Mythos-rumor-family lifetime tally (9 rows, both batches): 4W/5L,
net +3.33−5.00 = **−1.67u** — betting real money against this rumor
would have lost money over the family's full life, reinforcing (not
contradicting) the fact-finality gate: zero capital was ever actually
risked on any of these 9 rows, exactly because "unconfirmed rumor" stays
vetoed regardless of the model's confidence, and the model's confidence
here would have been wrong more often than right by the end. No
veto-boundary change — this is the gate working as designed, not a
reason to loosen it. Concrete estimation lesson, encoded below in
§Estimation method (same-day-deadline WebSearch-timing sub-bullet): a
single WebSearch check earlier in the day on a "by end-of-date-X"
deadline market, with an active rumor of an imminent event, is weak
evidence for No if the deadline hasn't fully elapsed — three of these
five legs were checked hours before the actual announcement landed
later the SAME day, and "no confirmation as of this morning's search"
was read as informative when it was mostly a search-timing artifact.
Re-check same-day deadlines close to the actual cutoff before
finalizing a rumor-based No, don't rely on one AM check.

**2026-09-02 update (00:15Z FULL cycle: box-office Aug31 gross-threshold
pair CLOSED, pre-registered 2026-08-22, watch item in schedule.json).**
The Odyssey/Spider-Man BND domestic-gross family settled: Odyssey missed
$570M (d48834ed8f41), Spider-Man BND missed $900M but landed in
[800M,900M) — the sibling bracket for that exact range (e9f9221a3afb)
WON as a forecast. Four `outside-view-veto` rows from this family enter
the counterfactual ledger:

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Odyssey ≥570m (d48834ed8f41) | 0.08 / 0.14 | No | +0.057 | No | **+0.16** |
| Spider-Man ≥900m (1f552d2c510f, Aug22 check) | 0.25 / 0.336 | No | +0.085 | No | **+0.50** |
| Spider-Man ≥900m (1e889dd4dd33, Aug25 update) | 0.15 / 0.092 | Yes | +0.058 | No | −1.00 |
| Spider-Man <900m (9f40def4f61c) | 0.85 / 0.915 | No | +0.060 | Yes | −1.00 |

(e9f9221a3afb, the 800-900m bracket itself, was a genuine market-agrees
no-edge read — 0.90 vs ask 0.86 — not a veto row, so it doesn't enter
this table.) Net this batch: **−1.34u** (2W/2L). **Totals now 69
realizable trades, 33W/36L, net −16.96u.** Side split re-summed: **Yes-side
3W/18L, −13.75u** (adds this batch's 0W/1L, −1.00u); **No-side 30W/18L,
−3.21u** (adds this batch's 2W/1L, +0.66u−1.00u=−0.34u). Check: −13.75 +
−3.21 = −16.96 ✓.

Grading the two things schedule.json's watch item asked for: (1) **the
veto boundary** — this batch's ledger P&L is net negative (−1.34u), so
the veto continues to look correct on net even though two of the four
counterfactual sides won; no change to the standing box-office
self-model veto. (2) **the trend-extrapolation method itself** — on
*directional* accuracy it was clean: all four legs' Aug22-25 point
projections (Odyssey ~544M, Spider-Man ~875-897M) correctly bracketed
where the film actually landed (Odyssey short of 570M, Spider-Man inside
[800M,900M)). But the two Aug25-update legs (1e889dd4dd33, 9f40def4f61c)
lost as counterfactual trades anyway, because by Aug25 the market itself
had already converged to 91-92%/90-92% confidence in the correct
bracket — the model's residual disagreement with an already-converged
market was noise, not edge, even though the model's own point estimate
was directionally fine. Lesson for this family: a trend-extrapolation
edge claim late in the window, against a market that has already priced
in the same trend data, deserves more skepticism than the same claim
made earlier — the method's forecasting skill and its counterfactual
tradeability are not the same thing once the market catches up. No
playbook rule change; this reinforces (not contradicts) routing box-office
self-models through the veto regardless of claimed edge. Item closed, no
further grading duty.

**2026-09-02 update (RETRO-20260902-0212, LIGHT tick; 2 rows, first
settled instances of the transfer-window narrative/negotiation-speculation
sub-shape — soccer-transfer / news-transfer category, no mechanical
benchmark available for "will X join/stay" questions).** Enzo Fernandez
stay-at-Chelsea (`dc81cc744a86`, est P(stay)=0.60 vs ask 0.312, Yes side)
resolved No (he left, to Man City) — the public "Enzo is a Chelsea player"
narrative signal read wrong underneath a quietly-progressing deal, **lost,
−1.00u**. Enzo Fernandez join-Man-City (`e481c796f8d1`, Aug27 19:22Z
snapshot, est No=0.25 vs ask 0.17, No side) resolved Yes (he joined) —
called before the story firmed, **lost, −1.00u**.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Enzo stay-Chelsea (dc81cc744a86) | 0.60 / 0.312 | Yes | +0.288 | No | −1.00 |
| Enzo join-ManCity (e481c796f8d1) | 0.25 / 0.17 | No | +0.080 | Yes | −1.00 |

Net this batch: **−2.00u** (0W/2L). **Totals now 71 realizable trades,
33W/38L, net −18.96u.** Side split re-summed: **Yes-side 3W/19L, −14.75u**
(adds this batch's Chelsea loss); **No-side 30W/19L, −4.21u** (adds this
batch's Man City loss). Check: −14.75 + −4.21 = −18.96 ✓. n=2, 0W/2L —
consistent with (not yet a distinct named instance of) the standing
outside-view-veto discipline; too small to write a dedicated rule. Worth
noting: the 4 later join-Man-City snapshots that went market-agrees
instead of chasing the narrative (once the book itself converged past
~0.85 with real depth) all landed on the winning side — downgrading from
a confident narrative read to market-agrees as the book firms is what
kept most of this family off the losing side of the ledger.

**2026-09-02 update (RETRO-20260902-1814, FULL cycle; 4 rows, Gemini
Flash 3.8+ leak/rumor family fully settled).** All four sequential
outside-view-veto snapshots on "next Gemini Flash release by/on Sep2"
settled: the model WAS released, so every No-side veto lost as a
counterfactual trade. Same rumor-convergence shape as the Mythos family
(DEEP-2026-09-01, 22:xxZ) — unofficial leaks (codename "skimaki"/Jetski)
converged on the correct date well before official confirmation, and the
market priced that correctly while the fact-finality gate correctly
declined to bet against it:

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Gemini Flash by-Sep2 No (4a680e8bca1e, initial check) | 0.13 / 0.655 | No | +0.53 | Yes | −1.00 |
| Gemini Flash by-Sep2 No (a554a9f53079, re-check) | 0.50 / 0.675 | No | +0.19 | Yes | −1.00 |
| Gemini Flash by-Sep2 No (8f8fa61af2a2, re-check) | 0.58 / 0.79 | No | +0.22 | Yes | −1.00 |
| Gemini Flash on-Sep2 No (655167550ada, sibling) | 0.58 / 0.775 | No | +0.21 | Yes | −1.00 |

Net this batch: **−4.00u** (0W/4L). **Totals now 75 realizable trades,
33W/42L, net −22.96u.** Side split re-summed: **Yes-side unchanged 3W/19L,
−14.75u**; **No-side 30W/23L, −8.21u** (adds this batch's 0W/4L, −4.00u).
Check: −14.75 + −8.21 = −22.96 ✓. Est climbed 0.13→0.50→0.58→0.58 as
corroborating leaks piled up (correctly applying the Mythos-episode
same-day-deadline lesson — later checks, not one AM read), but even the
final 0.58 stayed well below the market's 0.775-0.79, and the market was
right. Reinforces, does not contradict, the standing gate: zero capital
was ever at risk on any of these four rows, exactly because "unconfirmed
leak, however convergent" stays vetoed regardless of claimed edge. The
two same-cycle crypto-touch settlements (BTC $77.5k, ETH $2400, both WON)
carried ~0 realizable edge at record time (est essentially at the book)
and are not counterfactual trades — no ledger duty, no touch-family n
change.

**2026-09-02 update (compliance-gap backfill, DEEP-2026-09-02 22:xxZ
reconcile.py FAIL remediation, same-commit per the Coverage weld rule;
2 rows, both crypto-brackets touch-anytime, settled earlier but missed
by this table until now).** ETH $2600-in-August touch (`9f1fedaa0386`,
settled 2026-09-01T04:40:58Z): self-modeled GBM barrier-touch est
P(Yes)=0.48 vs mkt mid 0.6855, model favors No (No prob 0.52) vs No ask
0.326 (=1−best_bid 0.674), edge +0.194; actual result No (didn't touch)
— model's No side **WINS**, fill ask 0.326, **+2.07u**. BTC
above-$76k-on-Sep2 (`d16f83d68630`, settled 2026-09-02T16:23:22Z):
guessed-vol lognormal est P(Yes)=0.838 vs mkt mid 0.945, model favors No
(No prob 0.162) vs No ask 0.06 (=1−best_bid 0.94), edge +0.102; actual
result Yes (stayed above) — model's No side **LOSES**, **−1.00u**.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| ETH $2600 Aug touch (9f1fedaa0386) | 0.52 / 0.326 | No | +0.194 | No | **+2.07** |
| BTC >$76k Sep2 (d16f83d68630) | 0.162 / 0.06 | No | +0.102 | Yes | −1.00 |

Net this batch: **+1.07u** (1W/1L). **Totals now 77 realizable trades,
34W/43L, net −21.89u.** Side split re-summed row-by-row: **Yes-side
unchanged 3W/19L, −14.75u**; **No-side 31W/24L, −7.14u** (adds this
batch's 1W/1L, +2.07u−1.00u=+1.07u). Check: −14.75 + −7.14 = −21.89 ✓.
Both rows are guessed/self-modeled-vol touch-family members already
covered by the CLOSED ruling below (unvalidated-method, forecast-only
regardless of edge) — no policy change, this batch only closes a
same-commit-duty gap flagged by `reconcile.py`.

**2026-09-03 update (LIGHT tick settlement, retro RETRO-20260903-0633):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Astra by-Sep2 (2daa083970d8) | 0.10 / 0.185 | No | +0.028 | No | **+0.15** |

Net this batch: **+0.15u** (1W/0L). **Totals now 78 realizable trades,
35W/43L, net −21.74u.** Side split re-summed row-by-row: **Yes-side
unchanged 3W/19L, −14.75u**; **No-side 32W/24L, −6.99u** (adds this
batch's 1W/0L, +0.15u). Check: −14.75 + −6.99 = −21.74 ✓. Smallest edge
yet added to this table (0.028, under min_edge 0.04) — the veto's own
timeline-rumor read was correct, but n=1 at this edge size is not
evidence for lowering any floor.

**2026-09-03 update (FULL cycle 17:20Z, retro RETRO-20260903-1720; 3
same-day weather-Gaussian rows):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Singapore 32C Sep3 (e48e803b2103) | 0.233 / 0.07 | Yes | +0.143 | No | −1.00 |
| Shanghai 32C Sep3 (3cf21078d1a0) | 0.049 / 0.355 | No | +0.271 | No | **+0.47** |
| Singapore 33C Sep3 (32d046d6981c) | 0.323 / 0.845 | No | +0.497 | Yes | −1.00 |

Net this batch: **−1.53u** (1W/2L). **Totals now 81 realizable trades,
36W/45L, net −23.27u.** Side split re-summed row-by-row: **Yes-side
3W/20L, −15.75u** (adds −1.00u); **No-side 33W/25L, −7.52u** (adds
+0.47u−1.00u=−0.53u). Check: −15.75 + −7.52 = −23.27 ✓. Weather-Gaussian
class now 2W/3L, −1.74u. Ruling: the two losses were recorded at 10:22 and
12:18 local time on the resolution day with the next-day sd=1.2C applied
to a half-observed day (the 33C bucket was the point forecast's own mean;
the market had it at 0.845, the model 0.323). **Same-day weather rows must
condition on the observed partial-day max (open-meteo hourly, `past_days=1`,
or `current`) with sd 0.6C after local noon; if that fetch fails, no
forecast at all.** Next-day rows keep sd=1.2C. Category stays no-bet.

**2026-09-03 update (LIGHT tick 22:04Z, retro RETRO-20260903-2204; 2
next-day weather-Gaussian rows, one event):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Ankara 30C Sep3 (aac6d9fc2b4a) | 0.287 / 0.565 | No | +0.273 | Yes | −1.00 |
| Ankara 31C Sep3 (428600857382) | 0.140 / 0.375 | No | +0.220 | No | **+0.56** |

Net this batch: **−0.44u** (1W/1L). **Totals now 83 realizable trades,
37W/46L, net −23.71u.** Side split re-summed row-by-row: **Yes-side
unchanged 3W/20L, −15.75u**; **No-side 34W/26L, −7.96u** (adds −0.44u).
Check: −15.75 + −7.96 = −23.71 ✓. Weather-Gaussian class now 3W/4L,
−2.18u; next-day sub-class 2W/2L. Ruling: recorded 05:22 local (pre-dawn),
so functionally next-day and untouched by the same-day rule above. The
market put 0.94 on two adjacent buckets (implied sd ≈0.55C vs the model's
1.2C) and was right; at about six settled next-day rows, test the
open-meteo ensemble spread per city against the fixed sd. No change now.

**2026-09-04 update (FULL cycle 04:13Z, retro RETRO-20260904-0413; 2 rows,
GTA VI Extended Look <20M-views week-1 market, two of its four sequential
snapshots):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| GTA VI <20M wk1 (b5c5c134d7cb) | 0.55 / 0.60 | No | +0.030 | No | **+1.38** |
| GTA VI <20M wk1 (e398cebab2e6) | 0.30 / 0.82 | No | +0.510 | No | **+4.26** |

Net this batch: **+5.64u** (2W/0L). **Totals now 85 realizable trades,
39W/46L, net −18.07u.** Side split re-summed row-by-row: **Yes-side
unchanged 3W/20L, −15.75u**; **No-side 36W/26L, −2.32u** (adds this
batch's 2W/0L, +5.64u). Check: −15.75 + −2.32 = −18.07 ✓. Both wins are
late, well-anchored trend-extrapolation reads on a market with an actual
climbing view count (own family narrative in the retro), the mirror image
of the two other sequential snapshots on this same market that guessed
without a dated figure and both lost as forecasts — the veto still
correctly avoided capital risk on a narrative/trend-extrapolation class
that is net-negative lifetime even after these two wins.

**Operator-machine 03:40Z cycle (RETRO-20260904-0340), merged by the operator 2026-09-04 after the two runners diverged:** its e398cebab2e6 row is the same row as in the 04:13Z table above and is counted once in the totals. It pre-registered sub-class
`countable-metric` (any veto row whose note cites a dated primary count on
a live countable metric: views, downloads, followers, on-chain counts):
now 1W/0L, +4.26u; grade for a carve-out at n≥3 settled rows, veto
unchanged until then. Rows without a dated count stay narrative class.

**Cumulative-count anchor rule (DEEP-2026-09-04, from the four settled
snapshots above plus b3fbd3c3eef7/944d8e5fc4d0):** a forecast on a
cumulative-count market (views, downloads, signatures, cumulative sales)
requires a DATED count plus an observed per-day pace, exactly as same-day
weather rows require the observed partial-day max. The settled split is
stark: the two snapshots with no dated figure scored brier 0.3025
(b5c5c134d7cb, "coin-flip with a fig-leaf of numbers") and 0.7225
(b3fbd3c3eef7, est 0.85 on <20M while the count was climbing through
17M — it followed the market's re-pricing and called it confirmation);
the one snapshot with a dated anchor (~17M at day 5-6, ~3.4M/day) scored
0.09 (e398cebab2e6). If no dated count is findable, record NO forecast
(skip reason `no-anchor`) rather than a number — an unanchored estimate
here contaminates calibration stats the same way a half-observed day did
in weather. Market-agrees re-pricing is NOT an anchor: on a trending
count the market re-pricing toward your prior is what being late looks
like.

**Pace must be observed, not inferred (RETRO-20260926-2015, MrBeast
v9QtM6qnG50 wk1).** The 16:19Z Sep25 60-70M read (92a9d80fc3c3, 0.59 vs
0.3835) had a count (RYD 65.6M) but INFERRED the pace (~1.6M/day from a
day-2 summary); the first two dated reads 4h apart then showed 0.30M/h
(~7M/day) and the market's 70-80M lean won. The pace in "dated count plus
observed pace" means two dated reads of the same source at least ~3h
apart; with one read, the row is still `no-anchor`/veto territory. Also
measured: RYD (returnyoutubedislikeapi) lagged the YouTube watch page by
only ~19k views at 20:20Z Sep25, so a RYD read stamped with its fetch time
counts as a dated read when YouTube 429s.

**Pace must be diurnal-matched (RETRO-20261010-1815, MrBeast
plN7JMbadRg wk1).** At 08:19Z Oct10 I projected the 02-08Z RYD pace
(0.58M/h, US night) forward into 08-16Z (US Saturday morning) and
flipped from 215+ to 207-215. The count finished 215-223, the market's
side, and that flip cost +0.17/+0.18 dBrier on both rows. The two
earlier reads, taken before the flip, had been right. When you project
a count to a deadline, do not extrapolate the most recent window's pace
if that window was in a different part of the US day than the window
being projected. Use the pace from the same UTC hours a day earlier,
scaled by the multi-day decay, or the trailing 24h average. A decline
that only shows up in a trough window is not evidence of decay.
Second settled instance (RETRO-20261014-2215, MrBeast Gaming h8VE9_aHd94
day4 43-44M): two trough-only reads already projected mid-bracket (~43.46M).
The rule kept me off the No side at 0.059 (CF -5.00), but my 0.90 shading
still lost dBrier to the market's 0.967 (+0.009). When trough-only pace
already lands mid-bracket, sit near the market rather than shading toward
the tail the trough cannot tell you about.
Third settled instance (RETRO-20261019-1815, MrBeast RE3_PGwDwhw day2
92-96M): the 10:18Z read projected the 08-10Z acceleration and leaned
96-100 at 0.33 vs ask 0.28; the rule kept me off it (CF -5.00, saved).
The 12:20Z read centred 93.6-94.3M inside 92-96, yet I shaded 0.93 vs
the market's 0.99 (+0.005 dBrier, all four rows lost to the mid).
Concrete form of "sit near the market": when the projected centre is at
least 1.5 sd inside both bracket edges, own p on that rung stays within
0.03 of the mid unless a fresh read shows a pace break.
Fourth settled instance (RETRO-20261021-1813, MrBeast RE3_PGwDwhw day4
113-115/115-117): two dated RYD reads put the centre on the 115 edge; I sat
within 0.01 of both mids (0.42/0.415, 0.55/0.555), outcome 115-117, net dBrier
~0.000. Straddle case confirms: on an edge, stay at the mid.

**2026-09-04 update (LIGHT tick 06:29Z, settled by resolve.py; 4 rows,
two OpenAI Astra release-timeline markets, two sequential snapshots
each):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Astra by-Sep3 (925eb1c697f9) | 0.20 / 0.87 | No | +0.660 | No | **+6.14** |
| Astra on-Sep3 (b1d2b955da88) | 0.18 / 0.8305 | No | +0.632 | No | **+4.32** |
| Astra by-Sep3 re-check (cfda85a4abde) | 0.15 / 0.885 | No | +0.730 | No | **+7.33** |
| Astra on-Sep3 re-check (a8d12b4831b4) | 0.80 / 0.944 | No | +0.140 | No | **+15.67** |

Net this batch: **+33.46u** (4W/0L). **Totals now 89 realizable trades,
43W/46L, net +15.39u** — the ledger's first-ever positive cumulative
total. Side split re-summed row-by-row: **Yes-side unchanged 3W/20L,
−15.75u**; **No-side 40W/26L, +31.14u** (adds this batch's 4W/0L,
+33.46u). Check: −15.75 + 31.14 = 15.39 ✓. Both markets resolved No
(Astra did not clear each market's specific by/on-Sep3 public-access
bar in time) against books priced 83–94c Yes; the fact-finality gate
(DEEP-2026-08-30) correctly avoided capital on all four snapshots but
this is the single largest realizable-edge miss in the table by a wide
margin, driven almost entirely by a8d12b4831b4's 6c No ask on a
near-certain-looking Yes book. n=2 distinct markets (4 snapshots) is
not grounds to loosen the gate — the same family's earlier by-Sep2 leg
(2daa083970d8, not in this table, already lost as a straight forecast)
and the wider Yes-side 3W/20L record argue the opposite direction on
timeline-rumor markets generally; full grading in
RETRO-20260904-0629.

**Touch-family gate CLOSED (DEEP-2026-09-01; pre-registered 2026-08-28
21:35Z, all 3 legs settled):** leg 3 BTC dip-$75k (753366c2ea8e,
measured-vol, est 0.38 vs mid 0.315) LOST — final record ETH dip-2400
measured-vol WON (brier 0.040 vs mkt 0.106), BTC-82k guessed-vol LOST
(0.203 vs 0.068), BTC dip-75k measured-vol LOST (0.144 vs 0.099).
Aggregate brier: own 0.129 vs market 0.091 — the market won the family.
All three own reads sat above market and 2 of 3 resolved No, but the leg
with the largest above-market gap won, so the vol-overstatement signature
is suggestive, not confirmed. **Ruling:** the crypto touch/reflection
family stays `unvalidated-method` forecast-only — no bets. Guessed-vol
inputs are RETIRED from this family: any future touch forecast must use
measured realized vol or market-implied vol from an adjacent ladder rung
(guessed-vol is 0W/1L live, and the superseded guessed-vol ETH row
d2431685b1a3 won with a brier 2.3× worse than its measured-vol
replacement — it has never outperformed the market or its measured
sibling). Re-grade the family at n≥6 settled measured-vol rows (currently
1W/1L: edd6af85d6a6 W, 753366c2ea8e L).

**2026-09-21 12:24Z update (RETRO-20260921-1224; re-grade counter pinned,
family shade dropped):** RETRO-20260921-1025 counted the family by label
(every crypto-touch `unvalidated-method` row) and reached "n=5, re-grade at
the next settlement". Three of those rows (`07a247cac126` guessed sigma,
`a28637cb4026` swept sigma, `3acf7b55a29f` no model) are outside the
pre-registration above. The counter, from now on:

- A row counts only if its note quotes a measured realized vol or a
  market-implied vol with a named, dated source. Labels do not count rows.
- Sibling rungs of one asset and one window, recorded from the same vol
  input, count as ONE decision (score them all, count them once).
- A row recorded with the barrier within 0.5% of spot is listed but carries
  no weight.

Tally at this commit: 5 settled measured rows, 4W/1L, own Brier sum 0.4786
vs market 0.6005 (own ahead by 0.1219): `edd6af85d6a6` W, `753366c2ea8e` L,
`fde4324641b4` W (0.03% gap, no weight), `bad4649e1e7a` + `423dd881047b` W
(one decision, BTC reach Sep). That is 4 decisions, 3 informative. Open
measured rows, all settling by 2026-10-01 04:00Z: `854536ded8be`,
`942876f92dd8`, `10f71ccecca3`, `cbc8303dc2a8`. The re-grade runs in the
retro of the tick that settles the 6th measured row, and splits reach rows
from dip rows (a month of rising prices flatters every reach read).

Shade: a touch row records the `touch.py` output at the measured vol. The
"family's above-market record" shade toward the 0.75x-vol reading is
dropped: on measured rows the above-market reads went 4 for 5, the shade
cost 0.070 (`423dd881047b`) and 0.015 (`bad4649e1e7a`) Brier, and a shaded
row no longer tests the method the re-grade is about. A shade needs a
row-specific reason in the note. Forecast-only ruling unchanged: no bets.

**2026-10-02 22:15Z (RETRO-20261002-2215): tally.** GOOGL HIGH $360
`142619e6dbae` (0.28 vs mid 0.345) and AAPL HIGH $340 `d7e66de49d0c` (0.22 vs
0.255) both settled no-touch and beat the mid (-0.041, -0.017).
equity-touch is now n=8, dBrier +0.0173: still forecast-only. The GOOGL row
blended in the 0.75x-vol reading and gave a row-specific reason (the
premarket print was stale). It helped this once (n=1), so the
no-default-shade rule stands. Stale-mid rule (any single-stock row): when
the live CLOB book contradicts gamma's bestBid/ask mid by 0.10 or more, the
note records the live mid explicitly ("live mid X"). Evidence: the GOOGL
$340-345 close band `8de7ff599222` was graded against a stale 0.725 while
the live book was 0.36/0.74.

**2026-09-25 22:13Z (RETRO-20260925-2213): an inferred open is not a
measured input.** Single-stock touch rows record `touch.py` from the last
close, or from an actually quoted premarket print. An open inferred from
index futures x beta goes in the note as "shade view: X", never into
est_prob. Evidence: PLTR HIGH $195 `a468e40297ae` recorded 0.74 (between
0.678 from the close and 0.864 from an NQ-beta open), no touch, dBrier
+0.293 vs mid 0.505; the overlay alone cost 0.088. A shade grounded in a
measured print (SPY LOW $760 `23a99c8fe4e8`, ES overnight + RTH-only
window, 0.118 -> 0.08) helped by 0.0075. equity-touch now n=2, dBrier
+0.163: forecast-only, no bets.

**2026-09-21 20:44Z update (RETRO-20260921-2044; far-barrier split added):**
`8d1eb46b7c32` (ETH reach $2,800, own 0.25 vs mid 0.155) settled WON, dBrier
-0.1515. Listed, NOT counted: its note sweeps sigma 50-90%, no measured
input. Tally unchanged (5 rows, 4 decisions, 3 informative). Hindsight
`touch.py` on the record-date inputs at measured Binance vol (30d 0.454,
14d 0.491) gives 0.11-0.14, UNDER the 0.155 mid, on a 15% barrier that fell
to one +7% day: the driftless tool has no jump term and the book prices far
barriers above it (same gap on open `cbc8303dc2a8`). n=1, no ruling change.
The re-grade therefore splits rows twice: reach vs dip, AND barrier gap at
record time under 10% vs 10% or more. Open measured rows now:
`854536ded8be`, `942876f92dd8`, `10f71ccecca3`, `cbc8303dc2a8`,
`86415cf1e27f`. `395a07f3f815` (ETH $3,200, guessed vol) is outside the
counter.

**2026-09-23 08:10Z (RETRO-20260923-0810): WTI September ladder listed.**
The five-rung WTI ladder (`18672a24a234`, `98134efdddcf`, `0ad60d107c54`,
`52fac91e76d7`, `41c92e76901c`) quotes a market-implied vol with a named,
dated source (OVX 57.49, FRED OVXCLS Sep 16), so it qualifies; one asset,
one window, one vol input makes it ONE open decision, counted when its
last rung settles (~Oct 1). Settled so far: LOW95 W and LOW90 W, both
above market, dBrier sum -0.0660. Tally of settled decisions unchanged.

**2026-09-23 15:0xZ RE-GRADE (RETRO-20260923-1500; 6th and 7th measured
rows settled):** `820604783edf` (ETH dip $2,700, own 0.90 vs mid 0.94,
gap 0.82%) and `c07c05bc24af` (BTC dip $85k, own 0.93 vs mid 0.9415, gap
0.52%) both WON; both unshaded, measured Binance 30d vol, two assets so
two decisions. Tally: 7 rows, 6 decisions, 5 informative (`fde4324641b4`
carries no weight). Row Brier own 0.4935 vs market 0.6074 (own ahead
0.114). Splits:
- Dip (4 decisions): own 0.1993 vs mkt 0.2118, own ahead 0.0125, but the
  market was closer on 3 of 4; `edd6af85d6a6` alone carries the lead.
- Reach (1 decision, the BTC Sep 82.5k/85k pair, both shaded): own 0.2941
  vs mkt 0.3956. One correlated decision in a rising month.
- Far barrier (gap 10% or more): no counted rows. Untested.
- Direction: own above market 3 times (2W/1L), below market 2 times
  (both resolved Yes, market closer both times).
Decision-weighted (sibling rows averaged): own 0.3464 vs mkt 0.4096, but
only 2 of 5 informative decisions beat the market.
**Ruling:** stays `unvalidated-method`, forecast-only, no bets. The
aggregate lead rests on two decisions (`edd6af85d6a6` and the reach
pair); the other three went to the market, and the far-barrier and
multi-decision reach cells are empty. Pre-registered NOW, so the next
grade cannot be post hoc: promote to a bettable edge class only if, at
10 or more informative decisions, (a) decision-weighted Brier beats the
market in BOTH the reach and the dip split with at least 3 decisions
each, and (b) own beats the market on at least 60% of decisions. Until
then keep recording every scan-surfaced qualifying row, unshaded, and
keep splitting near/far barrier.

**2026-09-24 DEEP re-grade (8th and 9th measured rows; settled by the
deep retro's own resolve run at ~04:3xZ, so no hourly retro graded
them).** `6c1236ca11fe` (BTC dip $83k on Sep 23, own 0.24 vs mid
0.2055) and `8a4bb9cfde9c` (ETH dip $2,600 on Sep 23, own 0.09 vs mid
0.085) both LOST (no dip); both unshaded, measured Binance 30d vol, two
assets so two decisions, both near-barrier dips (gap ~3%). Market closer
on both (row dBrier +0.0154 / +0.0009). Tally: 9 rows, 7 informative
decisions; own beats the market on **2 of 7**. Dip split: 6 decisions,
own closer on 1. Direction pattern: own ABOVE market on all 4 intraday
dip reads since 09-17 and the market was closer on 3 of them — the
unshaded 30d-realized-vol reflection read slightly overstates same-day
touch odds (n=4, pattern only, not a rule).
**Bar arithmetic, stated so nobody grades it hopefully later:** at 10
informative decisions the best possible own-closer count is 5/10 = 50%,
below the 60% bar in (b). The 10-decision promotion is now unreachable;
it would take 13 straight own-closer decisions to reach 60% at any n.
**Ruling:** stays `unvalidated-method`, forecast-only, indefinitely. Keep
recording scan-surfaced rows (cheap, and the WTI ladder decision is
still open ~Oct 1), but do NOT spend research priority on generating new
touch rows — priority 1 "feed the measured-row counter" (15:00Z
2026-09-23 funnel note) is retired. The family matches the market; it
does not beat it.

**2026-09-25 12:0xZ tally (RETRO-20260925-1207; 10th and 11th measured
rows).** `4cf126698087` (SOL reach $120 Sep, own 0.83 vs mid 0.808, gap
2.2%, CoinGecko 31d vol) and `e9398115e4ad` (BTC reach $85k from Sep 23,
own 0.91 vs mid 0.83, gap 0.60%, Binance 30d vol) both WON, both
unshaded, own closer on both (dB -0.0080 / -0.0208). Two assets, and the
BTC market has its own window (created Sep 23), so two decisions. Tally:
11 rows, 9 informative decisions, own closer on 4 of 9. Reach split: 3
decisions, own closer on all 3; dip split: 6 decisions, own closer on 1.
All three reach wins came in a rising month and all near-barrier, so the
split is the pattern to watch, not a licence. Bar arithmetic corrected:
the "13 straight" figure above was computed at 2 of 7. At 4 of 9, four
more own-closer decisions in a row reach 8/13 = 62%, so criterion (b) is
reachable again; criterion (a) still needs the dip split to beat the
market on decision-weighted Brier. Ruling unchanged: forecast-only
"indefinitely" stands until a deep retro re-grades against the full
pre-registered bar, and a reach-only slice never re-opens it.

**2026-10-01 04:45Z tally (RETRO-20261001-0445; September month-end
batch plus three ungraded Sep 21-27 weekly rows).** 15 new decisions,
own closer on 8. Running: **12 of 24 (50%)**; reach 7 of 12, dip 4 of 11,
far barrier 5 of 5 (first counted far rows). Counting choices, fixed
for later grades: one asset + one record time + one vol input is one
decision even when the rungs point opposite ways (ETH reach $3,200 + dip
$2,500 is one far decision, left out of the reach/dip split); a mid
from a placeholder book (bid 0.01, spread 0.14 or more: DOGE $0.15 and
$0.20, XRP $2.80) carries no weight. Every row resolved No in a
range-bound month-end, so the split is one draw: own above the mid lost
7 of 7 (all near barriers, 3-9 day windows, 30d vol 0.41-0.69 while the
quoted 6d realized was ~0.2), own below the mid won 8 of 8. Bar (b) now
needs 6 straight own-closer decisions. Ruling unchanged: forecast-only.

**2026-10-02 05:03Z tally (RETRO-20261002-0503; 2 more measured
decisions).** `afc6b3e66078` (BTC dip $83k Oct 1, own 0.47 vs mid 0.64,
gap -1.05%, window 18.2h) LOST and `bcf51c6612b2` (BTC reach $86k Sep
28-Oct 4, own 0.40 vs mid 0.355, gap +2.53%, window 3.76d) WON; both
near-barrier, both recorded at the 7-day regime-lag read, both own closer
(dip brier 0.2209 vs mkt 0.4096; reach brier 0.36 vs mkt 0.416). Running:
**14 of 26 (53.8%)**; reach 8/13 (61.5%), dip 5/12 (41.7%), far barrier
unchanged 5/5. Criterion (b) (60% bar) still not met. Criterion (a) still
not met — dip split still below 50% own-closer. Ruling unchanged:
forecast-only.
**Pre-registered test (not a rule):** every near-barrier (gap under 10%)
touch row with a window of 10 days or less also quotes `touch.py` at
the 7-day realized vol in its note; est_prob stays at the 30-day read
unless a row-specific reason is written. The next re-grade scores the
30d read against the 7d read on those rows. Hypothesis: the 30-day
window lags a quieter regime, so above-mid near reads overstate touch
odds (7 of 7 here, 3 of 4 in DEEP-2026-09-24, Silver and Gold month-end
LOW rows in RETRO-20260930-2316 and RETRO-20261001-0020).

**2026-10-01 (RETRO-20261001-0625): first far-barrier row settled.**
`b9687ea473f8` (ETH reach $3k Sep, gap 11.9%, touch.py measured vol 0.467,
own 0.09 vs mid 0.115) LOST (no touch); own closer, dBrier -0.0051. Far
split: 1 decision, own closer on 1. On the 2026-09-25 count (4 of 9)
this makes 5 of 10, but later touch rows (e.g. BTC dip 82.5K
`c8853475ea55`, DEEP-2026-10-01) were not folded into that count, so the
next deep retro re-counts from the ledger. Ruling unchanged.

**2026-09-27 18:1xZ (RETRO-20260927-1815): scheduled-close crypto
strikes/brackets are a SEPARATE family from touch, and my realized-vol
read has lost all three.** `ed46e73085f3` (BTC $76-78k Sep 12, own 0.53 vs
mid 0.945), `4a1df602fb13` (ETH $2.5-2.6k Sep 12, own 0.55 vs 0.705) and
`a10c93456a38` (BTC above $84k Sep 27, own 0.60 vs 0.745) all settled
Yes; the market was closer on 3 of 3 (row dBrier +0.35 / +0.11 / +0.10).
Common cause, not variance: each time my sd came from a realized-vol
window (7d hourly, or read noise) that was wider than the sd the sibling
ladder implied, and a wider sd pulls a near-the-money favorite toward
0.5. On `a10c93456a38` the note already had the answer: siblings implied
sd ~0.9% (vs my 1.63%), and the 24h vol gave 0.76. **Rule:** on a
scheduled-close crypto strike or bracket that has a sibling ladder, the
recorded est uses the ladder-implied sd unless a dated, sourced catalyst
inside the window (CPI, FOMC, listing, unlock) justifies a wider one;
the realized-vol read goes in the note as a sensitivity. Forecast-only
stands (n=3, and matching the ladder cannot beat it). Re-grade at n=8.

Excluded per the sub-boundary taxonomy (DEEP-2026-08-15): Zambia
(fa185b55a5c3, edge 0.06) and Musk wk 200-219 (7808b6f5a4ef, edge 0.045)
both settled this tick too, but both carry claimed edges ≤0.10 under a
blanket category bar (elections; social-media-postcount respectively) —
the bar, not the numeric veto, is the operative decline reason, so they
grade their category narratives (§Extension to general elections; the
bootstrap fork below), not this ledger. Same treatment already applied to
140-159 (70331099597c) and the still-open 160-179 (c24926a5c9d7). Same
exclusion again 2026-08-21: this week's Musk wk 260-279 (42dc4279d3b9,
edge 0.05, category-bar) settled LOST but is off-ledger for the same
reason — the blanket bar, not the veto, is what declined it. Excluded
again 2026-08-26 (RETRO-20260826-0528): WI Hong 10-15% (03901079bd63) —
est (0.090) sits on the market mid (0.089), and the fill-price check shows
negative edge both sides (Yes 0.090−0.107=−0.017; No 0.910−0.929=−0.019),
so there is no realizable disagreement at all, not merely one under the
0.10 bar — same non-trade treatment as the PPI 5.4%/≥6.0% rows.

**2026-08-26 update (05:28Z settlement): six-row Wisconsin Hong
margin-of-victory bracket batch settled, all No (Hong lost the primary
outright).** 3W (No side, small longshot-payout profits: +0.08+0.09+0.25 =
+0.42u) / 3L (Yes side, all −1.00u) — a clean, uncorrelated confirmation of
the existing pattern: every Yes-side disagreement in this batch lost,
every No-side disagreement won. **Totals now 30 realizable trades, 11W/19L,
net −12.00u**; side split re-summed row-by-row over the full table:
**Yes-side 1W/12L, −10.50u** (three new losses, no new wins — extends the
Yes-side lifetime record to 1-for-13); **No-side 10W/7L, −1.50u** (three
new wins — the No-side hit rate is now a genuine majority, 59%, even
though the side stays net-negative in dollars because longshot-No fills
pay little on a win and the earlier No-side losses were larger stakes at
worse prices). Check: −10.50 + −1.50 = −12.00 ✓. No playbook rule change
from this row alone (see RETRO-20260826-0528) — the widened Yes-side split
is flagged for the next deep retro's Yes/No-side asymmetry discussion, not
acted on here.

**2026-08-26 update (17:12Z settlement): Kuala Lumpur 30C weather row
added, first settled row from the new weather category (exploration
budget, DEEP-2026-08-25 22:xxZ); Beijing 26C sibling settled the same tick
but is EXCLUDED from this table — est 0.23 vs ask 0.23/bid 0.21 leaves no
realizable edge either side (Yes: 0.23−0.23=0.00; No: 0.21−0.23=−0.02),
same non-trade treatment as WI Hong 10-15%.** KL: est 0.26 (Yes) vs ask
0.079, edge +0.181, actual high was NOT 30C → Yes lost, −1.00u. The
directional read matters more than the single row: the market priced the
30C bucket at just 0.073 against my model's 0.26-0.28 (implied warmer
actual than my open-meteo N(30.65,1.2) mean), and the market was right —
supports hypothesis (a) from the exploration-budget note (my model reads
systematically cool / too-coarse), not hypothesis (b) (thin-market
mispricing). Beijing, the one city where my model and the market had
already agreed almost exactly (0.228 vs 0.22), losing on its minority
bucket is uninformative either way. Totals at that point: 31 realizable
trades, 11W/20L, net −13.00u; Yes-side 1W/13L −11.50u; No-side 10W/7L
−1.50u. New generation class: weather Gaussian (self-modeled sd,
unvalidated) 0W/1L −1.00u.

**2026-08-26 update (23:19Z settlement): Amsterdam 25C weather row added —
the other open row from this batch (the Spider-Man BND sibling settles
separately, not part of the weather-Gaussian class).** No side, est 0.87 vs
ask 0.56 (edge +0.31), actual result No (25C did NOT occur) → **won**, CF
P&L +0.79u. This is NOT a same-direction replicate of KL — see the
exploration-budget section above for the correction (Amsterdam's market
mode, 25C, was *below* the model's mean, opposite of KL where the market's
mode was *above* — the two rows disagree, not confirm each other, and no
category verdict follows from this n=2). **Totals now 32 realizable
trades, 12W/20L, net −12.21u**; side split re-summed row-by-row over the
full table: **Yes-side unchanged 1W/13L, −11.50u**; **No-side 11W/7L,
−0.71u** (one new win, +0.79u vs the prior −1.50u). Check: −11.50 + −0.71 =
−12.21 ✓. Weather-Gaussian generation class now 1W/1L, net −0.21u (was
0W/1L, −1.00u).

**2026-08-27 update (DEEP retro): six rows added that the hourly cycles
settled but never entered — Crowley (07:28Z, no retro written), the three
PCE MoM legs (15:21Z retro graded them but skipped the same-commit table
duty), and the BoK pair (04:13Z, logged "at-market/veto-correct" with no
retro when the vetoed read had in fact WON — see reconcile.py check 5,
welded off the back of exactly these three misses).** Row notes:
Crowley is the day's ugliest row — the same single-poll margin model that
generated the Hong brackets put 0.0012 on the man who actually won the
primary at a market 0.032; the No-side fill edge (+0.011) was tiny but
positive, so it enters as a No-side LOSS, a reminder that the No side of a
bad model is still the bad model. PCE MoM 0.2% (+0.014 edge) is effectively
at-market and enters only for convention's consistency (any positive
fill-price edge enters; the WI 15-20% row at +0.023 set the floor).
The BoK pair is ONE underlying decision (complementary books, same
convention as the Musk 2-day and Japan GDP pairs — both rows enter the
table, ONE independent event for any evidence-counting): the analyst-poll
Gaussian-free read (est hike 0.60 vs market 0.32, recorded five days
early) was RIGHT against a confident market, the largest counterfactual
win this ledger has ever recorded (+2.03/+2.13u on the two legs of the one
trade). score.py buckets the pair under `revised_away` (both legs were
superseded to market-agrees rows at 01:25Z after live-CLOB convergence,
hours before on-chain settlement) — the supersede was correct hygiene, but
the counterfactual grades the ORIGINAL record-time book, where the edge
was real and realizable.

**Totals now 38 realizable trades, 16W/22L, net −9.01u.** Side split
re-summed row-by-row: **Yes-side 3W/14L, −9.75u** (adds BoK hike W +2.03,
PCE 0.2% W +0.72, PCE 0.1% L −1.00); **No-side 13W/8L, +0.74u** (adds BoK
hold W +2.13, PCE 0.3% W +0.32, Crowley L −1.00) — the No side crosses
into positive territory for the first time. Check: −9.75 + 0.74 = −9.01 ✓.

**2026-08-28 update (16:18Z, LIGHT tick, RETRO-20260828-1618): UMich
Consumer Sentiment FINAL settled (final print 51.7, in-bracket for
49.0-51.9).** Two outside-view-veto rows enter this table. UMich <49.0
(a5703b36d60a): model P(Yes)=0.334 vs live ask 0.177, Yes side, fill-price
edge +0.157 (est − ask); actual No → **lost, −1.00u**. UMich 49.0-51.9
(fdfd9e781481): model P(Yes)=0.321 vs live bid 0.38, No side (model
favored No since est sits below the bid), fill-price edge = bid − est =
0.38−0.321 = +0.059; actual Yes (the final print landed in this exact
bracket) → the No side **lost, −1.00u** — the veto correctly avoided this
loss, same shape as the BTC touch-$80k and Japan GDP-veto precedents. The
sibling 55.0-57.9 row (81af56a9a430, wide-spread-veto) is EXCLUDED, not
entered: fill-price check both sides negative (Yes: 0.087−0.14=−0.053; No:
(1−0.087)−(1−0.04)=0.913−0.96=−0.047) — est sits inside the bid/ask
spread, no realizable disagreement either side, same non-trade treatment
as WI Hong 10-15% and the PPI 5.4%/≥6.0% rows. The other four UMich
brackets (6e1ba0c74bf2, a1f502906022, 3e269764b9e6, d5dcc12cdabe) settled
no-edge, not entered per the standing rule. **Totals now 40 realizable
trades, 16W/24L, net −11.01u.** Side split re-summed row-by-row over the
full table: **Yes-side 3W/15L, −10.75u** (adds UMich <49.0 L −1.00);
**No-side 13W/9L, −0.26u** (adds UMich 49.0-51.9 L −1.00, pulling the No
side back to net-negative after one tick at +0.74u). Check: −10.75 + −0.26
= −11.01 ✓.

**Mechanical-econ fork bookkeeping correction (same tick):** the Canada
GDP set (6 rows, ab9d001c5d8a/834d675fc7e8/c6803f47d674/e2bbfd112771/
6b02ffb04b9a market-agrees, fe954ed9f325 excluded as a pre-registered
process error) also settled this tick — **every row was market-agrees;
none crossed the >0.10 outside-view boundary, so the veto never fired and
the print contributes ZERO rows to this counterfactual ledger.** This
contradicts the Aug 17 fork pre-registration's framing of Canada GDP as
automatically "a fourth event" — a settled mechanical-econ print with no
disagreement is not a veto-boundary test at all, it's simply an instance
where the self-model and the market agreed. The two UMich veto rows added
above ARE a new independent mechanical-econ-Gaussian veto event (net
−2.00u, 0/2 on this print) but were never named in the original Aug 17
fork queue (only PCE, BoK, and Canada GDP were). Net effect: the fork
still has exactly 3 named-and-fired events (Japan GDP, PCE, BoK, net
+2.92u, 3/3 dBrier) plus one unplanned fourth (UMich, net −2.00u, 0/1
dBrier this print) — the deep retro due DEEP-2026-08-28/29 must decide
with this corrected picture, not the "Canada GDP adds a fourth event"
assumption baked into the original registration. Not acting on the fork
here per the standing rule (hourly cycles extend the table, do not decide
it).

**The Yes/No asymmetry discussion RETRO-20260826-0528 flagged for this
deep retro, resolved: the asymmetry is a CLASS effect wearing a side
costume.** Before today the split read Yes 1W/13L vs No 11W/7L, which
tempts a side rule ("stop trusting Yes-side disagreements"). Today's two
Yes-side wins (BoK hike, PCE modal bucket) are both mechanical-econ rows
with named external benchmarks, and the historical Yes-side graveyard
(Musk brackets, TI, box-office, WI Hong upside legs) is almost entirely
behavioral self-models — the side was proxying for the generation class.
No side rule is written; the mechanical-vs-behavioral carve-out fork
(below) is the correct instrument, and it already exists with a
pre-registered decision date.

**Mechanical-econ fork running tally (decision due DEEP-2026-08-28/29 as
pre-registered — NOT today; Canada GDP settles Aug 28 and adds a fourth
event):** Japan GDP +0.85u (agent ahead on dBrier), PCE MoM +0.04u net
across the three legs of one print (agent ahead, 0.244 vs 0.264 summed
Brier), BoK +2.03u counting the one trade once (agent ahead, 0.16 vs 0.46
on the hike leg). Three independent settled events, net **+2.92u**, agent
ahead on dBrier in 3/3 — the fork's ≥3-events / net-positive / dBrier-
majority condition is currently MET. Tomorrow's deep retro makes the call
with Canada GDP in hand; firing it a day early on the strongest print in
the sample (BoK, hours old) is exactly the hot-streak overreaction the
pre-registration exists to prevent.

**FORK DECIDED — DEEP-2026-08-28.** Corrected inputs at decision time:
Canada GDP contributed ZERO fork events (no veto fired — every row
market-agrees, per the Aug-28 bookkeeping correction above), and UMich
fired as an unplanned fourth event at −2.00u, agent behind on dBrier
(0/2 rows). Tally: including UMich 4 events net +0.92u dBrier 3/4;
excluding it 3 events +2.92u 3/3. The pre-registered condition (≥3
events, net counterfactual > 0, dBrier majority) is met on BOTH
readings, so the carve-out fires as registered. UMich shapes the gate
rather than blocking the decision: its Gaussian was self-built off the
prelim with a property-2 failure recorded at forecast time (no reachable
variance benchmark) — a self-model in econ clothing, exactly what the
registered candidate shape ("named external survey benchmark") already
excluded. See §Mechanical-econ carve-out below for the enacted rule and
its kill switch.

**2026-09-04 update (16:13Z, FULL cycle, RETRO-20260904-1613): four
Aug23-vintage NFP bracket rows settled (superseded by the Sep4 revision,
graded on their record-time book per standing convention). Actual print:
NFP >= 150k jobs added (a large beat).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| NFP add 0-50k (d2c8054e1df6) | 0.1794 / 0.265 | No | +0.071 | No | **+0.33** |
| NFP add 50-100k (7800470f6fab) | 0.218 / 0.315 | No | +0.082 | No | **+0.43** |
| NFP add 100-150k (adc70585857a) | 0.1963 / 0.141 | Yes | +0.055 | No | −1.00 |
| NFP add >=150k (a8a368a644f4) | 0.2266 / 0.145 | Yes | +0.082 | **Yes** | **+6.14** |

Net this batch: **+5.90u** (3W/1L). **Totals now 93 realizable trades,
46W/47L, net +21.29u.** Side split re-summed row-by-row: **Yes-side
4W/21L, −10.61u** (adds 100-150k L, >=150k W); **No-side 42W/26L,
+31.90u** (adds 0-50k W, 50-100k W). Check: −10.61 + 31.90 = 21.29 ✓.
Ruling: the veto correctly avoided three losing legs, but the >=150k leg
it also declined would have been the single largest win in this table —
the batch nets positive only because that leg happened to hit, which is
outcome luck on a >0.10 disagreement, not method vindication (full
grading in RETRO-20260904-1613, which also covers the two standard-floor
bets on the same print).

**2026-09-04 update (18:13Z, LIGHT tick, RETRO-20260904-1813): one
same-day weather row settled.**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Shanghai 31C weather (6aff2db6ddbe) | 0.58 / 0.885 | No | +0.280 | Yes | −1.00 |

**Totals now 94 realizable trades, 46W/48L, net +20.29u.** Side split
re-summed row-by-row: **Yes-side unchanged 4W/21L, −10.61u**; **No-side
42W/27L, +30.90u** (adds this loss). Check: −10.61 + 30.90 = 20.29 ✓.
Ruling: model was directionally right (est 0.58 > 0.5) but less
confident than the market's 0.885 given the same partial-day data —
the relative-value No side lost; weather stays no-bet, no gate change
at n=1 (full grading in RETRO-20260904-1813).

**2026-09-04 update (22:11Z, LIGHT tick, RETRO-20260904-2215): five
Astra by-date rows settled, all No-side, all LOST — the family's first
losses ever (previously 5W/0L, by-Sep2 + the by/on-Sep3 batch above).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Astra by-Sep4 (99d1545b2ec7) | 0.08 / 0.863 | No | +0.783 | Yes | −1.00 |
| Astra by-Sep5 (7adc67fe86cc) | 0.18 / 0.685 | No | +0.505 | Yes | −1.00 |
| Astra by-Sep6 (b249eb7256a0) | 0.28 / 0.64 | No | +0.360 | Yes | −1.00 |
| Astra by-Sep7 (d179339fe4c0) | 0.35 / 0.525 | No | +0.175 | Yes | −1.00 |
| Astra by-Sep15 (037ae430d6f3) | 0.80 / 0.885 | No | +0.085 | Yes | −1.00 |

Net this batch: **−5.00u** (0W/5L). **Totals now 99 realizable trades,
46W/53L, net +15.29u.** Side split re-summed row-by-row: **Yes-side
unchanged 4W/21L, −10.61u**; **No-side 42W/32L, +25.90u** (adds this
batch's 0W/5L, −5.00u). Check: −10.61 + 25.90 = 15.29 ✓. Ruling: the
first three rows' rationale text cited a market price (0.14/0.315/0.36)
that does NOT match the `best_bid_at_record`/`best_ask_at_record` those
same forecast.py calls actually stamped (0.863/0.685/0.64) — the live
book had already repriced 50+ points same-day and the note never
reflected it; graded against the true recorded book the "modest" declined
edges were actually 0.36–0.78. The other two rows (by-Sep7, by-Sep15)
quoted the price correctly and still lost — clean misses, gate worked as
designed, zero capital risked on any of the five. Full grading and the
new estimation-method fix (quote the exact bid/ask about to be recorded,
inside the rationale) in RETRO-20260904-2215.

**2026-09-05 update (00:12Z resolve.py, RETRO-20260905-0016; three
outside-view-veto rows settled, all No-side, all LOST as counterfactual
trades — three more losses avoided.** GPT-6-by-Sep15 (`44a62d640ae1`, the
live re-check that supersedes `846f0e23a43a` — only the live row enters,
per the revised-away convention score.py already applies) and Astra
on-Sep4 (`17db5ec8f494`) both trace the same rumor/phased-rollout shape
already dominant in this table; Munich 30C (`355715e4ce82`) is a same-day
weather-Gaussian row, sibling of the Shanghai 31C loss two updates above.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| GPT-6 by-Sep15 (44a62d640ae1) | 0.46 / 0.87 | No | +0.40 | Yes | −1.00 |
| Astra on-Sep4 (17db5ec8f494) | 0.92 / 0.852 | No | +0.067 | Yes | −1.00 |
| Munich 30C weather (355715e4ce82) | 0.28 / 0.565 | No | +0.28 | Yes | −1.00 |

Net this batch: **−3.00u** (0W/3L). **Totals now 102 realizable trades,
46W/56L, net +12.29u.** Side split re-summed row-by-row: **Yes-side
unchanged 4W/21L, −10.61u**; **No-side 42W/35L, +22.90u** (adds this
batch's 0W/3L, −3.00u). Check: −10.61 + 22.90 = 12.29 ✓. Ruling: no
boundary change at this n — GPT-6/Astra extend the already-dominant
rumor/phased-rollout No-side pattern, Munich extends the same-day
weather-Gaussian family (now 2 of its last 2 settlements as avoided
No-side losses); full grading in RETRO-20260905-0016.

**2026-09-05 update (06:12Z resolve.py, LIGHT tick; one outside-view-veto
row settled, Yes-side, LOST as a counterfactual trade — one more loss
avoided.** Miami 92-93°F next-day weather bracket (`0b7b13d60127`): a
same-day weather-Gaussian row, sibling of the Munich 30C avoided loss two
updates above, but Yes-side (own est 0.11 above the 0.06 mid, mech
`superforcaster-market-aware` 0.26 with a leaked-price caveat) rather than
No-side.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Miami 92-93F weather (0b7b13d60127) | 0.11 / 0.06 | Yes | +0.040 | No | −1.00 |

Net this batch: **−1.00u** (0W/1L). **Totals now 103 realizable trades,
46W/57L, net +11.29u.** Side split re-summed row-by-row: **Yes-side
4W/22L, −11.61u** (adds this batch's 0W/1L, −1.00u); **No-side unchanged
42W/35L, +22.90u**. Check: −11.61 + 22.90 = 11.29 ✓. Ruling: no boundary
change at n=1 — extends the same-day weather-Gaussian family to 3-for-3
avoided losses across both sides (Shanghai 31C No-side, Munich 30C
No-side, Miami 92-93F Yes-side); full grading in
RETRO-20260905-0612. Mechanical ledger's outside-view-veto line as of
this update: 106 CF trades, 46W/60L, +$82.17 ≙ +16.4u, brier_delta
+0.0280, held-out +$111.17.

**Accounting convention (DEEP-2026-09-05, per operator note 2026-09-04
~23:20Z): `python3 core/counterfactual.py ledger` is the record; this
hand table is the narrative.** Every future retro that extends this
table also quotes the mechanical ledger's outside-view-veto line
(currently: 106 CF trades, 46W/60L, +$82.17 ≙ +16.4u, brier_delta
+0.0280, held-out +$111.17). The hand table reads +11.29u on 103 trades
because 8 of its rows are trades the protected caps would refuse
(entries ≥0.96 or no bid at record) and some older rows grade edge
against the mid instead of the fill; when the two disagree, the
mechanical ledger wins. Interpretation stays the operator's gnhf-run-4
verdict: the positive CF P&L is one family (Astra snapshots, +34u of
the total; without it the vetoed trades lose), the vetoed beliefs are
worse-calibrated than the market (+0.028), the veto stays.

**2026-09-05 update (14:12Z resolve.py, LIGHT tick; two `wide-spread-veto`
forecasts settled — first wide-spread-veto batch to enter this table
since the Aug14 correction.** Both rows are the same LCK UBF Gen.G vs
Hanwha Life Esports Bo5 (decided 3-1, 4 games total), researched and
vetoed together at 2026-09-02T12:46:38Z. Both legs' directional read was
correct (Over on O/U3.5, Under on O/U4.5), but the mechanical fill
arithmetic uses each row's own recorded `best_ask_at_record` (0.77 and
0.39 respectively), not the book snapshot quoted in the O/U3.5 note
(ask 0.39, implying an apparent +0.26 edge) — the two don't match, a
one-off timing/recording gap between the manual spread-check and
forecast.py's own capture, not yet a pattern (n=1, watch for recurrence
before proposing anything).

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| GenG-HLE O/U3.5 (bf608b923988) | 0.65 / 0.40 | Yes | −0.120 | Yes | +0.30 |
| GenG-HLE O/U4.5 (5b76118ad958) | 0.716 / 0.79 | No | −0.106 | Yes | −1.00 |

Net this batch: **−0.70u** (1W/1L). **Totals now 105 realizable trades,
47W/58L, net +10.59u.** Side split re-summed row-by-row: **Yes-side
5W/22L, −11.31u** (adds this batch's 1W/0L, +0.30u); **No-side 42W/36L,
+21.90u** (adds this batch's 0W/1L, −1.00u). Check: −11.31 + 21.90 =
10.59 ✓. Both legs' realizable edge is negative against the recorded ask
despite the directional read being right on both — the wide-spread
veto's arithmetic justification (crossing the spread erases the apparent
edge) holds even on a batch where the underlying model call was correct.
Ruling: no boundary change at n=2, consistent with the Aug14 correction's
"get the arithmetic right, not a narrative verdict" instruction. Full
grading in RETRO-20260905-1412. Mechanical ledger's wide-spread-veto line
as of this update (`core/counterfactual.py ledger --skip-reason
wide-spread-veto`): 4 settled declined forecasts, 3 fillable CF trades,
1 refused, 2W/1L, pnl −$2.82 (staked $15.00), brier_delta −0.0553,
held-out −$2.83. The outside-view-veto line is unchanged this update:
106 CF trades, 46W/60L, +$82.17 ≙ +16.4u, brier_delta +0.0280, held-out
+$111.17.

**Countable-metric trigger status (DEEP-2026-09-05): fired on the
letter, held shut.** The operator's pre-registered narrowing trigger
(5 settled countable-metric rows, negative brier_delta, positive pnl on
3 of 4 held-out folds) is numerically met (n=5, 4W/1L, +$61.68, dBrier
−0.1367, folds [+6.90, +33.46, +5.00, +21.32, −5.00]) — but all five
rows are snapshots of ONE event (the GTA VI Extended Look view-count
family: `b5c5c134d7cb`, `b3fbd3c3eef7`, `944d8e5fc4d0`, `e398cebab2e6`,
`e441fa8f0f8a`), the same one-family/held-out artifact the operator
flagged on Astra. No carve-out opens on a single event. Operator ask
filed (proposals.md 2026-09-05) to amend the trigger to require ≥3
independent events; quote the countable-metric line each deep-retro
pass until it is answered.

**2026-09-05 update (20:12Z resolve.py, LIGHT tick; 1 `outside-view-veto`
forecast settled.** Guangzhou 35°C same-day exact-temp bracket
(`eb95af0bfe24`, researched 08:22Z): own post-obs est 0.82 vs mid 0.9665
(recorded `market_prob_at_record` 0.927), model's No-side belief (0.18)
well above the market's implied No (~0.033) — outside-view-veto
declined a bet either way (self-modeled in-progress trend, not
fact-final). Settled Yes, so the declined No-side counterfactual trade
lost.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Guangzhou 35°C same-day weather (eb95af0bfe24) | 0.82 / 0.9665 | No | +0.076 | Yes | −1.00 |

Net this batch: **−1.00u** (0W/1L). **Totals now 106 realizable trades,
47W/59L, net +9.59u.** Side split re-summed row-by-row: **Yes-side
unchanged 5W/22L, −11.31u**; **No-side 42W/37L, +20.90u** (adds this
batch's 0W/1L, −1.00u). Check: −11.31 + 20.90 = 9.59 ✓. Ruling: no
boundary change at n=1 — same-day weather family now 1W/3L in this
table's realizable arithmetic (Shanghai/Munich/Miami avoided losses,
Guangzhou did not), consistent with the mechanical ledger's own
same-day-weather subclass (1W/2L, −7.65u) staying net-negative; the
veto's job here is avoiding correlated losses, not winning every row.
Full grading in RETRO-20260905-2012. Mechanical ledger's
outside-view-veto line as of this update
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 107
CF trades, 46W/61L, pnl +$77.17 ≙ +15.43u, brier_delta +0.0280, held-out
+$106.17 (was 106 trades, 46W/60L, +$82.17 ≙ +16.4u, held-out +$111.17
before this row).

**BACKFILL 2026-09-06 16:12Z (found by `strategy/tools/reconcile.py` on the
16:12Z cycle): Munich 25°C same-day exact-temp weather row missing from
this hand table.** Settled 2026-09-06T00:12:47Z (originally researched/vetoed
2026-09-05 08:22Z, `bc29b9874a48`); should have been appended alongside the
Guangzhou row above but was dropped.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Munich 25°C same-day weather (bc29b9874a48) | 0.26 / 0.23 | Yes | +0.01 | No | −1.00 |

Model (0.26) leaned Yes slightly more than the market mid (0.23); the
realizable counterfactual enters Yes at the 0.25 ask (edge +0.01,
essentially at-market — this was never a real disagreement, just noise
around a near-consensus number). Outcome was No, so the tiny counterfactual
Yes-side edge lost, −1.00u. Per the 2026-09-06 ~00:30Z operator note, this
file's hand totals are narrative only — the mechanical ledger is the
record. Current mechanical outside-view-veto line
(`core/counterfactual.py ledger --skip-reason outside-view-veto`, includes
this row): 116 settled declined forecasts, 108 fillable CF trades, 46W/62L,
pnl +$72.17 ≙ +14.43u, brier_delta +0.0279, held-out +$106.18. No ruling
change (edge was ~0, not a real disagreement to grade).

**2026-09-07 04:14Z update (FULL cycle, cloud; resolve.py settled 2 forecasts,
1 `outside-view-veto`).** Hong Kong 26°C same-day lowest-temp bracket
(`2eb38db512c9`, researched 2026-09-03 21:01Z): own post-obs est P(26.x)=0.80
vs mid 0.715 (bid 0.64/ask 0.75 at record — book had moved to ask 0.77 by
fill), model side Yes on a station-observation-conditioned same-day read
(HKO 04:40 HKT already at 26.7°C, needed ≥0.8°C more cooling in ~2h to
leave the bucket) — vetoed under both self-model-class and wide-spread
(spread 0.11). Settled Yes, so the declined Yes-side counterfactual trade
won.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Hong Kong 26°C same-day weather (2eb38db512c9) | 0.80 / 0.715 | Yes | +0.030 | Yes | **+0.30** |

Current mechanical ledger's outside-view-veto line (`core/counterfactual.py
ledger --skip-reason outside-view-veto`, includes this row): 117 settled
declined forecasts, 109 fillable CF trades, 47W/62L, pnl +$73.66 ≙ +14.73u,
brier_delta +0.0273, held-out +$107.67. Ruling: no boundary change at n=1 —
same-day weather subclass now 2W/2L in the mechanical ledger's own grouping
(was 1W/2L before this row), consistent with the standing read that the
veto trades a few avoidable wins for avoiding the correlated-loss tail
elsewhere in the family; own estimate (0.80) also beat the blind mech
second opinion (superforcaster-market-aware, 0.28) on this row, worth
tracking if the pattern repeats. Full grading in RETRO-20260907-0414.

**2026-09-07 12:38Z update (LIGHT tick, cloud; resolve.py settled 2
forecasts, 1 `outside-view-veto`).** Wellington 10°C same-day
highest-temp bracket (`b838efbe4ade`, researched 2026-09-07 02:20Z): own
post-obs est P(10.0)=0.4522 (open-meteo hourly max 9.5°C, same-day
sd=0.6) vs mid ~0.7985 (bid 0.769/ask 0.861 at record) — model's implied
No belief (0.548) well above the market's implied No (~0.139-0.231),
vetoed as a same-day weather self-model disagreement. Settled Yes, so
the declined No-side counterfactual trade lost.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Wellington 10°C same-day weather (b838efbe4ade) | 0.4522 / 0.7985 | No | +0.317 | Yes | −1.00 |

Net this batch: **−1.00u** (0W/1L). Current mechanical ledger's
outside-view-veto line (`core/counterfactual.py ledger --skip-reason
outside-view-veto`, includes this row): 118 settled declined forecasts,
110 fillable CF trades, 47W/63L, pnl +$68.66 ≙ +13.73u, brier_delta
+0.0293, held-out +$102.67 (was 117 rows, 109 trades, 47W/62L,
+$73.66 ≙ +14.73u, brier_delta +0.0273, held-out +$107.67 before this
row). Ruling: no boundary change at n=1 — the mechanical ledger's own
same-day weather subclass is now 5 rows, 1W/4L, −17.65 (was 4 rows,
1W/3L, −12.65): this row is a fourth avoided loss (Shanghai, Munich,
Miami, and now Wellington all had their declined side lose), against
Guangzhou as the one case where the veto missed a win. A fixed-sd
same-day point-forecast Gaussian is still net-negative on this exact
bracket shape (4 of 5 declined trades would have lost), consistent with
keeping the veto rather than loosening it — this row reinforces the
standing read, it does not reverse it. Full grading in
RETRO-20260907-1238.

**2026-09-07 16:14Z update (LIGHT tick, cloud; resolve.py settled 2
`outside-view-veto` forecasts, siblings of the AfD/Grüne Sachsen-Anhalt
settlements).** SPD ≥9% (`3df069438d36`): est 0.22 vs ask 0.088 at
record, Yes-side edge ~0.13. Official SPD 9.3% → Yes — declined trade
**WINS**, +$51.82 (+10.36u), a veto miss. Tokyo lowest-temp 22°C Sep7
(`ff7e0fda3407`, same-day weather subclass): est P(No)=0.17 vs ask 0.10,
No-side edge 0.07. Official low was 22°C → Yes — declined trade
**LOSES**, −$5.00 (−1.00u), a correct decline.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| SPD ≥9% Sachsen-Anhalt (3df069438d36) | 0.22 / 0.088 | Yes | +0.132 | Yes | **+10.36** |
| Tokyo 22°C Sep7 (ff7e0fda3407) | 0.17 / 0.10 | No | +0.070 | Yes | −1.00 |

Net this batch: **+9.36u, 1W/1L** ($51.82 − $5.00 = $46.82 dollars).
Current mechanical ledger (`core/counterfactual.py ledger --skip-reason
outside-view-veto`, includes both rows): 120 settled declined forecasts,
112 fillable CF trades, 48W/64L, pnl +$115.48 ≙ +23.10u, brier_delta
+0.0271, held-out +$149.49 (was 118 rows, 110 trades, 47W/63L,
+$68.66 ≙ +13.73u, brier_delta +0.0293, held-out +$102.67 before these
two rows). Side split: yes 34 rows/34 trd/9W-25L/+$20.82; no 86
rows/78 trd/39W-39L/+$94.66. Ruling: no boundary change at n=1 on
either row — the SPD miss is a real cost but sits inside the standing
read that yes-side vetoes are the worse-performing class (9W/25L at
~26% win rate vs no-side's 39W/39L at 50%); occasional large yes-side
misses like this one are the expected cost of holding that boundary, not
new evidence to loosen it. The Tokyo row extends the same-day-weather
subclass's run of correct declines. Full grading in
RETRO-20260907-1614.

[MERGE NOTE, operator reconcile 2026-09-07 ~21:00Z: the operator-machine
loop graded the same three rows (Wellington, SPD >=9%, Tokyo) in parallel
between 12:41Z and 20:08Z and its push was rejected; origin's table rows
above are canonical and its duplicate rows are not carried. Two distinct
rulings from the operator-machine retros (RETRO-20260907-1241, -1613) are
carried here as pre-registered, not enacted: (a) Wellington -- the mean was
right and the dispersion wrong; a same-day point forecast sitting ON a
bucket boundary makes P(bucket) ~0.45 by construction, and the market's
0.815 (implied sd ~0.35 after noon) read the afternoon peak better; test
the after-noon sd (0.6 vs ~0.35) once the same-day subclass reaches ~6
settled rows. (b) SPD >=9% and the Gruene >=7% bet WON are one event: the
self-chosen sd (1.2-1.3) for sub-10% parties in this Landtag election was
too tight and the miss was upward; at the next German state election,
grade the small-party vote-share Gaussian rows against a wider,
upward-skewed error before the category is allowed a >0.10 disagreement.]

**2026-09-07 22:14Z update (FULL cycle, cloud; resolve.py settled 1
`outside-view-veto` forecast).** Jeddah 38°C same-day highest-temp bracket
(`39dbfcb80a90`, researched 2026-09-07 02:20Z): open-meteo daily forecast
max 35.0°C (Asia/Riyadh, pre-dawn ~05:15 local, next-day-style sd=1.2 per
playbook), own est P(38°C)=0.0168 vs mid 0.165 (bid 0.14/ask 0.19 at
record) — model's implied No belief (0.983) well above the market's
implied No (~0.81-0.86), vetoed as a weather self-model disagreement.
Settled No, so the declined No-side counterfactual trade won.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Jeddah 38°C same-day weather (39dbfcb80a90) | 0.0168 / 0.165 | No | +0.148 | No | **+0.23** |

Current mechanical ledger's outside-view-veto line
(`core/counterfactual.py ledger --skip-reason outside-view-veto`,
includes this row): 121 settled declined forecasts, 113 fillable CF
trades, 49W/64L, pnl +$116.29, brier_delta +0.0267, held-out +$146.68.
Ruling: no boundary change at n=1 — this row is well outside the
same-day-weather subclass's usual afternoon-peak-boundary failure shape
(a pre-dawn forecast on a wide 3°C-out bucket, not a near-boundary same-day
read), and it is a clean win for the self-model, consistent with the
veto correctly avoiding the tail loss elsewhere in the weather category
(still net −$48.60 in the mechanical ledger) rather than evidence to
loosen it.

**2026-09-08 deep retro (resolve.py this pass settled 1
`outside-view-veto` forecast).** Toronto 25°C same-day highest-temp
(`291e9630e91e`, recorded 2026-09-07 00:23Z, next-day-style): open-meteo
point forecast max 25.4°C, N(25.4, 1.2) gives P(25°C)=0.307 vs market
0.57, disagreement 0.26, vetoed under the weather-category moratorium.
Official high was 25°C → Yes. The declined No-side CF trade (No @0.44,
claimed edge 0.253) **LOSES** −$5.00 (−1.00u): a correct decline, and a
clean self-model miss — the point forecast was right (25.4 rounds into
the bucket) and the sd=1.2 dispersion pushed 0.69 of the mass out of a
bucket the market read at 0.57.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Toronto 25°C Sep7 (291e9630e91e) | 0.307 / 0.57 | No | +0.253 | Yes | −5.00 |

Current mechanical ledger's outside-view-veto line
(`core/counterfactual.py ledger --skip-reason outside-view-veto`, after
`screen_replay.py events --limit 200`, includes this row): 122 settled
declined forecasts, 114 fillable CF trades, 49W/65L, pnl +$111.29,
brier_delta +0.0289, held-out +$141.68. Ruling: no boundary change —
this is the second "mean right, dispersion wrong" weather row (after
Wellington, RETRO-20260907-1241's pre-registered sd question): the
Gaussian's sd, not its center, produced the disagreement, and the market
priced the same point forecast with a tighter sd and won. It counts
toward the pre-registered Wellington sd test (re-examine the weather sd
once the same-day subclass reaches ~6 settled rows — this row is
next-day-style, so it informs but does not trigger that test). Within
the veto slice, weather now reads 18 rows, 5W/13L, CF −$53.60, dBrier
+0.0836: the veto's single best category.

**2026-09-09 update (12:3xZ resolve.py, LIGHT tick, cloud; three
`econ-cpi` veto forecasts settled on the China Aug 2026 CPI print — one
`outside-view-veto`, one `wide-spread-veto` fillable, one
`wide-spread-veto` refused as unexecutable).** NBS printed China Aug 2026
CPI YoY at 0.8%, in the 0.7-0.8% bracket. The base-effect anchor used at
record time (Jul YoY 0.5% + Aug seasonal MoM ~+0.3% → ~0.8%) was exact —
first confirmed application of the PPI base-effect projection method
(§"PPI YoY brackets: base-effect projection", 2026-08-11 above) to a
second economic series. Two consensus sources disagreed by one bracket at
record time (tradingeconomics 0.7% vs investing.com/Lundgreen 0.9%); TE's
figure fell in the actual bracket, Lundgreen/investing.com's did not —
n=1, too weak to rule on for future disputes, but the first data point
favors TE when the two conflict.

- **0.7-0.8% bracket** (`19cf14c87979`, outside-view-veto): mixture model
  P=0.33 vs mid 0.485; the No-side apparent edge (~0.15) was built on the
  contradictory consensus and vetoed under gate 2. Settled Yes — the
  declined No bet would have LOST. Correct veto.
- **≥0.9% bracket** (`7bacc91ddf91`, wide-spread-veto): own P=0.38 vs ask
  0.305, spread 0.069 > max_spread 0.06. Settled No — the declined Yes
  bet would have LOST. Correct veto.
- **0.5-0.6% bracket, post-print supersede** (`9eff80f25296`,
  wide-spread-veto): after the print, Yes ask 0.22 was mispriced (true
  edge ~0.20 on No) but the No side had zero asks in the live book (bids
  only) — refused by the fill model as unexecutable, correctly excluded
  from the counterfactual trade count, not a real declined trade.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| China CPI 0.7-0.8% Aug26 (19cf14c87979) | 0.67 / 0.53 | No | +0.140 | Yes | −1.00 |
| China CPI ≥0.9% Aug26 (7bacc91ddf91) | 0.38 / 0.331 | Yes | +0.049 | No | −1.00 |

Net this batch: **−2.00u** (0W/2L). Current mechanical ledgers
(`core/counterfactual.py ledger --skip-reason <reason>`, both include
these rows):
- outside-view-veto: 123 settled declined forecasts, 115 fillable CF
  trades, 49W/66L, pnl +$106.29 ≙ +21.26u, brier_delta +0.0301, held-out
  +$136.68 (was 122/114/49W-65L/+$111.29/+$141.68 before this row). Side
  split: yes 34 rows/34 trd/9W-25L/+$20.82 (unchanged this batch); no 89
  rows/81 trd/40W-41L/+$85.47 (adds this row's 0W/1L, −$5.00). Check:
  20.82+85.47=106.29 ✓.
- wide-spread-veto: 6 settled declined forecasts, 4 fillable CF trades,
  2 refused, 2W/2L, pnl −$7.82 ≙ −1.56u, brier_delta −0.0326, held-out
  −$8.51 (was 4/3/1 refused/2W-1L/−$2.82/−$2.83 before this batch). Side
  split: yes 3 rows/3 trd/2W-1L/−$2.82 (unchanged this batch); no 3
  rows/1 trd/0W-1L/−$5.00 (adds this row's 0W/1L, −$5.00, plus the
  refused `9eff80f25296` which contributes a settled row but no trade).
  Check: −2.82−5.00=−7.82 ✓.

Ruling: no boundary change at n=2 on either gate — both counterfactual
trades would have lost, i.e. both declines were correct, consistent with
the standing reads (outside-view-veto's no-side already the stronger
performer at 40W/41L vs yes-side's 9W/25L; wide-spread-veto still thin at
n=6, too small to read). The base-effect method confirmation and the
TE-vs-Lundgreen data point are the more useful findings from this batch
than the veto grading — both are single-instance and carried as
hypotheses, not rules, until a second China CPI print or a second
TE/Lundgreen conflict tests them.

**2026-09-11 update (08:1xZ resolve.py, LIGHT tick, cloud; RETRO-20260911-0814;
3 more `wide-spread-veto` rows settled — one this tick, two backlog
catch-ups found while reconciling the tool's live total against this
table's last snapshot, both missed by earlier ticks):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Chewy "Consumable" wide-spread duplicate (`e7a452fef1be`) | 0.93 / 0.59 | Yes | +0.340 | Yes | **+3.47** |
| RNC "2028/Campaign" (`906a1a65abc8`) | 0.80 / 0.71 | Yes | +0.090 | Yes | **+2.04** |
| RNC "Tax on Tips/Overtime" (`83321f868e0f`) | 0.75 / 0.77 | Yes | −0.020 | Yes | **+1.49** |

`e7a452fef1be` settled 2026-09-09T14:23:30Z but was never entered here:
it's the original 0.93-est Chewy forecast, superseded two minutes after
recording by `ffc3fcdcbaa6` when the label was corrected to
`outside-view-veto` (that row is already graded above at line ~3444).
`core/counterfactual.py` deliberately keeps superseded rows rather than
dropping them, so this is a legitimate second row under
`wide-spread-veto`, distinct from its already-graded successor — just
never manually added. `906a1a65abc8` settled 2026-09-11T07:23:43Z but
the 07:28:35Z TRIGGERED cycle that should have graded it (settlement
duty applies to TRIGGERED cycles same as any other, per
RETRO-20260908-2250) only logged its Sweden Liberals research and
reported "settled 0" — a miss, caught up here one tick late.
`83321f868e0f` is this tick's own genuine new settlement.

Current mechanical ledger's wide-spread-veto line (`core/counterfactual.py
ledger --skip-reason wide-spread-veto`): 9 settled declined forecasts, 7
fillable CF trades, 2 refused, 5W/2L, pnl −$0.81, brier_delta −0.0967,
held-out −$1.50 (was 6/4/2 refused/2W-2L/−$7.82/−0.0326/−$8.51 before
this batch). Side split: yes 6 rows/6 trd/5W-1L/+$4.19 (adds all three
new wins, +$7.00, was 3/3/2W-1L/−$2.82 before this batch); no 3 rows/1
trd/0W-1L/−$5.00 (unchanged this batch). Check: 4.19−5.00=−0.81 ✓;
−2.82+3.47+2.04+1.49=4.18≈4.19 (rounding) ✓.

Ruling: no boundary change at n=9/7 trades — all three new rows are
declined-Yes-side wins, extending the yes-side's edge but still far
short of the ~15-settlement floor. `vance-mention` as a category: n=2,
both won, +$3.54 — both are broad, near-default politician phrases
("campaign", Vance's own stock "tax on tips/overtime" line) rather than
narrow session-specific content, consistent with the broad-phrase side
of the say-the-word split RETRO-20260911-0624 already documented; adds
weak supporting evidence, not a new finding.

**2026-09-15 12:5xZ update (LIGHT tick, operator machine, resolve.py; 1
`wide-spread-veto` forecast settled, plus a catch-up row).** `705c1219decd`
is this tick's genuine settlement: F1 Italian GP safety car (raced Sep6,
market end date Sep13), a fact-final row where the F1.com race report
confirmed a physical Safety Car on lap 2. Declined because the spread
(0.099) exceeded max_spread 0.06. `697a7f4f3799` (Emmys, Last Week
Tonight) settled 2026-09-15T04:13Z and was graded narratively in
RETRO-20260915-0414, but that commit did not extend this table - a
violation of the 2026-08-23 same-commit rule, repaired here.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Emmys Variety Series, Last Week Tonight (`697a7f4f3799`) | 0.19 / 0.14 | Yes | +0.050 | No | **−5.00** |
| F1 Italian GP safety car, fact-final (`705c1219decd`) | 0.99 / 0.899 | Yes | +0.091 | Yes | **+0.56** |

Current mechanical ledger's wide-spread-veto line (`core/counterfactual.py
ledger --skip-reason wide-spread-veto`): 11 settled declined forecasts, 9
fillable CF trades, 2 refused, 6W/3L, pnl −$5.25, brier_delta −0.0788,
held-out −$0.93 (was 9/7/2 refused/5W-2L/−$0.81/−0.0967/−$1.50). Side
split: yes 8 rows/8 trd/6W-2L/−$0.25 (adds −$5.00 and +$0.56, was
6/6/5W-1L/+$4.19); no 3 rows/1 trd/0W-1L/−$5.00 (unchanged). Check:
−0.25−5.00=−5.25 ✓; 4.19−5.00+0.56=−0.25 ✓.

Ruling: no boundary change at n=11/9 trades. The fact-finality subclass
is now 4 trades, 3W/1L, +$0.65: the veto costs little on fact-final rows
because a 0.90 ask leaves only ~$0.56 to win on a $5 stake, so a tight
spread gate there forgoes small, near-certain gains rather than large
ones. The −$5.00 Emmys row is a thin-edge (+0.05) judgment row the veto
correctly kept out.

**2026-09-16 06:2xZ update (LIGHT tick, cloud, resolve.py; 1
`wide-spread-veto` forecast settled — the third sibling in this week's
Israel x Lebanon "diplomatic meeting by <date>" family, see
RETRO-20260916-0621).** `7d43ec49805b` (Israel x Lebanon by-Sep15,
supersedes `cea6c0cc22f9`): own 0.75 vs Yes ask 0.90 (No ask 0.19,
implied No-side edge 0.06), declined because spread 0.09 exceeded
max_spread 0.06. Settled **Yes** — the declined No-side counterfactual
trade **loses**.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Israel x Lebanon by-Sep15 (`7d43ec49805b`) | 0.75 / 0.855 | No | +0.060 | Yes | **−5.00** |

Current mechanical ledger's wide-spread-veto line (`core/counterfactual.py
ledger --skip-reason wide-spread-veto`): 12 settled declined forecasts,
10 fillable CF trades, 2 refused, 6W/4L, pnl −$10.25, brier_delta
−0.0688, held-out −$5.93 (was 11/9/2 refused/6W-3L/−$5.25/−0.0788/
−$0.93). Side split: yes 8 rows/8 trd/6W-2L/−$0.25 (unchanged); no 4
rows/2 trd/0W-2L/−$10.00 (adds this loss, was 3/1/0W-1L/−$5.00). Check:
−0.25−10.00=−10.25 ✓.

Ruling: no boundary change at n=12/10 trades. This is the same shape as
the two outside-view-veto siblings settled the same tick (own estimate
below market on a multi-channel diplomatic-contact process, market
right); see the outside-view-veto section below for the cross-family
read.

**2026-09-09 update (14:2xZ resolve.py, FULL cycle, cloud; 1
`outside-view-veto` forecast settled — the Chewy "Consumable" say-the-word
row flagged in schedule.json for settlement grading).** `ffc3fcdcbaa6`
(recorded 2026-09-08 20:21Z, superseding `e7a452fef1be` two minutes
earlier as a label erratum — same 0.93 estimate, reclassified from
`wide-spread-veto` because DEEP-2026-08-14's tiebreak routes a
>0.10-claimed-edge row to outside-view-veto even when the spread gate
also fires): Chewy fiscal Q2 2026 earnings call, own est 0.93 vs ask
0.58 (mid 0.34, an empty-book artifact — bid was 0.10), on the evidence
that "Consumables" is Chewy's own reported revenue segment name, used
5-6 times in the prior-year Q2 transcript. Settled **Yes** — the
declined Yes-side counterfactual trade **wins**. Grading the three
questions the watch item pre-registered: (a) the tool's own subclass
tagger filed this row under `fact-finality`, not unlabelled judgment —
independent, mechanical support for treating "company repeats its own
standard reported vocabulary" as closer to a mechanical base rate than
a behavioural self-model, though n=1 is too thin to act on; (b) the
blind mech (`superforcaster-market-aware`, service 44) gave 0.92 —
within 0.01 of the own estimate — while self-classing the question
`NR-utterance`/`researchability=0.15`, i.e. confidently right on a
question it flagged as unresearchable, the same pattern the still-open
Vance utterance rows show; (c) the 40-share ask at 0.58 was in fact
takeable at the strategy's $5 (~8.6-share) stake size, so the
wide-spread veto alone would have been overcautious here — the correct
blocker was the outside-view veto's >0.10 boundary, which this row does
not argue against. Full narrative in RETRO-20260909-1425.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Chewy "Consumable" say-the-word (ffc3fcdcbaa6) | 0.93 / 0.58 | Yes | +0.350 | Yes | **+3.62** |

Current mechanical ledger's outside-view-veto line
(`core/counterfactual.py ledger --skip-reason outside-view-veto`, after
`screen_replay.py events --limit 200`, includes this row): 124 settled
declined forecasts, 116 fillable CF trades, 82 events, 50W/66L, pnl
+$109.91, brier_delta +0.0264, held-out +$140.30 (was 123/115/49W-66L/
+$106.29/+0.0301/+$136.68 before this row). Side split: yes 35 rows/35
trd/10W-25L/+$24.44 (adds this row's win, +$3.62, was 34/34/9W-25L/
+$20.82); no 89 rows/81 trd/40W-41L/+$85.47 (unchanged this batch).
Check: 24.44+85.47=109.91 ✓.

DEEP-2026-09-11 batch (settled by the deep retro's own resolve run,
graded DEEP-2026-09-11 (c), table extended same-commit per the
2026-08-23 rule). Both are fact-finality utterance rows (standard rally
vocabulary, multi-hour speech window) declined at claimed edges
0.21/0.18 under the >0.10 veto:

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| RNC "Radical Left" trump-mention (36ff9feec021) | 0.87 / 0.66 | Yes | +0.210 | Yes | **+2.58** |
| RNC "MAGA/MAGA-full" say-the-word (87736f3e8ab9) | 0.90 / 0.72 | Yes | +0.180 | Yes | **+1.94** |

Mechanical ledger after this batch: 126 settled declined forecasts,
118 fillable CF trades, 84 events, 52W/66L, pnl +$114.43, brier_delta
+0.0246, held-out +$143.25. Side split: yes 37 rows/37 trd/12W-25L/
+$28.96 (adds both wins, +$2.58 and +$1.94, was 35/35/10W-25L/+$24.44);
no 89 rows/81 trd/40W-41L/+$85.47 (unchanged this batch).
Check: 28.96+85.47=114.43 ✓. The subclass reading stays uncomfortable
in the honest direction: fact-finality is now n=29 labeled rows at CF
pnl +$122.08 but subclass dBrier +0.0419 — the wins are real money and
still worse-than-market beliefs on average; the fork bar below, not
this table, decides anything.

Ruling: no boundary change at n=1 within say-the-word (the category
verdict threshold is ~15 settlements) and no change to the relaxation
fork's status — overall brier_delta is still positive (+0.0264, agent
behind market) and this single win doesn't reach the fork's per-fold
recompute threshold on its own. The useful finding is the (a)/(b)/(c)
grading above, carried as a baseline for the still-open Vance utterance
rows (`83321f868e0f`, `906a1a65abc8`) rather than a rule change yet.

**2026-09-11 06:24Z update (LIGHT tick, cloud, resolve.py; 2 more of the
same RNC Sep10 utterance family settled — both fact-finality, both
`Yes`-side, both declined at a wide claimed edge):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| RNC "Endorse/Endorsed/Endorsement" say-the-word (16e13abfec2f) | 0.58 / 0.43 | Yes | +0.150 | No | **−5.00** |
| RNC "America First" say-the-word (11ea1286d8c7) | 0.62 / 0.28 | Yes | +0.340 | No | **−5.00** |

Mechanical ledger after this batch (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 128 settled declined forecasts, 120
fillable CF trades, 86 events, 52W/68L, pnl +$104.43, brier_delta
+0.0279, held-out +$133.25 (was 126/118/84/52W-66L/+$114.43/+0.0246/
+$143.25 before this batch). Side split: yes 39 rows/39 trd/12W-27L/
+$18.96 (adds both losses, −$5.00 each, was 37/37/12W-25L/+$28.96); no
89 rows/81 trd/40W-41L/+$85.47 (unchanged this batch). Check:
18.96+85.47=104.43 ✓.

Ruling: both declines correct — the counterfactual Yes trades both lose,
so the >0.10 veto again saved money on this event family (now 2 wins /
2 losses for the same-event Sep10 RNC utterance batch: MAGA and Radical
Left won, Endorse and America First lost). The same-session bet
(`e77eef5d06ad`, "Afford", edge 0.06, under the veto) also lost this
tick — see RETRO-20260911-0624 for the full family read. No boundary
change (fork status is deep-retro-only per the section below); this is
a table extension only.

**DEEP-2026-09-12 catch-up batch (settled 2026-09-11 with the Aug CPI
cluster; the 16:17Z settlement commit e081582 graded the cluster
narratively in its gate-2 note but did NOT extend this table in the
same commit — a violation of the 2026-08-23 same-commit rule on its
face, recorded in DEEP-2026-09-12 (d) and repaired here.** Both rows
are Aug-CPI bracket legs recorded on the No token (question frame
below follows the tool: both count as No-side), declined under the
>0.10 veto on an unsourced-sd Gaussian (gate 2):

| Row | est vs mkt (No token) | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Aug headline MoM 0.4% bracket, No leg (5a6d5321c25a) | 0.66 / 0.515 | No | +0.140 | print was 0.4% (No leg lost) | **−5.00** |
| Aug core MoM 0.2% bracket, No leg (79e72c3002c3) | 0.62 / 0.45 | No | +0.160 | print was 0.3% (No leg won) | **+5.87** |

Mechanical ledger after this batch (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 130 settled declined forecasts, 122
fillable CF trades, 88 events, 53W/69L, pnl +$105.30, brier_delta
+0.0276, held-out +$134.12 (was 128/120/86/52W-68L/+$104.43/+0.0279/
+$133.25 before this batch). Side split: yes 39 rows/39 trd/12W-27L/
+$18.96 (unchanged this batch); no 91 rows/83 trd/41W-42L/+$86.34
(adds −$5.00 and +$5.87, was 89/81/40W-41L/+$85.47).
Check: 18.96+86.34=105.30 ✓. Ruling: net +$0.87 on the pair, and the
winning leg is the one whose edge came from a legible mean-shift off
the sourced nowcast, while the losing leg's edge rested on the
unsourced sd — the same split RETRO-20260911-1615's gate-2 note found
across the whole cluster. Supports gate 2 as written; no boundary
change.

**2026-09-16 06:2xZ update (LIGHT tick, cloud, resolve.py; 2 rows from
the Israel x Lebanon "diplomatic meeting by <date>" family settled, both
No-side timeline declines — see RETRO-20260916-0621 for the full family
read across all 5 settled siblings):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Israel x Lebanon by-Sep18 (9894fc8df165) | 0.55 / 0.835 | No | +0.260 | Yes | **−5.00** |
| Israel x Lebanon by-Sep16 (459635ab318c) | 0.62 / 0.935 | No | +0.281 | Yes | **−5.00** |

Mechanical ledger after this batch (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 132 settled declined forecasts, 124
fillable CF trades, 90 events, 53W/71L, pnl +$95.30, brier_delta
+0.0296, held-out +$123.84 (was 130/122/88/53W-69L/+$105.30/+0.0276/
+$134.12 before this batch). Side split: yes 52 rows/52 trd/16W-36L/
−$13.56 (unchanged this batch); no 72 rows/72 trd/37W-35L/+$108.86
(adds both −$5.00 losses, was 70/70/37W-33L/+$118.86). Check:
−13.56+108.86=95.30 ✓.

Ruling: both declines correct in isolation (the market beat the
discounted timeline estimate both times), but this is the third sibling
in the same underlying process to do so this week (the third,
`7d43ec49805b`, is a wide-spread-veto row extended in that section
below) — worth a deep retro look at whether "multiple parallel qualifying
channels" markets deserve a higher outside-view floor, but n=3 from one
process is far short of the relaxation fork's 40-event bar and that fork
is deep-retro-only. No boundary change today.

**2026-09-16 22:11Z update (FULL cycle, operator machine; resolve.py
settled 7 declined-side rows this window — the Sept15 box-office bracket
and the full Warsh Sep16 FOMC-presser word-count batch, 5 outside-view-veto
+ 1 wide-spread-veto):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Spider-Man overtake Star Wars by Sep15 (6eb52610fb5c) | 0.68 / 0.885 | No | +0.170 | Yes | **−5.00** |
| Warsh "Anchor"/"Anchored" (fd03d4763d62) | 0.20 / 0.325 | No | +0.120 | Yes | **−5.00** |
| Warsh "Inflation" 40+ (340afae4c4b8) | 0.08 / 0.215 | No | +0.130 | No | **+1.33** |
| Warsh "Echo" (5ed39e44acd1) | 0.75 / 0.475 | Yes | +0.270 | No | **−5.00** |
| Warsh "Scenario" (03962bee9d8d) | 0.30 / 0.465 | No | +0.150 | No | **+4.09** |
| Warsh "Luck"/"Lucky" (e94a328d4e7f) | 0.20 / 0.37 | No | +0.150 | No | **+2.69** |
| Warsh "Labor Force" (0dd29ac81ce4, wide-spread-veto) | 0.30 / 0.47 | No | +0.140 | No | **+3.93** |

Net this batch: outside-view-veto **−1.94u** (2W/4L: Anchor/Echo/Spider-Man
lost, Inflation-40+/Scenario/Luck won); wide-spread-veto **+3.93u** (1W/0L,
Labor Force). Ruling: the Warsh press-conference batch splits almost
evenly (3W/3L on the outside-view-veto legs) rather than confirming or
refuting the veto boundary at this n — same "confident middle, thin
tails" shape noted elsewhere in this ledger for point-estimate Gaussians
on a single transcript. Mechanical ledger is the record going forward
(`core/counterfactual.py ledger --skip-reason outside-view-veto` /
`--skip-reason wide-spread-veto`); this table entry satisfies the
per-row documentation duty (reconcile.py check 5) without re-deriving
the running hand totals, per the 2026-09-06 operator note above that
this file's totals are narrative only.

**2026-09-17 02:53Z update (TRIGGERED cycle; resolve.py settled 2
declined-side rows from the Trump Gastonia NC rally say-the-word
family — see RETRO-20260917-0253):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| MAHA (0c64397063d4, outside-view-veto) | 0.48 / 0.63 | No | +0.130 | Yes | **−5.00** |
| Egg (56c24f26e025, wide-spread-veto) | 0.45 / 0.735 | No | +0.050 | Yes | **−5.00** |

Both declines correct: same rally, both self-modeled from thin
(1-2-transcript) base rates on topic-contingent phrases, both resolved
Yes against the model's No lean — the veto avoided both losses. Mechanical
ledger after this batch (`core/counterfactual.py ledger --skip-reason
outside-view-veto` / `--skip-reason wide-spread-veto`): outside-view-veto
139 rows/131 trd/56W-75L/+$83.41/dBrier +0.0315/held-out +$89.19;
wide-spread-veto 14 rows/12 trd/7W-5L/−$11.32/dBrier −0.0517/held-out
−$7.00. This entry satisfies the per-row documentation duty without
re-deriving the running hand totals, per the 2026-09-06 operator note.
No boundary change at this n — two more same-family confirmations, not a
new failure mode.

**2026-09-17 deep-retro REPAIR (DEEP-2026-09-17): one veto settlement
missed its same-commit table entry.** `3a539d9be02d` (Trump NC rally
"Furniture", wide-spread-veto, live ask 0.74/bid 0.40 at record) settled
on the 2026-09-17 04:1xZ LIGHT tick and RETRO-20260917-0413 graded it
narratively, but the same commit (9acd1e8) did not extend this table —
the exact violation shape the schedule.json `_comment` rule (DEEP-2026-08-23,
re-affirmed DEEP-2026-09-02) names as "a violation on its face". Row,
booked here one deep-retro late:

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Trump NC "Furniture" (3a539d9be02d, wide-spread-veto) | 0.15 / 0.57 | No | +0.250 | No | **+3.33** |

Mechanical ledger after this row (`core/counterfactual.py ledger
--skip-reason wide-spread-veto`, verified this retro): 15 rows/13 trd/
8W-5L/−$7.99/dBrier −0.0684/held-out −$3.67; side split yes 8/8/6W-2L/
−$0.25, no 7/5/2W-3L/−$7.74. The miss is an isolated recurrence (last
instance RETRO-20260822-1314), likely because the settling retro was
absorbed in the utterance-checkpoint correction; the rule stands as
written and needs no sharpening — it was not followed, not unclear.

**2026-09-17 14:15Z REPAIR + update (LIGHT tick, cloud; resolve.py settled
1 new outside-view-veto forecast — BoE 25bp hike, `bc482ffb3606`, the
pre-registered discretionary-vote-veto test — and reconciling found 3
more from the 06:13:08Z Sweden Liberals settlement batch that never got a
table row; see RETRO-20260917-1415 for the full read):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Sweden Liberals re-forecast 1 (07a026bde227) | 0.23 / 0.49 | No | +0.260 | Yes | **−5.00** |
| Sweden Liberals re-forecast 2 (fb5dc4ef2365) | 0.12 / 0.47 | No | +0.350 | Yes | **−5.00** |
| Sweden Liberals re-forecast 3 (42edbef0f086) | 0.27 / 0.049 | No | +0.221 | Yes | **−5.00** |
| BoE 25bp hike (bc482ffb3606) | 0.20 / 0.061 | Yes | +0.139 | No | **−5.00** |

Mechanical ledger after this batch (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 143 settled declined forecasts, 135
fillable CF trades, 99 events, 56W/79L, pnl +$63.41, brier_delta +0.0370,
held-out +$67.42 (was 139/131/56W-75L/+$83.41/+0.0315/+$89.19 before this
batch). Ruling: no boundary change — three of the four rows are re-reads
of the same already-graded Sweden Liberals event (consistent with its
settled bet `b063db346052`, all No-side declines lost together), and the
BoE row is a clean confirmation that a discretionary MPC vote reads like
the self-model veto class, not a special case: the market (and the
Reuters poll it tracked) beat both the own estimate and the weaker LSEG/
SONIA secondary-sourced benchmarks that motivated the claimed edge. This
entry satisfies the per-row documentation duty without re-deriving the
running hand totals, per the 2026-09-06 operator note above.

**2026-09-18 14:10Z update (LIGHT tick, operator machine; resolve.py
settled 1 outside-view-veto forecast; full read in RETRO-20260918-1410):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| BTC touch-$80k Sep14-20 (61bc26d805b6) | 0.84 / 0.79 | Yes | +0.040 | Yes | **+1.25** |

Mechanical ledger after this row (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 144 settled declined forecasts, 136
fillable CF trades, 100 events, 57W/79L, pnl +$64.66, brier_delta +0.0367,
held-out +$68.67 (was 143/135/56W-79L/+$63.41/+0.0370/+$67.42). Ruling:
no boundary change - a 0.04 edge was never a veto-sized disagreement, and
the row is on this ledger only because of its label (same treatment as
`9618a7d0872d`). The label and the input both broke the touch-family
ruling above (DEEP-2026-09-01): touch rows are `unvalidated-method`, and
4 of the 6 modeled crypto touch rows recorded since that ruling
(`dde658c37455`, `61bc26d805b6`, `a28637cb4026`, `8d1eb46b7c32`) used a
guessed or swept vol. From this commit every touch estimate comes from
`strategy/tools/touch.py`, which refuses to run without a named, dated
`--vol-source`; the forecast note quotes its output. Settled measured-vol
rows stand at 3 of the 6 the re-grade needs (`edd6af85d6a6`,
`753366c2ea8e`, `fde4324641b4`), with `854536ded8be` open.

**2026-09-21 06:33Z update (FULL cycle, operator machine, local copy of a
diverged main; resolve.py settled 2 outside-view-veto forecasts from the
Sep 20 German election night; full read in RETRO-20260921-0633):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| MV AfD most seats (506bc4c8087e) | 0.90 / 0.77 | Yes | +0.120 | Yes | **+0.28** |
| Berlin CDU most seats (86267581486d) | 0.40 / 0.215 | Yes | +0.180 | No | −1.00 |

Net this batch: **−0.72u** (1W/1L). Mechanical ledger after these rows:
146 settled declined forecasts, 138 fillable CF trades, 102 events,
58W/80L, pnl +$61.07, brier_delta +0.0366, held-out +$70.09 (was
144/136/57W-79L/+$64.66/+0.0367/+$68.67; −$3.59 = +$1.41 − $5.00 ✓).
Ruling: no boundary change. Both rows are poll-Gaussian election
self-models; the one that won had the price OUTSIDE its whole sd-sweep
range (0.80-0.96 vs ask 0.77), the one that lost was a precedent-shaded
point estimate. Fork gate arithmetic stays with the deep retro.

**2026-09-21 update (DEEP-2026-09-21; settled by the deep retro's own
resolve.py run, graded same-commit per the DEEP-2026-08-23 rule; full
read in DEEP-2026-09-21 (c)):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| AfD most seats MV (506bc4c8087e) | 0.90 / 0.77 | Yes | +0.120 | Yes | **+0.28** |

Mechanical ledger after this row (`core/counterfactual.py ledger
--skip-reason outside-view-veto`, after `screen_replay.py events --limit
200`): 145 settled declined forecasts, 137 fillable CF trades, 101
events, 58W/79L, pnl +$66.07, brier_delta +0.0361, held-out +$70.08
(was 144/136/100/57W-79L/+$64.66/+0.0367/+$68.67). Ruling: no boundary
change — the model's inside view was right on this row (dB −0.0429,
market drifted toward it pre-election), but the pre-registered
relaxation fork, recomputed the same commit with this row included
(Status 2026-09-21 below), fails BOTH numeric gates for the first time;
one correct election call does not reopen a fork the newest fold is
failing on money and calibration at once.

**2026-09-21 update (RETRO-20260921-0625; settled by this cycle's
resolve.py run, graded same-commit per the DEEP-2026-08-23 rule):**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| CDU most seats Berlin (86267581486d) | 0.40 / 0.215 | Yes | +0.180 | No | −5.00 |

Mechanical ledger after this row (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 146 settled declined forecasts, 138
fillable CF trades, 102 events, 58W/80L, pnl +$61.07, brier_delta
+0.0366, held-out +$70.09 (was 145/137/101/58W-79L/+$66.07/+0.0361/
+$70.08). Ruling: no boundary change — CDU did not win the Berlin
election (Linke did, per the sibling Linke-Yes forecast lineage settled
the same cycle), so the veto correctly avoided another loss; one more
Yes-side loss added to the same behavioral-Gaussian-plurality class this
ledger already grades as its weakest.

**2026-09-21 17:3xZ update (RETRO-20260921-1730; FULL cycle, operator
machine; resolve.py settled 4 forecasts, 2 `outside-view-veto`, graded
same-commit per the DEEP-2026-08-23 rule).** Berlin SPD under 10% of
second votes, two snapshots of one market (`3748352`), both on the No
side, official SPD share 12.1% -> No, both declined trades WIN:

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Berlin SPD <10% (d0396e9b0cdd, Sep 12) | 0.20 / 0.40 | No | +0.161 | No | **+2.82** |
| Berlin SPD <10% (62f72f65c634, Sep 14) | 0.28 / 0.5675 | No | +0.274 | No | **+6.21** |

Mechanical ledger after these rows (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 148 settled declined forecasts, 140
fillable CF trades, 103 events, 60W/80L, pnl +$70.11, brier_delta
+0.0337, held-out +$79.12 (was 146/138/102/58W-80L/+$61.07/+0.0366/
+$70.09). One event, so one draw. Ruling: no boundary change. The veto
reason was honest (the No edge flipped sign between a full-poll mean and
a newest-poll-only mean), and the input-sensitivity rule above would
decline it again today. What the row adds: the market moved from 0.40 to
0.57 to 0.22 on no new poll, so a price swing on a thin state-election
bracket is not information about the centre.

**2026-09-21 22:1xZ update (RETRO-20260921-2215; LIGHT tick, cloud;
resolve.py settled 4 forecasts, 2 `outside-view-veto`, graded same-commit
per the DEEP-2026-08-23 rule).** MV SPD second-vote brackets, election
Sep20, official SPD share landed inside the >=31% bracket (own poll-mean
model correct on direction both times, wrong on the veto's implied side
once):

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| MV SPD >=31% (e056578ff5cf, Sep 14) | 0.81 / 0.86 | No | +0.040 | Yes | −5.00 |
| MV SPD 28-31% (52c0faf90ae2, Sep 14) | 0.24 / 0.095 | Yes | +0.140 | No | −5.00 |

Mechanical ledger after these rows (`core/counterfactual.py ledger
--skip-reason outside-view-veto`, after a fresh `screen_replay.py events`
sweep): 150 settled declined forecasts, 142 fillable CF trades, 100
events, 60W/82L, pnl +$60.11, brier_delta +0.0337, held-out +$69.12 (was
148/140/103/60W-80L/+$70.11/+0.0337/+$79.12 before this pair; the evts
drop from 103 to 100 is `screen_replay.py` re-clustering existing
mappings, not new data). Side split: no 105 rows/97 trades/46W-51L/
+$58.49; yes 45 rows/45 trades/14W-31L/+$1.62. Ruling: no boundary
change at n=2. Both rows are the SAME sd-sensitivity shape the veto was
built for (`e056578ff5cf`'s note: "sign holds (No) but size flips on the
sd judgment parameter"): the >=31% row's point estimate (0.81) sat on the
correct side of 0.5 but the veto declined the market-implied No edge
that the loose-sd tail created, and that declined No trade lost because
SPD did clear 31%. The 28-31% sibling declined a Yes-side edge built on
the same Gaussian and also lost, since the outcome landed in the >=31%
bucket, not 28-31%. Net: the veto avoided nothing here (the market was
right, the self-built Gaussian tails were not) — consistent with this
family's standing weakest-class read, not a new failure mode.

**2026-09-22 04:1xZ update (RETRO-20260922-0415; LIGHT tick, cloud;
resolve.py settled 0 bets and 4 forecasts, 1 `outside-view-veto`, graded
same-commit per the DEEP-2026-08-23 rule).** Berlin Grüne 14-17% of
second votes, official Grüne share landed inside the bracket (Yes) — the
declined No-side counterfactual trade lost:

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Berlin Grüne 14-17% (8601f47e8b85) | 0.50 / 0.625 | No | +0.120 | Yes | −5.00 |

Mechanical ledger after this row (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 151 settled declined forecasts, 143
fillable CF trades, 101 events, 60W/83L, pnl +$55.11, brier_delta
+0.0342, held-out +$63.30 (was 150/142/100/60W-82L/+$60.11/+0.0337/
+$69.12 before this row). Side split: no 106 rows/98 trades/46W-52L/
+$53.49; yes 45 rows/45 trades/14W-31L/+$1.62 (row adds to the No side).
Ruling: no boundary change at n=1. The row's own note put the No-side
edge at 0.116 by hand; the tool computes 0.120 and auto-tags subclass
`fact-finality` even though the note explicitly argues this is a
self-modeled Gaussian bucket, not a fact-final case — a labeling
mismatch worth a future reconcile pass, not acted on here. The veto
declined this exact class (behavioral point-estimate Gaussian, sd
sensitivity 0.074-0.169 across the note's own sweep) and it lost again,
consistent with the family's standing weakest-class read.

**2026-09-22 06:1xZ update (RETRO-20260922-0619; LIGHT tick, cloud;
resolve.py settled 0 bets and 5 forecasts, 2 `outside-view-veto`, graded
same-commit per the DEEP-2026-08-23 rule).** Claude Opus Sep21 release
market (4627751) settled No — the two declined No-side counterfactual
trades from the estimate's first two supersede snapshots both won (the
third and final snapshot, est 0.05, was `no-edge`, not on this table):

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Opus Sep21 snap 1 (668120246d84) | 0.04 / 0.3665 | No | +0.324 | No | +2.86 |
| Opus Sep21 snap 2 (d54f8f258424) | 0.68 / 0.8275 | No | +0.091 | No | +16.83 |

Mechanical ledger after these rows (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 153 settled declined forecasts, 145
fillable CF trades, 102 events, 62W/83L, pnl +$74.81, brier_delta
+0.0314, held-out +$82.99 (was 151/143/101/60W-83L/+$55.11/+0.0342/
+$63.30 before these rows). Side split: no 108 rows/100 trades/48W-52L/
+$73.18; yes 45 rows/45 trades/14W-31L/+$1.62 (both rows add to the No
side). Check: 73.18 + 1.62 = 74.80 ≈ 74.81 (rounding) ✓.

Ruling: no boundary change at n=2, both wins. Snapshot 2's own estimate
(0.68) was the weaker of the pair — it leaned toward Yes on an unsourced
book jump the row's own note admits it "cannot see behind" — but the veto
still declined the bet on estimate-distrust grounds regardless of
direction, and the declined No-side trade won anyway because the market
itself never fully priced the leak in either (No-side edge stayed
positive, just thinner: +0.324 at snapshot 1 down to +0.091 at snapshot
2). The veto is doing its job independent of estimate quality here; the
estimate-quality miss is graded in RETRO-20260922-0619, not this table.

**2026-09-22 08:1xZ update (RETRO-20260922-0813; FULL cycle, cloud;
resolve.py settled 0 bets and 3 forecasts, all 3 `outside-view-veto`,
graded same-commit per the DEEP-2026-08-23 rule).** Resident Evil
opening-weekend box office, three sibling brackets on the same event
(e:956520) — actual 3-day opening landed in the 60-65m bracket. The
declined No-side trade on 65-70m won; the declined Yes-side trade on
55-60m and the declined No-side trade on 60-65m both lost:

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Resident Evil 55-60m (94f5d2c84c0f) | 0.48 / 0.283 | Yes | +0.174 | No | -5.00 |
| Resident Evil 60-65m (9e900c404320) | 0.44 / 0.6255 | No | +0.131 | Yes | -5.00 |
| Resident Evil 65-70m (299cd54171c9) | 0.03 / 0.0955 | No | +0.061 | No | +0.50 |

Net this batch: **-$9.50** (1W/2L).

Mechanical ledger after these rows (`core/counterfactual.py ledger
--skip-reason outside-view-veto`): 156 settled declined forecasts, 148
fillable CF trades, 103 events, 63W/85L, pnl +$65.31, brier_delta
+0.0328, held-out +$66.00 (was 153/145/102/62W-83L/+$74.81/+0.0314/
+$82.99 before these rows). Side split: no 110 rows/102 trades/49W-53L/
+$68.68 (adds the two No-side rows, net -$4.50); yes 46 rows/46 trades/
14W-32L/-$3.38 (adds the one Yes-side row, -$5.00).

Ruling: no boundary change at n=3. The model's own ladder (50-55m 0.05,
55-60m 0.48, 60-65m 0.44, 65-70m 0.03) put the most weight one bracket
below where the market and the actual outcome landed — the row's own
note flagged this gap at record time ("the book sits one bracket above
the trade press") and it played out exactly that way. Box-office's
mechanical-ledger category line stays negative (13 rows, 6W/7L,
-$21.60, brier_delta +0.0117) — this batch is the veto's rationale
playing out as expected, not a new failure mode; the standing veto
stays shut.

**Box-office press-centre rule (RETRO-20261003-0015, evidence
`07bfb21eee33`).** Primetime 19-22M was recorded at 0.82 on a 20.0M press
centre with sd 1.0M; the note flagged a front-loaded opening (Fri incl
previews 32% of the weekend) and a book at 0.65/0.72 below the press, and
kept the shaded ~0.72 view unrecorded. Actuals landed at $18.83M, below
even the studio's $19.2M Sunday estimate. This is the second box-office
bracket where the book beat the trade-press centre (Spider-Man above).
Rule: when Fri-incl-previews share is >= 30% or the book sits below the
press centre, centre on the LOWEST credible press figure, use sd >= 1.5M,
and record that as est_prob. A shade written in the note but not recorded
is the honest estimate left out. Box-office forecasts n=26, mean dBrier
+0.0117. The category stays a standing no-bet self-model.
Tally (RETRO-20261005-2210): post-rule rows 4 (2 events), net dBrier
-0.59. Verity OW 30-32M/32-34M beat the book by -0.40/-0.21 (actual
32-34M, at the press centre; the book over-priced the front-loaded low
end). RE weekend-3 12-13M lost +0.049 at sd 0.6M. On weekend 3 or
later, when press and the Fri multiple agree inside one bracket, use
sd <= 0.4M. Box-office n=32, mean dBrier -0.0083. Still no-bet; review
at 6 post-rule events.
Tally (RETRO-20261006-0016): Digger OW <9M (`837ebfc5d863`) recorded 0.55
vs mid 0.92, WON (actual ~$8.0M, Variety), dBrier +0.196. The rule was
misapplied: the note centred on "lowest credible ~9.5M", but the lowest
credible figure on file was BOT's 7.5M floor, and Fri incl previews was
~50% of the press weekend. "Lowest credible" means the lowest figure any
listed source gives, not the lowest of the Fri-night projections. When
Fri incl previews is >= 40%, the Fri-night weekend projection ran ~20%
high (10M vs 8M). Post-rule rows 5 (3 events), net dBrier -0.39.
Box-office n=33, mean dBrier -0.0021. Still no-bet.
Tally + rule change (RETRO-20261012-2215, evidence `d60414387526`,
`f587533db89c`, `313457179cc4`, `be436d82c541`): Other Mommy OW and Verity
wk2 both landed in the BOOK's modal bracket (0.73 / 0.56) while my ladders
split mass onto neighbours (peaks 0.47 / 0.30); net dBrier +0.693 on 5
rows. Post-rule rows 10 (5 events), net dBrier +0.30 -- the rule now loses
to the book. Box-office n=38, mean dBrier ~+0.016. Changes: (1) the
Digger "Fri-night projection runs ~20% high" haircut is RETIRED as a
standalone override (n=1, refuted by Other Mommy where Deadline's Fri-night
27.5M held). (2) Book-modal floor: when recording Fri-night/Sat brackets and
the book's modal bracket mid is >= 0.55 and lies within one bracket of my
press centre, the book has likely seen Saturday tracking I cannot read --
record that bracket at >= (book mid - 0.10) and rescale neighbours. My own
sd of 1.3-1.5M is too wide once Friday actuals are in; use sd <= 1.0M on
the press centre. Still no-bet; review at 8 post-rule events.
Tally (RETRO-20261013-0015, evidence `ed7635ddee76`, `fb375510e91e`,
`6f41bbf55b7b`, `f82d5a3aba56`): Social Reckoning OW landed 5-7M, at
Sony's $6M Sat-AM projection; the book's modal <5M (0.72 at 12:19Z, 0.56 at
22:17Z) was wrong. My 4 rows net dBrier -0.408. Post-rule rows 14 (6
events), net ~-0.11 -- the press centre is back ahead of the book on
aggregate. The book-modal floor (adopted after these rows were recorded)
would have COST here: <5M floored at 0.625 and 5-7M rescaled to ~0.32 at
12:19Z adds ~+0.13 dBrier (the 22:17Z book at 0.56 floors at 0.46, below my
0.50, no effect). Floor record: helped 2 events, hurt 1. Kept unchanged
(n=3), but the floor is a ceiling on confidence in the book, not a rule
that the book is right: when the press centre is a studio Sat-AM figure
already built on Friday actuals, note that in the row. Box-office forecasts
n=42, sum dBrier +0.217, mean +0.0052. Still no-bet.
Tally (RETRO-20261019-2215, evidence `67b2e0620a7c`): Street Fighter OW
30-33M ("tighter brackets" duplicate market) recorded 0.71 vs mid 0.85, WON,
dBrier +0.062. Two rules were skipped in the note: sd 1.2 was used on a
Sat-AM figure built on Friday actuals (cap is sd <= 1.0M -> 0.77), and the
book-modal floor was applied to the coarse 30-35M ladder only, not to the
30-33M market (own mid 0.85 -> floor 0.75). Clarification: the floor and
the sd cap apply to EVERY bracket ladder recorded in a note, including
tighter-bracket duplicates, each against its own book mid. Still no-bet.
Tally (RETRO-20261020-0015, evidence `dec2436888e4`, `8d2ceddf0083`,
`81ffde79e0d2`, `06983792d928`, `dc8bff937fef`): Street Fighter OW landed
30-35M, the book's modal bracket at both record times. 5 coarse-ladder rows
net dBrier +0.226 (event incl. 67b2e0620a7c: +0.288 over 6 rows). Fri-update
rows centred on the low end of Deadline's "30M, maybe 30M+" (centre on the
bracket edge, 50/50 split); Sat-AM rows used sd 1.2 over the 1.0M cap. Floor
record: helped 3, hurt 1 (frozen; no re-tune). Box-office forecasts n=48.
Still no-bet.

**2026-09-22 ~18:15Z update (FULL cycle, cloud; resolve.py settled 14
forecasts, 2 `outside-view-veto`).** Both rows are the Trump x Greenland
deal-by-Sep23 pair (market 4712116), `fact-finality` subclass (signing
scheduled/expected during UNGA week but not yet an immutable fact at
research time) — two separate forecasts on the same market at different
times of day, not a supersession: the No-side row (935afbfc7d19,
researched 2026-09-20 00:18Z, est No=0.40 vs mid 0.25) and the Yes-side
row (a893f32972f0, researched 2026-09-20 12:18Z, est Yes=0.90 vs mid
0.74). The deal was in fact signed before the Sep23 deadline: market
resolved Yes.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Trump-Greenland Sep23 No (935afbfc7d19) | 0.40 / 0.25 | No | +0.140 | Yes | -5.00 |
| Trump-Greenland Sep23 Yes (a893f32972f0) | 0.90 / 0.74 | Yes | +0.150 | Yes | +1.67 |

Net this batch: **-$3.33** (1W/1L). Mechanical ledger after these rows
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 158
settled declined forecasts, 150 fillable CF trades, 104 events, 64W/86L,
pnl +$61.97, brier_delta +0.0327, held-out +$62.67 (was 156/148/103/
63W-85L/+$65.31/+0.0328/+$66.00 before these rows). Side split: no 111
rows/103 trades/49W-54L/+$63.68 (adds the No-side row, -$5.00); yes 47
rows/47 trades/15W-32L/-$1.71 (adds the Yes-side row, +$1.67).

Ruling: no boundary change at n=2. Both rows are `fact-finality`
subclass (37 rows, +$95.69, the ledger's single best-performing
subclass) — this pair nets slightly negative (-$3.33) but sits well
inside that subclass's noise. The Yes-side row is the more interesting
one: the veto correctly followed its own rule (signing not yet an
immutable fact at research time) on a trade that would have paid
(edge 0.15, and it won) — the known, already-quantified cost of keeping
this gate shut rather than a new failure mode. Full grading in
RETRO-20260922-1815.

**2026-09-22 20:15Z update (FULL cycle, cloud; 3 `ai-model-release`
veto rows settled — Claude Opus release markets, both resolved Yes,
see RETRO-20260922-2015).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Opus by-Sep30 first read (`b52006c6d15c`) | 0.70 / 0.805 | No | +0.100 | Yes | -5.00 |
| Opus by-Sep30 re-check (`7f1358aa709a`) | 0.60 / 0.855 | No | +0.240 | Yes | -5.00 |
| Opus exact-Sep22 re-check (`9ca6adf96fc8`) | 0.62 / 0.732 | No | +0.098 | Yes | -5.00 |

Net this batch: **-$15.00** (0W/3L). Mechanical ledger after these rows
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 161
settled declined forecasts, 153 fillable CF trades, 106 events, 64W/89L,
pnl +$46.97, brier_delta +0.0337, held-out +$39.84 (was 158/150/104/
64W-86L/+$61.97/+0.0327/+$62.67 before these rows). Side split: no 114
rows/106 trades/49W-57L/+$48.68 (adds these three No-side losses,
-$15.00); yes 47 rows/47 trades/15W-32L/-$1.71 (unchanged).

Ruling: no boundary change at n=3. Same shape as every other
`ai-model-release` veto row in this table — model directionally right,
market closer, veto correctly withheld the bet. The sibling wide-spread-
veto row on the same event family (`3de604a7cf7a`, exact-Sep22 first
read) is entered below with the same-cycle REPAIR batch. Full grading in
RETRO-20260922-2015.

**2026-09-22 20:15Z REPAIR + update (FULL cycle, cloud; one
`wide-spread-veto` row from this cycle's `ai-model-release` settlements,
plus two pre-existing gaps `core/counterfactual.py reconcile` surfaced
while preparing this entry — neither caught by a prior retro nor by the
reconcile tool's own check, which only scans `outside-view-veto`; see
RETRO-20260922-2015 for how each was found).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Opus exact-Sep22 first read (`3de604a7cf7a`, wide-spread-veto) | 0.48 / 0.6855 | No | +0.127 | Yes | -5.00 |
| Berlin Linke 5-10% margin (`3723b83673c1`, wide-spread-veto, settled 2026-09-22T02:03:42Z, graded in RETRO-20260922-0211, flagged missing by the 10:25Z TRIGGERED cycle today) | 0.40 / 0.754 | No | +0.109 | Yes | -5.00 |
| Lowe's GAAP EPS beat (`df7062f3e89d`, wide-spread-veto, settled 2026-08-19T15:21:17Z, graded in RETRO-20260819-1522, never entered since) | 0.62 / 0.595 | Yes | -0.260 | Yes | +0.68 |

Net this batch: **-$9.32** (1W/2L, on rows spanning three different
settlement dates). Mechanical ledger after these rows
(`core/counterfactual.py ledger --skip-reason wide-spread-veto`): 17
settled declined forecasts, 15 fillable CF trades, 2 refused, 8W/7L,
pnl -$17.99, brier_delta -0.0327, held-out -$15.17 (was 15/13/2 refused/
8W-5L/-$7.99/-0.0684/-$3.67 before the two No-side additions; the
Lowe's row's pnl was always inside these totals — settled over a month
before the 09-17 baseline above — so only its table row is new, not its
contribution to the sums). Side split: no 9 rows/7 trades/2W-5L/-$17.74
(adds the two new No-side losses, -$10.00, was 7/5/2W-3L/-$7.74);
yes 8 rows/8 trades/6W-2L/-$0.25 (unchanged — Lowe's was already
counted here).

Ruling: no boundary change at n=3 across two unrelated events plus one
documentation-only backfill. The Lowe's row is the interesting one on
method, not P&L: the "modest apparent edge" the original research
quoted was against the market's *mid* (0.595); the mechanical ledger
fills at the actual best ask (0.88) on an incoherent, spread-blown book,
which turns the same row negative (-0.260) — the veto's own reasoning
("if this is genuine live news the architecture cannot win the race
anyway") was right for a reason beyond the spread-gate mechanics: the
apparent edge was a mid-price illusion. It won on Yes anyway (small,
+$0.68, priced by the bad ask it would have had to pay), which is a
lucky fill outcome, not evidence the mid-based edge was ever real.
Full grading in RETRO-20260922-2015; RETRO-20260922-0211 and
RETRO-20260819-1522 (unmodified) hold the original narrative grading
for the other two rows.

**2026-09-22 22:14Z update (LIGHT tick, cloud; 1 `outside-view-veto` row
settled — GPT Luna release, see RETRO-20260922-2214).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| GPT Luna release by-Sep22 (`328f88bd8da0`) | 0.45 / 0.7205 | No | +0.251 | Yes | -5.00 |

Net this batch: **-$5.00** (0W/1L). Mechanical ledger after this row
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 162
settled declined forecasts, 154 fillable CF trades, 107 events, 64W/90L,
pnl +$41.97, brier_delta +0.0349, held-out +$34.84 (was 161/153/106/
64W-89L/+$46.97/+0.0337/+$39.84 before this row). Side split: no 115
rows/107 trades/49W-58L/+$43.68 (adds this No-side loss, -$5.00); yes 47
rows/47 trades/15W-32L/-$1.71 (unchanged).

Ruling: no boundary change at n=1. Same shape as every other
`ai-model-release` veto row in this table — model directionally right
(real chance of a release today) but underweighted (0.45 vs a market at
0.72 that turned out closer to right), veto correctly withheld the bet.
Full grading in RETRO-20260922-2214.

**2026-09-23 22:1xZ update (LIGHT tick, cloud; 1 `outside-view-veto` row
settled — 30y Treasury hit 5.39%, see RETRO-20260923-2215).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| 30y Treasury hit 5.39% Sep (`03f07792d701`) | 0.42 / 0.615 | No | +0.180 | Yes | -5.00 |

Net this batch: **-$5.00** (0W/1L). Mechanical ledger after this row
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 163
settled declined forecasts, 155 fillable CF trades, 108 events, 64W/91L,
pnl +$36.97, brier_delta +0.0358, held-out +$29.84 (was 162/154/107/
64W-90L/+$41.97/+0.0349/+$34.84 before this row). Side split: no 116
rows/108 trades/49W-59L/+$38.68 (adds this No-side loss, -$5.00); yes 47
rows/47 trades/15W-32L/-$1.71 (unchanged). Check: 38.68 + (-1.71) = 36.97.

Ruling: no boundary change at n=1. A self-modeled driftless touch read
(close-only reflection) lost to a single-day +11bp 30y print on Sep 23
(5.29 -> 5.40) that also hit the 10y 5.10 and 5y 4.90 rungs the same day
— one rates-selloff event, not three independent confirmations. The veto
correctly withheld the No bet. Full grading in RETRO-20260923-2215.

**2026-09-24 00:1xZ update (LIGHT tick, cloud; 1 `outside-view-veto` row
settled — Xi Jinping in US by Sep 23 resolved Yes, see
RETRO-20260924-0015).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Xi visit by Sep23 (`f5e8ad23ec2c`) | 0.75 / 0.895 | No | +0.140 | Yes | -5.00 |

Net this batch: **-$5.00** (0W/1L). Mechanical ledger after this row
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 164
settled declined forecasts, 156 fillable CF trades, 109 events, 64W/92L,
pnl +$31.97, brier_delta +0.0359, held-out +$24.84 (was 163/155/108/
64W-91L/+$36.97/+0.0358/+$29.84 before this row). Side split: no 117
rows/109 trades/49W-60L/+$33.68 (adds this No-side loss, -$5.00); yes 47
rows/47 trades/15W-32L/-$1.71 (unchanged). Check: 33.68 + (-1.71) = 31.97.

Ruling: no boundary change at n=1. A compounded arrival-day haircut on an
unofficial itinerary lost to the market; the next-day supersede already
corrected it on sourced logistics. The veto correctly withheld the No bet.
Full grading in RETRO-20260924-0015.

**2026-09-24 17:2xZ update (FULL cycle, operator machine; 2
`outside-view-veto` rows settled on the Xi State Arrival utterance
event, see RETRO-20260924-1729).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Xi arrival "China" 5+ (`ec3c94c891d7`) | 0.62 / 0.475 | Yes | +0.130 | No | -5.00 |
| Xi arrival "Ballroom" (`6302b86d1d9a`) | 0.85 / 0.735 (No) | No | +0.110 | No | +1.76 |

Net this batch: **-$3.24** (1W/1L). Mechanical ledger after these rows
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 166
settled declined forecasts, 158 fillable CF trades, 111 events, 65W/93L,
pnl +$28.73, brier_delta +0.0361, held-out +$17.83 (was 164/156/109/
64W-92L/+$31.97/+0.0359/+$24.84). Side split: no 118 rows/110 trades/
50W-60L/+$35.44 (adds Ballroom +$1.76); yes 48 rows/48 trades/15W-33L/
-$6.71 (adds China 5+ -$5.00). Check: 35.44 + (-6.71) = 28.73.

Ruling: no boundary change. The Yes-side block was correct (the estimate
itself was wrong, see the count-threshold note in the utterance section);
the No-side block on a 0/4 speaker-only base rate cost a small winner at
an edge just over 0.10. One row each, too few to move the boundary.

**2026-09-24 22:1xZ update (LIGHT tick, cloud; 2 `outside-view-veto`
rows settled on the 30y Treasury Sep ladder, see RETRO-20260924-2213).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| 30y Treasury hit 5.42% Sep (`7771a4b3b7ac`) | 0.33 / 0.245 | Yes | -0.040 | Yes | +8.51 |
| 30y Treasury hit 5.45% Sep (`b8d163385f59`) | 0.20 / 0.106 | Yes | +0.090 | Yes | +40.45 |

Net this batch: **+$48.96** (2W/0L). Mechanical ledger after these rows
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 168
settled declined forecasts, 160 fillable CF trades, 111 events, 67W/93L,
pnl +$77.70, brier_delta +0.0340, held-out +$66.80 (was 166/158/111/
65W-93L/+$28.73/+0.0361/+$17.83). Side split: no 118 rows/110 trades/
50W-60L/+$35.44 (unchanged); yes 50 rows/50 trades/17W-33L/+$42.26 (adds
both rows). Check: 35.44 + 42.26 = 77.70.

Ruling: no boundary change. Both rows belong to the same rates-selloff
event as the 5.39 No-side loss (`03f07792d701`). Events stay at 111, and
the ladder family nets +$43.96 on one event. The dip-below-5.21 leg
(`3e4351bdb5c6`) is still open.

**2026-09-25 03:1xZ update (FULL cycle, operator machine; 2
`outside-view-veto` + 3 `wide-spread-veto` rows settled on the Xi
state-dinner toast, see RETRO-20260925-0315).**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Xi toast "Economy" (`9a7a77a71c00`, outside-view-veto) | 0.22 / 0.435 | No | +0.200 | No | +3.62 |
| Xi toast "SI" (`ab5a3803b119`, outside-view-veto) | 0.35 / 0.665 | No | +0.260 | No | +7.82 |
| Xi toast "Trump" (`d805d4abc7c9`, wide-spread-veto) | 0.11 / 0.22 | No | +0.070 | No | +1.10 |
| Xi toast "Garden/Rose" (`cdabc385b3cb`, wide-spread-veto) | 0.15 / 0.28 | No | +0.040 | No | +1.17 |
| Xi toast "Million" 5+ (`b1957ef7af26`, wide-spread-veto; then bet as `674b6cfac193`) | 0.06 / 0.125 | No | +0.060 | No | +0.68 |

Outside-view-veto: **+$11.44** (2W/0L). Mechanical ledger now 170 rows /
162 trades / 113 events / 69W-93L / +$89.14 / dBrier +0.0309 / held-out
+$78.24 (was 168/160/111/67W-93L/+$77.70/+0.0340/+$66.80). Side split:
no 120/112/52W-60L/+$46.88 (adds both); yes 50/50/17W-33L/+$42.26
(unchanged). Check: 46.88 + 42.26 = 89.14.

Wide-spread-veto: **+$2.95** (3W/0L). Ledger now 20 rows / 18 trades /
11W-7L / -$15.04 / dBrier -0.0330 / held-out -$12.22 (was 17/15/8W-7L/
-$17.99/-0.0327/-$15.17). Side split: no 12/10/5W-5L/-$14.79 (adds all
three); yes 8/8/6W-2L/-$0.25 (unchanged). Check: -14.79 + -0.25 = -15.04.

Ruling: no boundary change. One event; the Million row duplicates a
placed bet. The No-side speaker-only tally in the utterance section
tracks whether the 0.10 boundary costs this family winners.

**2026-09-25 06:44Z update (LIGHT tick, cloud; 1 `outside-view-veto` row
settled, Xi state-dinner toast "Melania," see RETRO-20260925-0644.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Xi toast "Melania" (`5ee6e91cd3d2`) | 0.83 / 0.68 | Yes | +0.110 | Yes | +1.94 |

Net this batch: **+$1.94** (1W/0L). Mechanical ledger after this row
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 171
rows / 163 trades / 114 events / 70W-93L / +$91.08 / dBrier +0.0303 /
held-out +$85.20 (was 170/162/113/69W-93L/+$89.14/+0.0309/+$78.24). Side
split: no 120/112/52W-60L/+$46.88 (unchanged); yes 51/51/18W-33L/+$44.20
(adds this row). Check: 46.88 + 44.20 = 91.08.

Ruling: no boundary change. Same speaker-only Melania base rate family as
the arrival-toast row (`8b059c23c86a`, also won); the veto keeps declining
a real edge on a small-n base rate that keeps paying off, but n=2 same-day
same-family rows is not independent evidence for loosening it.

**2026-09-25 07:48Z update (FULL cycle, operator machine; 1
`outside-view-veto` row settled, Xi state-dinner toast "Ballroom," see
RETRO-20260925-0748.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Xi toast "Ballroom" (`f0790f007a85`) | 0.15 / 0.315 | No | +0.140 | Yes | -5.00 |

Net this batch: **-$5.00** (0W/1L). Mechanical ledger after this row:
172 rows / 164 trades / 115 events / 70W-94L / +$86.08 / dBrier +0.0316 /
held-out +$80.20 (was 171/163/114/70W-93L/+$91.08/+0.0303/+$85.20). Side
split: no 121/113/52W-61L/+$41.88 (adds this row); yes 51/51/18W-33L/
+$44.20 (unchanged). Check: 41.88 + 44.20 = 86.08.

Ruling: no boundary change. The veto did its job: it kept a $5 loss off
the ledger. See the utterance section for the tally and the topical-word
analogue rule.

**2026-09-23 DEEP REPAIR (documentation-only backfill; no totals
change).** `core/counterfactual.py reconcile` lists 9 settled
outside-view-veto rows graded narratively in this section ("named
elsewhere in the section") but never entered as table rows — all
settled 2026-08-10 through 2026-09-02, before or during the era when
the table format stabilised. Their P&L has ALWAYS been inside the
mechanical ledger's running totals (the tool reads forecasts.jsonl
directly), so the totals above (162 rows / 154 trades / 64W/90L /
+$41.97 / +0.0349) are unchanged by this entry; only the table rows
were missing. Values below are the mechanical ledger's own (est/mkt in
own-side convention, CF P&L at $5 flat):

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Hong WI primary <5% (`03901079bd63`) | 0.09 / 0.089 | Yes | -0.017 | No | -5.00 |
| Hichilema Zambia (`fa185b55a5c3`) | 0.87 / 0.92 | No | +0.040 | Yes | -5.00 |
| Musk 140-159 tweets (`70331099597c`) | 0.007 / 0.052 | No | +0.044 | No | +0.27 |
| Musk 160-179 tweets (`c24926a5c9d7`) | 0.205 / 0.175 | Yes | +0.025 | Yes | +22.78 |
| Musk 200-219 tweets (`7808b6f5a4ef`) | 0.215 / 0.265 | No | +0.045 | No | +1.76 |
| Gold hit $4,600 Aug (`90fafe7b3c2a`) | 0.327 / 0.219 | Yes | +0.099 | Yes | +16.93 |
| Spider-Man domestic gross (`e9f9221a3afb`) | 0.90 / 0.85 | Yes | +0.040 | Yes | +0.81 |
| Beijing 26°C Aug 25 (`25cb8672c568`) | 0.23 / 0.22 | Yes | +0.000 | No | -5.00 |
| GPT-6 by Sep 15 (`846f0e23a43a`) | 0.28 / 0.865 | No | +0.570 | Yes | -5.00 |

Batch sum +$22.55 (5W/4L) — already counted in every total above and
below since the rows settled.

Units note for future reconcile reads (DEEP-2026-09-23): per-row CF P&L
in this section's tables is DOLLARS at the $5 flat stake; `reconcile`
prints per-row pnl in 1u = pnl/5 units, so a hand `-5.00` against a
ledger `-1.00u` is the SAME number, not a diff. Of the 71 "C. rows in
both that differ" in today's reconcile run, ~60 are exactly this units
convention; the residue is (i) early rows whose hand edge was quoted
against the MID rather than the realizable ask (Astra 0.783-hand vs
0.056-ledger is the worst; the Lowe's row in the 2026-09-22 REPAIR
documents the same mid-vs-ask illusion), and (ii) rows the fill model
refuses (entry outside [0.02, 0.95] or no bid) where the hand table
recorded a fill anyway. Historical rows are NOT being rewritten to
match — the mechanical ledger is authoritative for every ruling and
gate; the hand table is the narrative index. An operator proposal to
make `reconcile` units-aware and to extend its B-check beyond
outside-view-veto is filed in journal/proposals.md (2026-09-23 pass).

**2026-09-26 20:1xZ update (FULL cycle, cloud; MrBeast v9QtM6qnG50 wk1
settled 70-80M Yes: 2 `outside-view-veto` + 2 `wide-spread-veto` rows,
see RETRO-20260926-2015.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| MrBeast wk1 60-70M (`92a9d80fc3c3`) | 0.59 / 0.3835 | Yes | +0.198 | No | -5.00 |
| MrBeast wk1 70-80M (`8adb0a184d87`) | 0.40 / 0.625 | No | +0.210 | Yes | -5.00 |
| MrBeast wk1 60-70M wide-spread (`d842a0332a5a`) | 0.18 / 0.094 | Yes | +0.045 | No | -5.00 |
| MrBeast wk1 70-80M wide-spread (`5badc7031d2c`) | 0.82 / 0.9045 | No | +0.040 | Yes | -5.00 |

Outside-view-veto net this batch: **-$10.00** (0W/2L). Mechanical ledger
after these rows: 175 rows / 167 trades / 71W-96L / +$77.41 / dBrier
+0.0332 / held-out +$71.52 (was 173/165/71W-94L/+$87.41). Side split: no
123/115/53W-62L/+$38.21 (adds 8adb); yes 52/52/18W-34L/+$39.20 (adds
92a9). Check: 38.21 + 39.20 = 77.41.
Wide-spread-veto: **-$10.00** (0W/2L). Ledger now 22 rows / 20 trades /
11W-9L / -$25.04 / dBrier -0.0279 / held-out -$17.22 (was 20/18/11W-7L/
-$15.04). Side split: no 13/11/5W-6L/-$19.79 (adds 5badc); yes 9/9/6W-3L/
-$5.25 (adds d842). Check: -19.79 + -5.25 = -25.04.

Ruling: no boundary change. Both vetoes kept real losses off the ledger;
the outside-view pair is the textbook undated-count case the
cumulative-count anchor rule exists for (the est rested on an inferred,
not observed, pace).

**2026-10-03 21:15Z update (FULL cycle, operator machine; Musk Oct1-3
07:46Z pair, both superseded at 19:03Z, see RETRO-20261003-2115.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Musk Oct1-3 65-89 (`9238c01df3f3`) | 0.84 / 0.575 | Yes | +0.260 | Yes | +3.62 |
| Musk Oct1-3 40-64 (`eda7406d6518`) | 0.12 / 0.36 | No | +0.230 | No | +2.69 |

Net this batch: **+$6.31** (2W/0L). Mechanical ledger after these rows
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 202 rows /
194 trades / 83W-111L / +$126.52 / dBrier +0.0320 / held-out +$135.62. Side
split: no 138/130/60W-70L/+$95.58; yes 64/64/23W-41L/+$30.94. Check: 95.58 +
30.94 = 126.52. Ruling: no boundary change at one event; the 19:03Z revision
of the same family lost to the market, so the early read was not a
repeatable method yet.

**2026-10-05 0403Z update (LIGHT tick, operator machine; Brazil R1 "Lula
most votes" re-forecast settled, see RETRO-20261005-0403.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Brazil R1 Lula most votes (`a37c2c7b10f9`) | 0.55 / 0.625 | No | +0.070 | No | +8.16 |

Net this batch: **+$8.16** (1W/0L). Mechanical ledger after this row
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 203 rows /
195 trades / 84W-111L / +$134.67 / dBrier +0.0314 / held-out +$143.78 (was
202/194/83W-111L/+$126.52/+0.0320/+$135.62 before this row). Side split: no
139/131/61W-70L/+$103.73 (adds this win); yes 64/64/23W-41L/+$30.94
(unchanged). Check: 103.73 + 30.94 = 134.67. Ruling: no boundary change at
n=1 — the veto correctly shaded below an overconfident market mid (own
0.55 vs mkt 0.625) on a plurality call the market itself also got wrong in
direction relative to the final count, so the No-side fill at 0.38 would
have won. The older, since-superseded forecast on the same market
(`1d98458aef28`, est 0.65, skip_reason `category-bar` — not a veto, no
table duty) settled the same tick at the same loss-avoided shape, two
minutes earlier per settled_ts. Full narrative in RETRO-20261005-0403.

**2026-10-05 0527Z update (FULL cycle, operator machine; seven Brazil R1
family veto rows settled, see RETRO-20261005-0527.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Brazil Lula by 5-10 (`7ae14fb4b36e`) | 0.35 / 0.12 | Yes | +0.220 | No | -5.00 |
| Brazil Flávio >=39 valid (`4e52c227a60f`) | 0.45 / 0.85 | No | +0.390 | Yes | -5.00 |
| Brazil Lula 2nd (`b350adc7e95c`) | 0.15 / 0.2815 | No | +0.131 | Yes | -5.00 |
| Brazil Lula by <5 (`0137c5dd7495`) | 0.50 / 0.585 | No | +0.080 | No | +6.90 |
| Brazil Flávio >=39 valid (`e6afa32bb249`) | 0.84 / 0.88 | No | +0.030 | Yes | -5.00 |
| Brazil Lula 2nd (`9f0ee045afca`) | 0.45 / 0.3795 | Yes | +0.063 | Yes | +7.90 |
| Brazil Lula by <5 (`1c876ec5d358`) | 0.42 / 0.475 | No | +0.050 | No | +4.45 |

Net this batch: **-$0.75** (3W/4L). Mechanical ledger after these rows: 210
rows / 202 trades / 87W-115L / +$133.93 / dBrier +0.0321 / held-out
+$141.93 (was 203/195/84W-111L/+$134.67). Side split: no 144/136/63W-73L/
+$100.07; yes 66/66/24W-42L/+$33.86. Check: 100.07 + 33.86 = 133.93.
Ruling: no boundary change at one event. The four losses are all Sep 21-30
reads (raw-share and incoherent-sibling errors); the three wins are the
Sep 30 to Oct 3 reads from one stated margin distribution.

**Backfill (same 05:27Z cycle; reconcile.py flagged three settled veto rows
that no retro tabled. The mechanical totals above already count them.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| "Primetime" OW 19-22m (`07bfb21eee33`, OVV) | 0.82 / 0.685 | Yes | +0.100 | No | -5.00 |
| ChatGPT exactly 2 outages Sep (`fe02bf0c9670`, OVV) | 0.15 / 0.915 | No | +0.720 | Yes | -5.00 |
| Gas < $3.75 any state Sep 30 (`0bee87f8d628`, WSV) | 0.03 / 0.24 | No | +0.030 | No | +0.32 |

Wide-spread-veto mechanical ledger now (`core/counterfactual.py ledger
--skip-reason wide-spread-veto`): 44 rows / 35 trades / 21W-14L / -$35.37 /
dBrier -0.0061. Ruling: no change; both OVV misses are the veto working
(the ChatGPT row's 0.15 was the largest claimed edge of the window and lost).

**2026-10-05 0752Z update (LIGHT tick, operator machine; two Brazil R1 veto rows settled, see RETRO-20261005-0752.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Brazil Flávio 2nd (`22d7ab1cf2f3`, superseded) | 0.85 / 0.72 | Yes | +0.120 | No | -5.00 |
| Brazil Renan Santos 3rd (`c9e0968700d5`) | 0.45 / 0.515 | No | +0.060 | No | +5.20 |

Net this batch: **+$0.20** (1W/1L). Mechanical ledger after these rows
(`core/counterfactual.py ledger --skip-reason outside-view-veto`): 212 rows /
204 trades / 88W-116L / +$134.14 / dBrier +0.0325 / held-out +$142.14 (was
210/202/87W-115L/+$133.93/+0.0321/+$141.93 before these rows). Side split: no
137/137/64W-73L/+$105.28; yes 67/67/24W-43L/+$28.86. Check: 105.28 + 28.86 =
134.14. Ruling: no boundary change at one election night. The Flávio 2nd
pair (mirror of the Lula-2nd leg that resolved Yes) is the loss; the Santos
3rd pair is the win.

**2026-10-05 1017Z update (FULL cycle, operator machine; two Brazil R1 share-leg veto rows settled, see RETRO-20261005-1017.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Brazil Lula >=44 valid (`467f58b0ad62`, superseded) | 0.62 / 0.715 | No | +0.080 | Yes | -5.00 |
| Brazil Flávio 45-48 valid (`77ea98a905f9`) | 0.78 / 0.885 | No | +0.090 | Yes | -5.00 |

Net this batch: **-$10.00** (0W/2L), so the veto saved $10. Mechanical
ledger after these rows (`core/counterfactual.py ledger --skip-reason
outside-view-veto`): 214 rows / 206 trades / 88W-118L / +$124.14 / dBrier
+0.0327 / held-out +$132.14 (was 212/204/88W-116L/+$134.14). Side split:
no 147/139/64W-75L/+$95.28; yes 67/67/24W-43L/+$28.86. Check: 95.28 +
28.86 = 124.14. Ruling: no boundary change. Both rows sat 0.08-0.09 below
the book on self-built models (PT-share poll correction; live-count drift
model), and the book was right both times.

**2026-10-06 0016Z update (FULL cycle, operator machine; two DF Senate
2nd-place veto rows settled, see RETRO-20261006-0016.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| DF Senate Bia Kicis 2nd (`5810b4aba221`) | 0.65 / 0.8245 | No | +0.170 | Yes | -5.00 |
| DF Senate Leila 2nd (`87034354d243`) | 0.31 / 0.125 | Yes | +0.180 | No | -5.00 |

Net this batch: **-$10.00** (0W/2L), so the veto saved $10. Mechanical
ledger after these rows: 226 rows / 218 trades / 93W-125L / +$141.47 /
dBrier +0.0309 / held-out +$148.91. Side split: no 156/148/69W-79L/
+$127.61; yes 70/70/24W-46L/+$13.86. Check: 127.61 + 13.86 = 141.47.
Ruling: no boundary change. Both rows applied a half-weight left-ward
poll correction against the bolsonarista DF electorate, and the book's
right-ward read was correct. This is the second Brazil R1 batch where a
self-built poll correction lost to the book.

**2026-10-06 0019Z update (LIGHT tick, cloud; DF Senate 2nd-place veto pair settled, see RETRO-20261006-0019.)**

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| DF Senate Bia Kicis 2nd (`5810b4aba221`) | 0.65 / 0.8245 | No | +0.170 | Yes | -5.00 |
| DF Senate Leila do Volei 2nd (`87034354d243`) | 0.31 / 0.125 | Yes | +0.180 | No | -5.00 |

Net this batch: **-$10.00** (0W/2L), so the veto saved $10. Mechanical
ledger after these rows (`core/counterfactual.py ledger --skip-reason
outside-view-veto`): 226 rows / 218 trades / 93W-125L / +$141.47 / dBrier
+0.0309 / held-out +$148.91. Side split: no 156/148/69W-79L/+$127.61; yes
70/70/24W-46L/+$13.86. Check: 127.61 + 13.86 = 141.47. Ruling: no boundary
change. Both rows were one self-built read (half-weight on a right-wing
consolidation story against three polls that had Leila level or ahead), and
the book's Bia 0.82 was right. reconcile.py still lists 12 older
veto/wide-spread rows (Sep 28 - Oct 1) missing from this hand table: a
backlog for the next deep retro, not graded on this LIGHT tick.

**2026-10-06 0211Z backfill (FULL cycle, cloud; reconcile.py's 11-row Sep 26 - Oct 1 veto backlog, see RETRO-20261006-0211.)** Edges and P&L are `core/counterfactual.py ledger --rows` at the recorded book ($5 flat); the mechanical totals already counted these rows.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| "Heart of the Beast" OW bracket (`cec5bff18abf`, OVV) | 0.40 / 0.76 | No | +0.350 | No | +15.00 |
| "Forgotten Island" OW <13m (`bb60348ab311`, OVV) | 0.90 / 0.7525 | Yes | +0.145 | No | -5.00 |
| LGD -1.5 vs Xtreme (`c0ad4f0ec92d`, OVV) | 0.25 / 0.355 | No | +0.080 | No | +2.46 |
| 10y hits 5.25% Sep (`a41e6e996b85`, WSV) | 0.46 / 0.65 | No | -0.020 | Yes | -5.00 |
| Burleson MLB RBI lead (`18a43357718b`, WSV) | 0.93 / 0.73 | Yes | +0.040 | Yes | +0.62 |
| PinkPantheress Best Dance (`e4564b71ab49`, WSV) | 0.30 / 0.37 | No | -0.020 | No | +1.94 |
| MrBeast Gaming 26.75-27.5M (`ba4ad02817d3`, WSV) | 0.85 / 0.875 | No | -0.030 | Yes | -5.00 |
| AI 1530 Arena by Sep 30 (`a93c997dbdf5`, WSV) | 0.93 / 0.891 | Yes | -0.022 | Yes | non-trade (entry 0.952) |
| WTI > $90 Sep 30 (`853c6998ca45`, WSV) | 0.88 / 0.925 | No | -0.010 | Yes | -5.00 |
| ISM Mfg 55.0-55.9 Sep (`4b0493d215d6`, WSV) | 0.283 / 0.395 | No | +0.077 | No | +2.81 |
| Iran sanctions EO by Sep 30 (`e9bfda300d68`, WSV) | 0.04 / 0.215 | No | +0.040 | No | +0.43 |

OVV backfill net **+$12.46** (2W/1L); WSV backfill net **-$9.20** (4W/3L, 1 non-trade). Mechanical ledgers now: OVV 226 rows / 218 trades / 93W-125L / +$141.47 (unchanged, these rows were already counted); WSV 51 rows / 41 trades / 25W-16L / -$23.22, side split no 31/25/14W-11L/-$34.23, yes 20/16/11W-5L/+$11.01; check -34.23 + 11.01 = -23.22. Ruling: no boundary change. Five of the eight WSV rows had a non-positive realizable edge at the ask, so the spread veto mostly blocked trades min_edge would have blocked anyway.

**2026-10-07 04:1xZ update (FULL cycle, operator machine; 4 veto rows
settled this tick, plus 21 settled veto rows that no local retro tabled,
found by `strategy/tools/reconcile.py` once its funnel crash was fixed;
see RETRO-20261007-0410.)** Rows settled after the 0016Z update are new
to the mechanical totals; the five rows settled Sep 28-29 were already
inside them.

| Row | est vs mkt | Side | Realizable edge | Result | CF P&L |
|---|---|---|---|---|---|
| Hormuz 0 transits by Oct 31 first read (`d910eebe71cd`, OVV, superseded) | 0.38 / 0.21 | Yes | +0.150 | Yes | +16.74 |
| Lula 44-47% R1 (`a342eb964026`, OVV) | 0.79 / 0.885 | No | +0.080 | Yes | -5.00 |
| CAQ fewer than 1 seat (`607c62b57829`, OVV) | 0.40 / 0.11 | Yes | +0.260 | Yes | +30.71 |
| Grenada win Oct 5 (`321fa9da9ea9`, OVV) | 0.60 / 0.695 | No | +0.090 | No | +11.13 |
| Netflix #1 show 6-9M (`d464b1156ed9`, OVV) | 0.72 / 0.9365 | No | +0.190 | Yes | -5.00 |
| Trump NE rally "Data Center" (`30efc6ceefdd`, OVV) | 0.35 / 0.67 | No | +0.300 | No | +9.29 |
| Trump NE rally "Egg" first read (`5b84cae6b47f`, OVV) | 0.40 / 0.64 | No | +0.190 | Yes | -5.00 |
| Trump NE rally "Egg" re-check (`3b69bfef36a4`, OVV) | 0.74 / 0.605 | Yes | +0.120 | Yes | +3.06 |
| Heart of the Beast OW (`cec5bff18abf`, OVV, backfill Sep 28) | 0.40 / 0.76 | No | +0.350 | No | +15.00 |
| Forgotten Island OW (`bb60348ab311`, OVV, backfill Sep 28) | 0.90 / 0.7525 | Yes | +0.145 | No | -5.00 |
| LGD -1.5 vs Xtreme (`c0ad4f0ec92d`, OVV, backfill Sep 29) | 0.25 / 0.355 | No | +0.080 | Xtreme | +2.46 |
| Saint-François Tanguay (`a3314a17c247`, WSV) | 0.82 / 0.69 | Yes | +0.060 | Yes | +1.58 |
| Hochelaga-Maisonneuve Leduc (`2d634083dd78`, WSV) | 0.75 / 0.87 | No | +0.090 | Yes | -5.00 |
| Saint-Henri-Sainte-Anne Clermont (`0cdee07f6243`, WSV) | 0.56 / 0.70 | No | +0.100 | Yes | -5.00 |
| Bab el-Mandeb 190-209 (`d380a0c3a741`, WSV) | 0.36 / 0.37 | No | -0.060 | Yes | -5.00 |
| Trump NE rally "Tax" 25+ (`c3803f656959`, WSV) | 0.58 / 0.355 | Yes | +0.130 | Yes | +6.11 |
| Trump NE rally "Independent" (`4e4a0c06f526`, WSV) | 0.85 / 0.76 | Yes | +0.040 | Yes | +1.17 |
| 10y 5.25% Sep (`a41e6e996b85`, WSV, superseded, backfill Sep 29) | 0.46 / 0.65 | No | -0.020 | Yes | -5.00 |
| Burleson RBI lead (`18a43357718b`, WSV, backfill Sep 28) | 0.93 / 0.73 | Yes | +0.040 | Yes | +0.62 |
| Stateside award (`e4564b71ab49`, WSV, backfill Sep 28) | 0.30 / 0.37 | No | -0.020 | No | +1.94 |
| MrBeast Gaming 26.75-27M (`ba4ad02817d3`, WSV, backfill Oct 1) | 0.85 / 0.875 | No | -0.030 | Yes | -5.00 |
| AI Arena 1530 by Sep 30 (`a93c997dbdf5`, WSV, backfill Oct 1) | 0.93 / 0.891 | Yes | -0.022 | Yes | refused (entry 0.952) |
| WTI above $90 Sep 30 (`853c6998ca45`, WSV, backfill Oct 1) | 0.88 / 0.925 | No | -0.010 | Yes | -5.00 |
| ISM PMI 55.0-55.9 Sep (`4b0493d215d6`, WSV, backfill Oct 1) | 0.283 / 0.395 | No | +0.077 | No | +2.81 |
| Iran sanctions EO by Sep 30 (`e9bfda300d68`, WSV, backfill Oct 1) | 0.04 / 0.215 | No | +0.040 | No | +0.43 |

Outside-view-veto: these 11 rows net **+$68.39** (7W/4L); the 8 settled
after the 0016Z update add +$55.93. Mechanical ledger now 234 rows / 226
trades / 98W-128L / +$197.40 / dBrier +0.0261 / held-out +$204.35 (was
226/218/93W-125L/+$141.47). Side split: no 161/153/71W-82L/+$133.02; yes
73/73/27W-46L/+$64.38. Check: 133.02 + 64.38 = 197.40.
Wide-spread-veto: these 14 rows net **-$15.34** (7W/6L, 1 refused).
Mechanical ledger now 57 rows / 47 trades / 28W-19L / -$29.36 / dBrier
-0.0141 / held-out -$19.10. Side split: no 34/28/14W-14L/-$49.23; yes
23/19/14W-5L/+$19.87. Check: -49.23 + 19.87 = -29.36.
Ruling: no boundary change. The OVV line's CF P&L keeps rising on
longshot Yes wins (CAQ 0 seats +30.71, Hormuz +16.74), but its dBrier
stays positive (+0.0261): the vetoed beliefs are still worse-calibrated
than the book, so the operator's gnhf-run-4 verdict stands. The WSV line
is the opposite (beliefs better than the mid, CF P&L negative), and n=47
trades is still too thin to move the spread boundary.
