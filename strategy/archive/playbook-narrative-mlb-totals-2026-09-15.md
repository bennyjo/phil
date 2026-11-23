# Archived from strategy/playbook.md by DEEP-2026-11-23 (compaction tranche 1; no behaviour change)

Live gates restated in playbook.md under "Live rules (compacted)". MLB is out of season until ~2027-03.

## New hypothesis: Normal-fit cross-line extrapolation for MLB totals (2026-09-15 02:4xZ)

TRIGGERED cycle on two new PM markets, SD@COL (Coors Field) O/U 12.5
(4573201) and O/U 10.5 (4573200), both created ~10min before the watch
trigger, ~22h before first pitch. `core/odds.py odds baseball_mlb --markets
totals` returned 6 sportsbook lines clustered at 14.5/15.0/15.5 — a full run
higher than either PM line, and itself spread across a full run
(14.5-15.5), consistent with early/soft pricing before starters are
confirmed. Power-devigged each book (`strategy/tools/devig.py`), averaged
by line (14.5: 0.518, 15.0: 0.488, 15.5: 0.428), fit a Normal(mu,sigma) to
the 14.5/15.5 points (mu=14.70, sigma=4.39 — checked against the 15.0 point:
predicted 0.473 vs observed 0.488, close enough to trust the shape), then
extrapolated down to PM's lines: 12.5 → model P(Over)=0.692 vs ask 0.43
(claimed edge 0.26); 10.5 → model P(Over)=0.831 vs ask 0.59 (claimed edge
0.24).

This is a first-contact method for MLB (no prior cross-line total
extrapolation attempted in this book — the closest precedent is the soccer
Poisson-derivative section above, which fits a scoreline model to devigged
h2h rather than fitting a distribution directly to devigged totals at
multiple lines). Both claimed edges are far past the 0.10 outside-view-veto
boundary with no fact-final or mechanical-benchmark anchor (a self-built
Normal fit is exactly the self-model class the veto exists to catch, not a
carve-out candidate), and the 2-3 run gap being extrapolated (down from a
14.5-15.5 cluster to 10.5/12.5) is a wide reach for an assumed-Gaussian
shape when the true total-runs distribution is right-skewed and discrete.
Declining to bet either leg — recorded as `unvalidated-method` forecasts
only (5b6a0e52dd62 for 12.5-Over, 793b7298aec9 for 10.5-Over), per the same
maiden-voyage discipline as the soccer hypothesis (forecast-only until an
independent-instance bar is met). Both settle within ~22h;
**grade at settlement** and decide whether a second instance is worth
seeking out, or whether one high-divergence pre-lineup game is enough
evidence that early lines are too soft to extrapolate confidently.

**Bar pre-registered by DEEP-2026-09-15** (mirroring the soccer
Poisson-derivative bar and its 2026-09-05 leg-counting correction,
which this hypothesis cited but left unset): forecast-only until
**n>=6 independent GAMES** settle with recorded cross-line forecasts;
multiple lines on the same game (here 12.5 and 10.5 on SD@COL) count
as ONE game, graded by average leg dBrier — one fitted Normal and one
realized run total make every line of the same game agree in
direction, exactly the correlated-legs artifact the soccer correction
documented. Tally direction-of-miss per game (model-high/model-low/hit)
to catch the known skew risk: the true total-runs distribution is
right-skewed and discrete, so a symmetric Normal fitted at 14.5-15.5
and read at 10.5-12.5 likely OVERSTATES P(Over) at lines far below the
mean — if the tally shows persistent model-high misses on the low
side, that is the fitted-shape bias showing, not noise. Also record
the book-line context per instance (cluster width, hours to first
pitch, starters confirmed or not): the alternative reading of any
early win is "early book lines are soft," which is a timing edge, not
a distribution-fit edge, and only the context column can separate
them.

