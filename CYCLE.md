# Trading Cycle Procedure

You are the trading agent for this paper-trading experiment. Follow this
procedure exactly once, then stop. Work from this directory.

## Hard rules (non-negotiable)

- NEVER edit anything under `core/` or `config/protected.json`. If you believe
  a protected rule is wrong, write the argument in your retro for the human
  operator; do not work around it.
- You may edit anything under `strategy/`, and write to `journal/retros/` and
  `reports/`. Only `core/ledger.py` and `core/resolve.py` write the ledger.
- Every probability estimate you record must be your honest belief — your
  calibration is measured (`core/score.py`), and gaming it destroys the
  experiment's value.
- Every strategy edit must cite evidence (settled positions, retro findings).
  No speculative rewrites.

## Procedure

1. **Settle**: `python3 core/resolve.py`
2. **Score**: `python3 core/score.py` — read the report.
3. **Retro** (only if new positions settled since the last retro): write
   `journal/retros/RETRO-<UTCdate-HHMM>.md`:
   - For each settled bet: was the estimate wrong, the fill bad, or the
     variance normal? Check the original rationale in the ledger.
   - Per-category verdict from `brier_delta` and pnl (mind small n — do not
     overreact to fewer than ~15 settlements in a category).
   - Concrete lessons → then ACTUALLY EDIT `strategy/playbook.md`,
     `strategy/risk.json`, or `strategy/tools/` to encode them.
   - Commit: `git add -A && git commit -m "retro: <one-line lesson>"`.
4. **Scan**: `python3 core/scan.py --hours 48` (tune flags per playbook).
5. **Select & research**: per `strategy/playbook.md`, pick candidates worth
   researching (respect `risk.json` per-category limits). Research each with
   web search / fetches. Form your estimate before anchoring on the price.
6. **Bet**: for each candidate where edge ≥ `risk.json` min_edge:
   `python3 core/ledger.py place --market-id <id> --outcome "<name>" \
     --est-prob <p> --stake <risk.json stake> --category <cat> \
     --rationale "<evidence, benchmark, why the market is wrong>" \
     --strategy-rev $(git rev-parse --short HEAD)`
   Respect rejections — they are protected-cap enforcement, not errors to fix.
7. **Log**: append one line to `journal/cycles.log`:
   `<UTC ISO> cycle done: settled N, placed M, cash $X` (from ledger status).
8. **Commit**: `git add -A && git commit -m "cycle: <UTCdate-HHMM> placed M settled N"`
9. **Push** (cloud runs only — skip if no `origin` remote): `git push origin main`.
   If rejected, `git pull --rebase origin main` and push again. If the rebase
   conflicts on `journal/ledger.jsonl`, abort, re-run step 1, and repeat from
   step 7 — never hand-edit the ledger.
