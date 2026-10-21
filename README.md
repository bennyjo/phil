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
universe: earnings beats, daily sports, pre-match esports, official economic
prints, near-term news. Crypto up-or-down coin-flips are banned. Every cycle
it settles yesterday's bets against official resolutions and scores its own
calibration against the market price it paid. It writes a retrospective when
bets have settled. A swarm of cheap screening subagents scores ~300 markets
per full cycle against the live price (`core/screen.py`), and the agent
spends its research slots on the largest divergences. It **edits its own
playbook, risk policy, tooling, sensing** (the market-discovery queries and
the screening prompt) **and pacing** (which hourly ticks deserve a full
cycle). Then it commits the diff, researches, and bets again.

Three layers keep it honest:

- an **hourly cycle agent** that screens, researches, bets, and self-edits,
  plus lightweight **watchers** (`core/watch.py`) that check every ~15
  minutes for new listings and price moves on the agent's watchlist and
  trigger an early cycle when something fires;
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
the whole market universe, with watcher ticks every ~15 minutes in between,
because hundreds of simulated feedback loops cost nothing and answer the
question that matters: *in which market categories does fast AI research
actually beat the price?*

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

## Repository layout

The operator owns the engine, and the agent owns its strategy and its
record. The following table lists who owns each path:

| Path | What it holds | Owner |
|---|---|---|
| `core/` | The engine: market scan, screening, ledger and fills, settlement, scoring, real execution (`real.py`), the runner lease, integrity tripwires (`validate.py`), and offline tests (`test_*.py`) | Operator |
| `config/protected.json` | Bankroll, stake and position caps, banned question patterns, screener tunables, and the real-execution caps | Operator |
| `CYCLE.md`, `REAL.md` | The procedure the agent follows each cycle, and the addendum for real mode | Operator |
| `loop.sh` | Runs cycles headlessly with Claude Code and reverts agent edits to operator-owned paths | Operator |
| `.github/`, `.claude/` | CI, the boundary guard, community files, and subagent definitions | Operator |
| `strategy/` | Playbook, risk policy, discovery queries, screener prompt, pacing schedule, watchlist, and tools | Agent |
| `journal/` | Ledger, forecasts, retrospectives, cycle log, operator notes, and proposals | Agent, with ledger rows written only through `core/` and operator notes by the operator |

## Quickstart

The engine is Python 3 standard library only, so there is nothing to
install. CI runs on Python 3.12. These commands work on a fresh clone:

```bash
git clone https://github.com/bennyjo/phil.git
cd phil
python3 -m unittest discover -s core -p 'test_*.py'   # offline tests
python3 core/validate.py                              # integrity tripwires
python3 core/score.py                                 # calibration and P&L report
```

`core/score.py` fetches live prices to mark open positions to market. To run
it offline, add `--skip-mtm`. Market data needs no API key; it comes from
Polymarket's public gamma and CLOB endpoints.

## Run cycles

A cycle is a headless [Claude Code](https://claude.com/claude-code) session
that follows `CYCLE.md`. `loop.sh` runs cycles one after another:

```bash
./loop.sh 10 45               # 10 paper cycles, 45 minutes apart
./loop.sh 1 45 --real         # one cycle with real twins via Pearl Connect
python3 core/real.py doctor   # is the real-execution path ready?
```

Before you run `loop.sh`, know what it does:

- It needs `claude` on your `PATH`, and each cycle uses your Claude Code
  account. `loop.sh` pins the model per cycle (`claude-opus-5-5`, or
  `claude-sonnet-5` when the pacing schedule makes the tick light) and runs
  the session with `--permission-mode acceptEdits` and a fixed tool
  allowlist that includes web search and web fetch.
- Each cycle commits, and `loop.sh` pushes to `main` on your `origin`
  remote. Before each cycle it takes the runner lease (`core/lease.py`),
  which is also a push to `origin`. On a clone that can't push to `origin`,
  such as a clone without write access, every tick is skipped with
  `WARNING: runner lease not taken`. To run your own Phil, fork the
  repository and clone your fork. To run locally without pushing anywhere,
  remove the remote with `git remote remove origin`; without an `origin`
  remote, the lease and the push are both skipped.
- A fork starts from Phil's state on the day you fork it: the ledger, open
  positions, strategy, and journal.
- Cycles stay on paper unless all of these hold: you pass `--real`,
  `PEARL_CONNECT_STORE` is set, the local Pearl Connect signer is healthy,
  and `python3 core/real.py doctor` reports ready. `real_trading_enabled` is
  `true` in this repository's `config/protected.json`; to turn real mode off
  in code, set it to `false`.
- With `PEARL_CONNECT_STORE` set and the signer up, paper cycles can also buy
  second-opinion predictions from the Olas mech marketplace, about $0.01
  USDC each, paid from the service Safe (`CYCLE.md` step 5a).

In Phil's own deployment, the hourly cycle, the watcher, and the daily deep
retro run as scheduled cloud routines that the operator configures outside
this repository. `loop.sh` is the runner that ships with it.

## Configuration

Caps and engine settings live in `config/protected.json`; the agent's sizing
policy lives in `strategy/risk.json`, inside those caps. All environment
variables are optional:

| Variable | Read by | Purpose |
|---|---|---|
| `PEARL_CONNECT_STORE` | `loop.sh`, `core/real.py` | Pearl Connect workspace directory (contains `.mcp.json`). Enables mech second opinions and, with `--real`, real twins. |
| `CONNECT_POLYMARKET_VENV` | `core/real.py` | Virtual environment of the connect-polymarket skill scripts. Defaults to `~/.cache/connect-polymarket/venv`. |
| `ODDS_API_KEY` | `core/odds.py` | Key for the bookmaker-odds benchmark from [the-odds-api.com](https://the-odds-api.com). Falls back to `~/.config/phil/odds-api-key`. |
| `HEADLINE_ARENA_AGENT_ID`, `HEADLINE_ARENA_CLIENT_SECRET` | `core/headline_arena.py` | Credentials for Headline Arena daily questions. Fall back to `~/.config/phil/headline-arena.json`. Without them, the step is off. |
| `PHIL_RUNNER` | `core/screen.py`, `core/lease.py` | Runner name for the lease and the screener quota. Defaults to `operator` under `loop.sh`, else `cloud`. |

Keep keys and tokens outside the repository. The journal and strategy are
public, and every cycle commits them.

## Status

Phil is a running experiment, not a versioned release. The agent commits to
`main` many times a day, and `main` is the only supported version. For the
current score, run `python3 core/score.py` or read the newest retrospective
in `journal/retros/`.

## Disclaimer

This is a research experiment in agent self-improvement. Most trading is
simulated. A small real-money leg runs through Pearl Connect only when the
operator deliberately enables it: per-bet and daily stakes are capped in
`config/protected.json`, and the wallet holds only what the operator funds.
Nothing here is financial, investment, or betting advice. Past performance,
paper or real, predicts nothing. Prediction-market trading is restricted or
unlawful in some jurisdictions. Know your own rules before running any of
this with real funds.

## Contributing and security

- [Contributing guide](.github/CONTRIBUTING.md): what is accepted, and the
  checks to run before a pull request.
- [Code of conduct](.github/CODE_OF_CONDUCT.md)
- [Security policy](.github/SECURITY.md): report anything that touches funds,
  keys, or the protected boundary privately.

## License

[Apache-2.0](LICENSE). The journal and strategy files are part of the
experiment's record and are covered by the same license.
