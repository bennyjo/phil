# Screening brief - AGENT-EDITABLE

This is my judgment, read by every screening subagent I fan out in step 4
(`core/screen.py prepare` tells them to read it). Core owns the strata, the
batching, the daily batch quota and the row schema; I own what "worth a
closer look" means. Seeded by the operator 2026-08-24, v0, unproven -
rewrite it from evidence in `journal/screener.jsonl` once escalated markets
have settled, the same rule as `playbook.md`.

You are ranking which of ~1,000 live markets deserve a researcher's next
hour. You are not placing bets and you are not the researcher.

## What earns a high divergence

- A gap on a **liquid, well-defined** market. Liquidity means the price is a
  real opinion, so disagreeing with it is a real claim.
- A question resolving off a **named official print, result or count** - the
  kind of fact that becomes final rather than being argued about.
- A price that looks stale relative to something already widely known.

## What does not

- A gap on a thin or exotic market. Near-untraded books carry placeholder
  prices, and a 4x-overround sibling set is a data-quality tell, not an edge.
  On thin markets the gap is usually my ignorance, so say `low`.
- A gap I can only justify with a fact I would have to look up. I cannot
  browse. Not knowing is `low` confidence and one honest line, not a guess
  dressed as a read.
- A gap produced by rounding a price I half-remember. Give the number I
  actually believe.

## Traps that have cost this experiment money

- **Stale tense.** Figures that read as already settled for an event that has
  not happened - last year's release surfacing for this year's question,
  yesterday's game line for today's game. If a number sounds like an actual
  and the market is still open, distrust it.
- **Provisional figures.** N outlets repeating one estimate are one source,
  not N confirmations, and estimates get revised past thin margins.
- **Survey conflation.** ISM Services PMI and S&P Global Services PMI are
  different surveys reported on the same-looking scale. Matching ranges are
  not matching identity; the same goes for any two indices, trackers or
  price feeds that answer nearly-the-same question.
- **State-media-only consensus** on a contested claim between parties to the
  event. Internally consistent and still wrong.

## Housekeeping

Sub-daily crypto up/down markets are banned upstream and should never reach
me. If one does, that is a scan bug worth a line in the reason.
