# self-improving-trader

[![CI](https://github.com/bennyjo/self-improving-trader/actions/workflows/ci.yml/badge.svg)](https://github.com/bennyjo/self-improving-trader/actions/workflows/ci.yml)

**An AI agent that trades short-term prediction markets and rewrites its own
strategy after every resolved bet.** Paper-trading first; real funds via
[Pearl Connect](https://olas.network/) only if the simulation earns it.


## The experiment

Claude Code gets a simulated $1,000 bankroll and the short-term Polymarket
universe (earnings beats, daily sports, pre-match esports, near-term news —
sub-daily crypto coin-flips are banned). Every cycle it settles yesterday's
bets against official resolutions, scores its own calibration against the
market price it paid, writes a retrospective, **edits its own playbook, risk
policy, and tooling**, commits the diff, then researches and bets again.

The strategy's git log is the product: every commit is a lesson the agent paid
for (in paper) — and the honest metric is `brier_delta` (is the agent's
probability a better forecast than the market's own price?), not just P&L.

## Why simulation first

Hundreds of feedback loops across the whole market universe cost nothing and
answer the only question that matters before real money: *in which market
categories does fast AI research actually beat the price?* Real-funds trading
(via Pearl Connect's wallet on Polygon) is gated on that evidence AND a human
flipping `real_trading_enabled` — the agent cannot.

## Honest-simulation rules

- Paper fills cross the live CLOB spread (buy at best ask), like a real taker.
- Entry prices are recorded at bet time; resolutions are Polymarket's own.
- The agent cannot edit the engine (`core/`, `config/protected.json`);
  `loop.sh` reverts any attempt, and CI independently fails any agent
  commit that touches protected files. Caps: $10/bet max, 60 open positions,
  no market resolving <20 min out, no entries outside 2¢–95¢.

## Run

```bash
./loop.sh 10 45   # 10 cycles, 45 min apart (headless Claude Code)
python3 core/score.py   # calibration & P&L report any time
```

Requires [Claude Code](https://claude.com/claude-code) (`claude` on your
PATH) and Python 3. No API keys needed — market data comes from Polymarket's
public gamma/CLOB endpoints.

## Disclaimer

This is a research experiment in agent self-improvement, running entirely on
simulated money. Nothing here is financial, investment, or betting advice,
and the strategy's past paper performance predicts nothing. Prediction-market
trading is restricted or unlawful in some jurisdictions — know your own rules
before touching real funds.

## License

[Apache-2.0](LICENSE). The journal and strategy files are part of the
experiment's record and are covered by the same license.