**GRADED 2026-09-16 04:1xZ (RETRO-20260916-0411): game 1/6, bar still NOT
met.** SD@COL settled: total runs landed at 11 or 12 (12.5-Over lost,
10.5-Over won). Model-high miss confirmed on the 12.5 leg exactly where
the pre-registered right-skew concern predicted it (est 0.69, market mid
0.42, actual Under: model brier 0.4761 vs market brier 0.1764, dBrier
model-mkt +0.2997 — market clearly better). The 10.5 leg hit (est 0.83,
market mid 0.58, actual Over: model brier 0.0289 vs market brier 0.1764,
dBrier model-mkt −0.1475 — model better, but 10.5 was already a soft bar
given the actual total, so a hit there isn't strong confirmation of the
fitted shape). Average leg dBrier (model−mkt) for this game: **+0.0761**
(model underperformed the market on net). Direction-of-miss tally:
model-high ×1 (12.5 leg — real total came in ~2.7-3.7 runs below the
fitted mean of 14.70, squarely the "symmetric Normal overstates P(Over)
read far below the mean" failure mode the bar was written to catch),
hit ×1 (10.5 leg, weak evidence per above). Book-line context: 6-book
cluster at 14.5-15.5 (~1-run spread), ~22h pre-game, starters likely
unconfirmed at forecast time — consistent with "early lines still
soft/wide" rather than a confirmed distribution-fit edge either way.
No bets were placed (unvalidated-method correctly kept this
forecast-only — $0 P&L impact from a leg that would have lost real
stake). Still forecast-only; **5 more independent games** needed before
the n>=6 bar is reached. No playbook policy change yet — one game is not
a sample, but the single data point points toward the right-skew
overstatement risk being real rather than illustrative.

**Second candidate instance, imported-sigma sub-variant, NOT yet tallied
(2026-09-30 01:xxZ TRIGGERED cycle):** AL Wild Card Game 2, CWS@HOU, two
new PM markets (5144942 O/U8.5, 5144941 O/U6.5) fired the watcher on
creation, starters TBD. Unlike SD@COL, `core/odds.py` returned NO cross-
book dispersion here — all 8 books quote the identical 7.5 line, power-devig
consensus P(Over 7.5)=0.504 (spreads <=0.08, essentially fair). With no
fresh line spread to fit mu/sigma from, sigma=4.39 was imported unchanged
from the SD@COL fit rather than refit — a weaker instance methodologically
(external parameter vs in-game data), so it is recorded as forecast-only
(`090e99f18536` Over8.5 est 0.41, `8f80c89cb1a0` Over6.5 est 0.59 — both
skip-reason `no-edge`, both edges <=0.04 anyway so the floor alone would
have blocked a bet regardless of method status) but flagged separately
rather than folded into the SD@COL n>=6 count. Grade at settlement
(~2026-09-30 21:00Z) same as SD@COL (direction-of-miss, book-line
context), and decide then whether tight-single-line + imported-sigma
belongs in the same tally as multi-line + fitted-sigma, or needs its own
bar.

**TALLY 2026-10-01 04:1xZ (RETRO-20261001-0415): fitted-sigma games 2/6,
bar NOT met.** Game 2 BOS@NYY (2-pt fit on 6.5/7.0 books, mu 6.72 sigma
3.67, PM lines 5.5/7.5 within 1 run of the fit): avg leg dBrier +0.0071,
~hit (model within a tick of the mid, Over landed). Imported-sigma side
tally kept separate: CWS@HOU (RETRO-20261001-0015) +0.0196 avg, model-low.
Running read: near-line reads reproduce PM (no claimable edge), far-line
reads (SD@COL) lose to PM. Still forecast-only; nothing yet argues for an
edge class here.

**Fourth candidate instance overall, fitted-sigma genre, NOT yet tallied
(2026-10-13 03:5xZ TRIGGERED cycle):** CLE@TB (Oct 14), three new PM markets fired the
watcher on creation: O/U7.5 (5640089), O/U5.5 (5640088), and a
underdog-framed Spread: Guardians(-1.5) (5640086, see below — separate
method). Totals books split across two lines this time (6.5: 4 books,
7.0: 5 books) — real cross-book dispersion to fit from, like SD@COL/BOS@NYY
rather than imported-sigma. Power-devig consensus P(Over6.5)=0.5165,
P(Over7.0)=0.4840; fit gives sigma=6.14, mu=6.75 (wider sigma than the
SD@COL fit's 4.39 — only a 0.5-run gap between anchor lines here, vs
SD@COL's 1-run gap, so the fit is noisier). Read at PM's lines:
P(Over7.5)=0.4516 vs ask 0.43/bid 0.41 (edge 0.02 at ask); P(Over5.5)=0.5809
vs ask 0.64/bid 0.63, i.e. Under 0.419 vs ask 0.37 (edge 0.049 at ask).
Both forecast-only (f4b1ecd5d257, 0096c34309c9), fitted-sigma bar still at
2/6 after the BOS@NYY grading, so this is the 3rd fitted-sigma candidate,
not yet settled. Grade at settlement (~2026-10-14 03:00Z-ish, first pitch
2026-10-14T00:00Z + game length).

**GRADED late (2026-10-19 21:xxZ cycle, picked up while researching the
Oct19 CLE@TB rematch below — this grading was missed at the time):**
actual total landed at or under 5 (both the 7.5-Over and 5.5-Over legs
settled Under). 7.5 leg: model 0.4516 vs mkt-mid 0.42, dBrier (model−mkt)
+0.0275 (model slightly worse). 5.5 leg: model 0.5809 vs mkt-mid 0.635,
dBrier −0.0658 (model notably better — the market was more confidently
wrong than the model on this leg). Average leg dBrier for the game:
**−0.0192 (favorable, model beat market net)**. Direction-of-miss:
model-high on both legs (fitted mu=6.75, actual total materially below
it) — same direction as the SD@COL model-high miss, reinforcing the
pre-registered right-skew-overstatement concern even on a game where the
average dBrier came out favorable (the model was less wrong than the
market, not right). **Fitted-sigma tally now 3/6 games**: SD@COL
unfavorable (+0.0761, model-high), BOS@NYY ~neutral (+0.0071, hit),
CLE@TB-Oct13 favorable (−0.0192, model-high). Bar still not met; 3 more
independent games needed.

**Dog -1.5 decay-ratio cross-market extrapolation, second use (same
cycle):** the Guardians(-1.5) spread market is the underdog's alt line —
structurally benchmark-unreachable by direct devig (2026-08-06 finding
above: books only quote the favorite's -1.5/dog's +1.5). Applied the same
ad-hoc decay-ratio extrapolation as the LAD-MIL forecast
(`ee9b886749ca`, settled lost, RETRO-20261013-0015): devig the favorite's
ML and spread-cover probabilities, take r = P(fav covers)/P(fav ML win),
apply r to the dog's ML win prob to estimate the dog's cover prob. Here:
Guardians ML 0.450, Rays ML 0.550, Rays covers-1.5 0.351, r=0.638 →
Guardians covers-1.5 ≈ 0.287 vs PM ask 0.32 (model edge negative, -0.033 —
favors the already-tiny Rays-side edge of +0.013 instead). Recorded
unvalidated-method (`855d4035dd0b`), no bet. Two uses now (one settled
lost, one pending); not enough to rule on the method, but worth a formal
bar before a third use claims a real edge: **pre-registering** forecast-
only until n>=5 independent games settle with this exact r-transfer
method, graded same as the totals Normal-fit (direction-of-miss tally,
since r borrowed from the favorite's distribution could systematically
mis-scale the dog's).

**GRADED late (2026-10-19 21:xxZ, picked up alongside the fitted-sigma
grading above — also missed at the time):** Guardians did not cover -1.5
(Rays won the spread market too). Model 0.287 vs mkt-mid 0.31, both vs
actual 0: model brier 0.0824, market brier 0.0961, dBrier −0.0137
(slightly favorable — model closer to the outcome, consistent with the
model also leaning Rays-side here even though its claimed edge was
tiny/negative). Re-checking the first instance (LAD-MIL, `ee9b886749ca`)
while grading this one: est 0.29 vs mkt-mid 0.29 — those were identical,
so its dBrier is exactly 0 (a wash, not favorable; it was recorded
`market-agrees`, not a real divergence test of the method at all).
**r-transfer tally now 2/2 settled: LAD-MIL neutral (dBrier 0, no real
divergence to grade), CLE-TB-Oct13 slightly favorable (−0.0137).** No
evidence against the method yet, but n=2 and only one of those two
actually tested it — nowhere near the n>=5 bar. Still forecast-only.

**Third candidate instance, imported-sigma, NOT yet tallied (2026-10-13
01:5xZ TRIGGERED cycle):** MIL@LAD (Oct 14), two new PM markets
(5639253 O/U8.5, 5639252 O/U6.5) fired the watcher on creation, same
8.5/6.5 shape as CWS@HOU. 9 books all quote the identical 7.5 line
(no cross-book dispersion to fit sigma from), power-devig consensus
P(Over7.5)=0.493 (essentially fair) — sigma=4.39 imported unchanged from
the SD@COL fit again. mu solved at 7.42; model P(Over6.5)=0.583 vs ask
0.61/bid 0.60 (best-side edge Under +0.027), P(Over8.5)=0.403 vs ask
0.41/bid 0.40 (edge ~0.007 either side). Both near min_edge-floor-irrelevant
territory — same "near-line reproduces PM" shape as BOS@NYY and CWS@HOU,
no bet either way regardless of the method's forecast-only status.
Recorded forecast-only, skip-reason no-edge (aa4bc68026cf Over6.5 est
0.583, c064c5c2a9a2 Over8.5 est 0.403). Grade at settlement (~2026-10-15
00:00Z first pitch Oct14 8PM ET + game length) same as prior instances;
if this also lands near-line/no-edge it strengthens the "imported-sigma
near-line case never clears min_edge" read without needing the n>=6
fitted-sigma bar to resolve it.
Graded RETRO-20261015-0415: run total 7-8 vs mu 7.42 (hit), leg dBrier
+0.022/-0.006 (avg +0.008, at market); near-line/no-edge again, as predicted.

**Fifth candidate instance, fitted-sigma genre, first INTERPOLATION case
(2026-10-19 21:4xZ TRIGGERED cycle):** CLE@TB again (Oct 19, a rematch of
the Oct13-14 game above — same two teams, new game, new market id
5940380), single new PM market O/U7.5 fired the watcher on creation,
~2.5h before first pitch (2026-10-20T00:08Z). Books split 6.5 (4 books:
fanduel/bovada/betonlineag/lowvig) and 7.0 (5 books:
betrivers/mybookieag/betmgm/draftkings/betus) — power-devig averages
P(Over6.5)=0.5386, P(Over7.0)=0.4793. Fit Normal(mu=6.83, sigma=3.36) to
those two points. Unlike every prior fitted/imported-sigma instance, PM's
line (7.5) sits **between** the two anchor lines rather than outside
them — this is interpolation, not extrapolation, so the right-skew
overstatement risk the bar was written to catch (which bites hardest
reading far below the fitted mean) should be smaller here. Model
P(Over7.5)=0.4205 vs PM ask 0.41/bid 0.39 (mid 0.40) — edge ~0.01-0.02 at
ask, below min_edge 0.04 regardless of the method's validation status.
Recorded forecast-only, skip-reason no-edge (`9c0ded05716b`). Grade at
settlement (~2026-10-20 03:00Z-ish, first pitch + game length); this adds
a 4th fitted-sigma candidate to the tally (3/6 graded, this one pending)
and is the first instance that can test whether interpolation reads are
better-behaved than the extrapolation reads that have driven the
model-high bias so far.

