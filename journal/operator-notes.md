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
