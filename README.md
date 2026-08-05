# Phil the self-improving trader

[![CI](https://github.com/bennyjo/phil/actions/workflows/ci.yml/badge.svg)](https://github.com/bennyjo/phil/actions/workflows/ci.yml)

<img src=".github/phil.png" alt="Phil, a groundhog peeking over a rising price chart" width="100" align="left"/>

**Phil is a self-improving trader: an AI agent that trades short-term
prediction markets and rewrites its own strategy after every resolved
bet.** Paper trading is the 24/7 learning engine. Real money runs alongside
it, deliberately small: capped stakes through
[Pearl Connect](https://github.com/valory-xyz/connect), only in edge classes
whose settled evidence has earned it.

The name honors the man who relived the same day until he'd learned enough
to win it, and the groundhog who makes forecasts.


## The experiment

Claude Code gets a simulated $1,000 bankroll and the short-term Polymarket
universe: earnings beats, daily sports, pre-match esports, near-term news.
Sub-daily crypto coin-flips are banned. Every cycle it settles yesterday's
bets against official resolutions and scores its own calibration against the
market price it paid. It writes a retrospective when bets have settled. It
**edits its own playbook, risk policy, tooling, sensing** (the
market-discovery queries) **and pacing** (which hourly ticks deserve a full
cycle). Then it commits the diff, researches, and bets again.

Three layers keep it honest:

- an **hourly cycle agent** that researches, bets, and self-edits;
- a **daily deep-retro agent** that audits every strategy edit (keep,
  sharpen, or revert), grades the day's biggest estimation errors, and
  adjudicates the cycle agent's proposals;
- the **human operator**, who owns the protected engine (`core/`, the caps,
  the cycle procedure). Evidence flows in through
  `journal/operator-notes.md`. Asks flow out through `journal/proposals.md`
  for changes only the operator can make.

The strategy's git log is the product: every commit is a lesson the agent
paid for (in paper). The honest metric is `brier_delta`, not just P&L: is
the agent's probability a better forecast than the market's own price?

## Two loops: paper learns 24/7, real money follows the evidence

The learning engine is paper. An always-on cloud loop cycles hourly across
the whole market universe, because hundreds of simulated feedback loops cost
nothing and answer the question that matters: *in which market categories
does fast AI research actually beat the price?*

Real execution rides on top, deliberately small. When the operator's machine
is on and Pearl Connect's local signer is healthy (`./loop.sh --real`),
paper bets in edge classes with positive settled evidence get a **real
twin** on Polymarket (Polygon). Orders go through `core/real.py`, the only
code that touches funds, and the sizing is all config: per-bet, per-day and
open-position caps live in `config/protected.json` (currently $1 per bet),
with hard ceilings that CI enforces. The Safe holds only what the operator
chooses to fund; its balance is the final cap no code can exceed. The agent
never holds keys; every signature goes through Pearl Connect's audited
local choke point. Real fills feed back into the journal so retros can
measure what paper can't: actual fill quality versus the simulated
cross-the-spread model.

[Pearl Connect](https://github.com/valory-xyz/connect) is Pearl's BYOA
signing service. It lets any agent harness, Claude Code included, act as an
Olas Pearl agent without ever holding keys. To run it yourself, download
Pearl at [pearl.you/connect](https://www.pearl.you/connect).

## Honest-simulation rules

- Paper fills cross the live CLOB spread (buy at best ask), like a real taker.
- Entry prices are recorded at bet time; resolutions are Polymarket's own.
- The agent cannot edit the engine (`core/`, `config/protected.json`).
  `loop.sh` reverts any attempt, and CI independently fails any agent
  commit that touches protected files. Caps: $10/bet max, 60 open positions,
  no market resolving under 20 minutes out, no entries outside 2¢ to 95¢.

## Run

```bash
./loop.sh 10 45          # 10 paper cycles, 45 min apart (headless Claude Code)
./loop.sh 1 45 --real    # one cycle with real twins via Pearl Connect
python3 core/score.py    # calibration & P&L report any time
python3 core/real.py doctor   # is the real-execution path ready?
```

Requires [Claude Code](https://claude.com/claude-code) (`claude` on your
PATH) and Python 3. No API keys needed: market data comes from Polymarket's
public gamma/CLOB endpoints.

## Disclaimer

This is a research experiment in agent self-improvement. Most trading is
simulated. A small real-money leg runs through Pearl Connect only when the
operator deliberately enables it: per-bet and daily stakes are capped in
`config/protected.json`, and the wallet holds only what the operator funds.
Nothing here is financial, investment, or betting advice. Past performance,
paper or real, predicts nothing. Prediction-market trading is restricted or
unlawful in some jurisdictions. Know your own rules before running any of
this with real funds.

## License

[Apache-2.0](LICENSE). The journal and strategy files are part of the
experiment's record and are covered by the same license.
