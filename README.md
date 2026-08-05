# self-improving-trader

[![CI](https://github.com/bennyjo/self-improving-trader/actions/workflows/ci.yml/badge.svg)](https://github.com/bennyjo/self-improving-trader/actions/workflows/ci.yml)

**An AI agent that trades short-term prediction markets and rewrites its own
strategy after every resolved bet.** Paper trading is the 24/7 learning
engine; real money runs alongside it, deliberately small — $1 stakes through
[Pearl Connect](https://github.com/valory-xyz/connect), only in edge classes
whose settled evidence has earned it.

The agent goes by **Phil** — after the man who relived the same day until
he'd learned enough to win it, and the groundhog who makes forecasts.


## The experiment

Claude Code gets a simulated $1,000 bankroll and the short-term Polymarket
universe (earnings beats, daily sports, pre-match esports, near-term news —
sub-daily crypto coin-flips are banned). Every cycle it settles yesterday's
bets against official resolutions, scores its own calibration against the
market price it paid, writes a retrospective when bets have settled, **edits
its own playbook, risk policy, tooling, sensing** (the market-discovery
queries) **and pacing** (which hourly ticks deserve a full cycle), commits
the diff, then researches and bets again.

Three layers keep it honest:

- an **hourly cycle agent** that researches, bets, and self-edits;
- a **daily deep-retro agent** that audits every strategy edit — keeping,
  sharpening, or reverting each — grades the day's biggest estimation
  errors, and adjudicates the cycle agent's proposals;
- the **human operator**, who owns the protected engine (`core/`, the caps,
  the cycle procedure) and talks to the agents through
  `journal/operator-notes.md` (evidence in) and `journal/proposals.md`
  (asks out — changes only the operator can make).

The strategy's git log is the product: every commit is a lesson the agent paid
for (in paper) — and the honest metric is `brier_delta` (is the agent's
probability a better forecast than the market's own price?), not just P&L.

## Two loops: paper learns 24/7, real money follows the evidence

The learning engine is paper: an always-on cloud loop cycles hourly across
the whole market universe, because hundreds of simulated feedback loops cost
nothing and answer the question that matters: *in which market categories
does fast AI research actually beat the price?*

Real execution rides on top, deliberately small: when the operator's machine
is on and Pearl Connect's local signer is healthy (`./loop.sh --real`),
paper bets in edge classes with positive settled evidence get a **$1 real
twin** on Polymarket (Polygon) — placed through `core/real.py`, the only
code that touches funds, against hard caps in `config/protected.json`
(per-bet, per-day, open-position). The Safe holds ~$25; the agent never
holds keys; every signature goes through Pearl Connect's audited local
choke point. Real fills feed back into the journal so retros can measure
what paper can't: actual fill quality versus the simulated
cross-the-spread model.

[Pearl Connect](https://github.com/valory-xyz/connect) is Pearl's BYOA
signing service: it lets any agent harness — Claude Code included — act as an
Olas Pearl agent without ever holding keys. To run it yourself, download
Pearl at [pearl.you/connect](https://www.pearl.you/connect).

## Honest-simulation rules

- Paper fills cross the live CLOB spread (buy at best ask), like a real taker.
- Entry prices are recorded at bet time; resolutions are Polymarket's own.
- The agent cannot edit the engine (`core/`, `config/protected.json`);
  `loop.sh` reverts any attempt, and CI independently fails any agent
  commit that touches protected files. Caps: $10/bet max, 60 open positions,
  no market resolving <20 min out, no entries outside 2¢–95¢.

## Run

```bash
./loop.sh 10 45          # 10 paper cycles, 45 min apart (headless Claude Code)
./loop.sh 1 45 --real    # one cycle with $1 real twins via Pearl Connect
python3 core/score.py    # calibration & P&L report any time
python3 core/real.py doctor   # is the real-execution path ready?
```

Requires [Claude Code](https://claude.com/claude-code) (`claude` on your
PATH) and Python 3. No API keys needed — market data comes from Polymarket's
public gamma/CLOB endpoints.

## Disclaimer

This is a research experiment in agent self-improvement. Most trading is
simulated; a small real-money leg (capped at $1 per bet from a wallet
holding ~$25) runs through Pearl Connect only when the operator deliberately
enables it. Nothing here is financial, investment, or betting advice, and
past performance — paper or real — predicts nothing. Prediction-market
trading is restricted or unlawful in some jurisdictions — know your own
rules before running any of this with real funds.

## License

[Apache-2.0](LICENSE). The journal and strategy files are part of the
experiment's record and are covered by the same license.
