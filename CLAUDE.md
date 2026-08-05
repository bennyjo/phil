# Phil (self-improving trader)

A self-improving trading agent for short-term Polymarket markets. The
agent (Claude Code, headless) runs `CYCLE.md` repeatedly: settle → score →
retrospective → edit its own strategy → research → place simulated bets.

## Layout

- `core/` + `config/protected.json` — PROTECTED simulation engine (honest
  CLOB-ask fills, bankroll caps, official resolutions). The agent must never
  edit these; `loop.sh` reverts any such change. Also operator-owned: the
  top-level docs, `LICENSE`, and `.github/` (CI).
- CI (`.github/workflows/ci.yml`) runs on every push: `core/validate.py`
  integrity tripwires (real_trading_enabled stays false, JSONs parse, ledger
  rows respect the protected caps, Python compiles), a bug-class-only ruff
  pass, and a boundary guard — commits not prefixed `operator:` are agent
  commits and must not touch operator-owned paths. Human commits to protected
  files MUST use the `operator:` message prefix or CI fails the push.
- `strategy/` — the agent's own playbook, risk policy, and tools. This is what
  self-improves. Its git history IS the experiment's product.
- `journal/` — ledger (JSONL, written only by core), retros, cycle log.
- `CYCLE.md` — the per-cycle procedure the headless agent follows.

## Purpose

Paper is the 24/7 learning engine (cloud loop, hourly): find WHERE fast
research beats the market (calibration per category and edge class,
`brier_delta` in `core/score.py`). Real execution runs only on the
operator's machine via `./loop.sh --real`: qualifying paper bets (edge
classes in `config/protected.json` → `real.allowed_edge_classes`) get a $1
real twin on Polymarket through Pearl Connect.

## Real execution (operator machine only)

- Env: `PEARL_CONNECT_STORE` = Pearl Connect workspace dir (contains
  `.mcp.json`); optional `CONNECT_POLYMARKET_VENV` (default
  `~/.cache/connect-polymarket/venv`).
- `core/real.py` (protected) is the only code that touches funds — it wraps
  the connect-polymarket skill scripts Pearl Connect provisions, enforces
  the `real` caps block, and is the sole writer of
  `journal/real-ledger.jsonl` (paper `ledger.jsonl` discipline mirrored).
- `real_trading_enabled: true` + the `real` caps block are validated by CI
  (`core/validate.py` hard ceilings). Editing either is an operator act.
- REAL.md is appended to the cycle prompt only in real mode; loop.sh
  downgrades to paper with a warning if the signer isn't ready.
