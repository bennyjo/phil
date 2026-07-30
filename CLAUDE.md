# self-improving-trader

A self-improving paper-trading agent for short-term Polymarket markets. The
agent (Claude Code, headless) runs `CYCLE.md` repeatedly: settle → score →
retrospective → edit its own strategy → research → place simulated bets.

## Layout

- `core/` + `config/protected.json` — PROTECTED simulation engine (honest
  CLOB-ask fills, bankroll caps, official resolutions). The agent must never
  edit these; `loop.sh` reverts any such change.
- `strategy/` — the agent's own playbook, risk policy, and tools. This is what
  self-improves. Its git history IS the experiment's product.
- `journal/` — ledger (JSONL, written only by core), retros, cycle log.
- `CYCLE.md` — the per-cycle procedure the headless agent follows.

## Purpose

Phase 1 (now): simulation only — find out WHERE fast research beats the market
(calibration per category, `brier_delta` in `core/score.py`) across hundreds
of paper bets. Phase 2 (gated on evidence + human sign-off): route the proven
strategy through Pearl Connect's wallet for real USDC trades on Polygon.

`config/protected.json` has `real_trading_enabled: false`. Flipping it is a
human decision, never the agent's.
