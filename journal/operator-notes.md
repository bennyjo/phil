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
