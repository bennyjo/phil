# Playbook archive

Settled narrative moved out of `strategy/playbook.md` so the live file stays
readable. Nothing here is a live rule; any rule a moved section carried was
restated in the live file when it moved. Not read per cycle.

## Moved DEEP-2026-09-30: per-settlement counterfactual updates, Sep 26-29

## 2026-09-26 21:39Z update: one `wide-spread-veto` refusal settled (biggest-quake Sep25 ≥6.1)

`f7fcd3a05a31`, recorded 2026-09-26T04:16:55Z, own est 0.97 vs a bid-only
mid of 0.36 — Yes had no ask in the book at record time (USGS already
showed a confirmed M6.6, next-largest 5.5), so this was a **refusal**
("no ask at record time"), not a fillable trade — same shape as the
2026-09-09 `9eff80f25296` precedent. Settled WON. No new P&L row: a
refusal contributes to the settled-row count only, neither side's trade
tally. Current mechanical ledger (`core/counterfactual.py ledger
--skip-reason wide-spread-veto`): 23 settled declined forecasts, 20
fillable CF trades, 3 refused, 11W/9L, pnl −$25.04 (staked $100.00),
brier_delta −0.0444, held-out −$17.22. Side split unchanged by this row:
no 13 rows/11 trd/5W-6L/−$19.79; yes 10 rows/9 trd/6W-3L/−$5.25. Check:
−19.79−5.25=−25.04 ✓. Ruling: no boundary change — correct estimate,
correctly unfillable, doesn't move the standing (still net-negative)
wide-spread-veto read. Full grading in RETRO-20260926-2143.

## 2026-09-28 02:15Z update: one `wide-spread-veto` row settled (Burleson MLB RBI lead)

| Burleson RBI lead (`18a43357718b`, wide-spread-veto) | 0.93 / 0.73 | Yes | +0.040 | Yes | **+0.62** |

Fillable at the 0.89 ask (book 0.53/0.89, spread 0.36). Mechanical ledger
(`core/counterfactual.py ledger --skip-reason wide-spread-veto`): 24 settled
rows, 21 fillable CF trades, 3 refused, 12W/9L, pnl −$24.42 (was −$25.04;
−25.04+0.62=−24.42 ✓), dBrier −0.0454. Side split: no 13 rows/11 trd/5W-6L/
−$19.79 (unchanged); yes 11 rows/10 trd/7W-3L/−$4.63 (−5.25+0.62 ✓). Check:
−19.79−4.63=−24.42 ✓. Ruling: no boundary change. The realizable ask-edge
sat at the min_edge floor, so the 0.20 mid gap was stale-mid, not tradable.
Full grading in RETRO-20260928-0215.

## 2026-09-28 04:15Z update: one `wide-spread-veto` row settled (VMA Best Dance Stateside)

| VMA Best Dance Stateside (`e4564b71ab49`, wide-spread-veto) | 0.30 / 0.37 | No | −0.020 | No | **+1.94** |

Fillable at the 0.72 No ask (book 0.28/0.46). Mechanical ledger
(`core/counterfactual.py ledger --skip-reason wide-spread-veto`): 25 settled
rows, 22 fillable CF trades, 3 refused, 13W/9L, pnl −$22.48 (was −$24.42;
−24.42+1.94=−22.48 ✓), dBrier −0.0455. Side split: no 14 rows/12 trd/6W-6L/
−$17.84 (−19.79+1.94, rounding); yes 11 rows/10 trd/7W-3L/−$4.63 (unchanged).
Check: −17.84−4.63=−22.47 ≈ −22.48 (rounding) ✓. Ruling: no boundary change —
realizable edge was negative, a lucky CF win on a correctly declined trade.
Full grading in RETRO-20260928-0415.

## 2026-09-28 22:15Z update: 4 `outside-view-veto` + 2 `wide-spread-veto` rows settled (Treasury Sep ladder, box office Sep 26 weekend)

| 10y hit 5.20% Sep (`fdedb184ad3e`, OVV) | 0.28 / 0.06 (No frame) | No | +0.190 | Yes | −5.00 |
| 10y hit 5.20% Sep (`3ed526b57eca`, OVV) | 0.47 / 0.26 (No frame) | No | +0.200 | Yes | −5.00 |
| Heart of the Beast 17-20m (`cec5bff18abf`, OVV) | 0.40 / 0.76 | No | +0.350 | No | **+15.00** |
| Forgotten Island <13m (`bb60348ab311`, OVV) | 0.90 / 0.7525 | Yes | +0.145 | No | −5.00 |
| 30y hit 5.50% Sep (`99df204b7f85`, WSV) | 0.67 / 0.54 | Yes | +0.055 | Yes | **+3.13** |
| 30y hit 5.55% Sep (`84012264b65d`, WSV) | 0.31 / 0.51 | No | −0.107 | Yes | −5.00 |

Mechanical ledgers (`core/counterfactual.py ledger --skip-reason ...`):
outside-view-veto batch $0.00 (1W/3L): 179 rows, 171 trd, 72W/99L,
+$77.41 (unchanged). Side: no 126/118/54W-64L/+$43.21 (+5.00); yes
53/53/18W-35L/+$34.20 (−5.00). Check 43.21+34.20=77.41 ✓.
wide-spread-veto batch −$1.87 (1W/1L): 27 rows, 24 trd, 3 refused,
14W/10L, −$24.35 (−22.48−1.87 ✓), dBrier −0.0372. Side: no 15/13/6W-7L/
−$22.84; yes 12/11/8W-3L/−$1.50. Check −22.84−1.50=−24.34 ≈ −24.35
(rounding) ✓. Ruling: no boundary change; the rates misses were the
driftless est (new Treasury touch drift rule), not the veto. Full
grading in RETRO-20260928-2215.

## 2026-09-29 18:00Z update: JOLTS Aug ladder + one `outside-view-veto` row settled

| LGD -1.5 vs Xtreme (`c0ad4f0ec92d`, OVV) | 0.25 / 0.355 | No | +0.105 | No | **+2.46** |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
outside-view-veto`): 180 rows, 172 trd, 8 refused, 73W/99L, +$79.87 (was
+$77.41; 77.41+2.46=79.87 ✓), dBrier +0.0322. Side: no 127/119/55W-64L/
+$45.67 (43.21+2.46 ✓); yes 53/53/18W-35L/+$34.20 (unchanged). Check
45.67+34.20=79.87 ✓. Ruling: no boundary change. It is one draw on a
self-built Bo3 model. Full grading in RETRO-20260929-1800.

- **JOLTS: record the LinkUp model centre and do not tilt past consensus
  on soft signals (n=1, RETRO-20260929-1800).** Aug print 7,079k vs
  consensus 7.23M, LinkUp 7.185M. I tilted the centre UP to 7.25M on an
  Indeed/NFP read. The five ladder rows netted dBrier +0.0011 (a wash).
  The same shape showed up in the Canada GDP retro: a directional tilt
  on top of a sourced benchmark is unvalidated. Cap it at 0.05 of bracket
  mass there, and at zero past consensus for JOLTS until it has graded
  evidence.
- **Econ ladders: record every bracket whose book was read, centre
  included.** The Aug JOLTS ladder recorded the tails and the upper
  brackets, but not 7.0-7.1 or 7.1-7.2, and the print landed in 7.0-7.1.
  A ladder with no row near the outcome can't be graded as a
  distribution. This is the validated-feed sweep rule ("forecasts for
  every leg read") applied to BLS/BEA/StatCan ladders.

## 2026-09-29 22:15Z update: one `wide-spread-veto` row settled (10y hit 5.25% Sep)

| 10y hit 5.25% Sep (`a41e6e996b85`, WSV, superseded by `5e46d21ef6ca`) | 0.46 / 0.65 | No | fillable per ledger | Yes | −5.00 |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
wide-spread-veto`): 28 rows, 25 trd, 3 refused, 14W/11L, −$29.35 (was
−$24.35; −24.35−5.00=−29.35 ✓), dBrier −0.0299. Side: no 16/14/6W-8L/
−$27.84 (was 15/13/6W-7L/−$22.84; −22.84−5.00 ✓); yes 12/11/8W-3L/−$1.50
(unchanged). Check −27.84−1.50=−29.34 ≈ −29.35 (rounding) ✓. Ruling: no
boundary change. The loss comes from the pre-drift-rule driftless blend (Sep 25),
not from the veto. The superseding drift-plus-futures row (0.76 vs 0.74)
beat the mid by 0.010. It is still the single September up-trend regime, so
the October split-by-trend re-grade stands. Full grading in
RETRO-20260929-2215.

## 2026-09-29 23:42Z update: one `outside-view-veto` row settled (Trump renames AI, 3-snapshot chain) — unexplained-move tracking, n=2

| Trump renames AI (`e22fb0445ebe`, OVV, supersedes `f85a9b197bc6`) | 0.30 / 0.535 | No | +0.23 | Yes | **-5.00** |

Mechanical ledger (`core/counterfactual.py ledger --skip-reason
outside-view-veto`): 181 rows, 173 trd, 8 refused, 73W/100L, +$74.87 (was
+$79.87; 79.87-5.00=74.87 ✓), dBrier +0.0336 (was +0.0322). Side: no
128/120trd/55W-65L/+$40.67 (was 127/119/55W-64L/+$45.67; 45.67-5.00=40.67
✓); yes 53/53/18W-35L/+$34.20 (unchanged). Check 40.67+34.20=74.87 ✓.
Ruling: no boundary change — the declined No bet would have lost, so the
veto did its job on the trade decision.

**Unexplained-move tracking (paired with the 2026-09-21 Opus case,
RETRO-20260922-0619): 1-for-2 so far, not a rule either way.** This
market's book moved 0.255->0.535 between Sep27 and Sep29 with, per the
row's note, "no source I can find." Per the Sep21 lesson ("a price move
with no sourced cause is not itself evidence") the estimate was NOT
revised toward the market (held at 0.30 vs market 0.535) and the bet was
vetoed. This time the market was right — event resolved Yes, own's
whitehouse.gov/presidential-actions search method never surfaced whatever
the book saw. Sep21's case had the opposite result: an unsourced jump
that reversed, where discounting it was correct. Two data points, one
each way, on the specific question "should an unexplained price move
against a public-record-search estimate shift the estimate itself
(separately from whether it should ever be traded)." Full grading in
RETRO-20260929-2342. Stays a tracked observation, not a playbook rule —
n=2 is far below the ~15-settlement floor CYCLE.md sets for acting on a
read, and the two cases are in different categories (ai-model-release vs
news). Re-visit if a third instance settles either way.
