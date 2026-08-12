# Trading Cycle Procedure

You are the trading agent for this paper-trading experiment. Follow this
procedure exactly once, then stop. Work from this directory.

## Hard rules (non-negotiable)

- NEVER edit anything under `core/`, `config/`, or `.github/`, nor the
  operator's top-level files (`CYCLE.md`, `REAL.md`, `loop.sh`, `CLAUDE.md`,
  `LICENSE`, `README.md`, `.gitignore`). If you believe a protected rule is
  wrong, write the argument in your retro for the human operator; do not work
  around it. CI fails the push on any non-`operator:` commit touching these
  paths.
- You may edit anything under `strategy/`, and write to `journal/retros/` and
  `reports/`. Only `core/ledger.py` and `core/resolve.py` write the ledger;
  only `core/forecast.py` and `core/resolve.py` write `journal/forecasts.jsonl`.
- Every probability estimate you record must be your honest belief — your
  calibration is measured (`core/score.py`), and gaming it destroys the
  experiment's value.
- Every strategy edit must cite evidence (settled positions, retro findings).
  No speculative rewrites.

## What is mine to change (added 2026-08-03)

I own my **judgment** (`strategy/playbook.md`, `strategy/risk.json`), my
**tools** (`strategy/tools/`), my **sensing** (`strategy/discovery.py` — the
market queries `core/scan.py` runs), and my **pacing**
(`strategy/schedule.json` — which hourly ticks get a full cycle).

I do not own the protected filters, the ledger, resolution, scoring, the caps,
or this procedure. When the thing that needs changing is one of those, the
answer is never to work around it: append to `journal/proposals.md` with the
evidence. **A structural oddity in my inputs is a proposal, not a shrug** — if
every candidate sits in one bucket, a whole research channel fails, or a
category never appears, say so there. Cycle logs record symptoms; proposals
get causes fixed.

## Procedure

0. **Sync**: `git fetch origin main` (if it fails or there is no origin,
   note it in the cycle log line and continue on local state). If local
   `main` is strictly behind `origin/main`, fast-forward:
   `git checkout -B main origin/main`. If the histories have genuinely
   diverged, log a warning for the operator and continue on local state —
   never reset over local commits. Then the **collision guard**: if
   `origin/main`'s tip is a `cycle:` commit committed less than 20 minutes
   ago, another runner just cycled — run this invocation as a LIGHT tick
   (step 1 and the open-position monitor only), regardless of pacing state.

0b. **Pace**: read `strategy/schedule.json`. If `next_full_cycle_after` is in
   the future AND at least `min_full_cycles_per_day` full cycles ran in the
   last 24h (`journal/cycles.log`), run a LIGHT tick: steps 1 and the
   open-position monitor only, log one line, commit, stop. Otherwise run the
   full procedure. Update the file (with a reason) whenever the coming hours
   look genuinely empty — and clear it when they don't.

0c. **CI health** (full cycles only): `python3 core/ci.py` reports the CI
   verdict for the last pushed commits. On `"status": "failure"`, acting on
   it is part of this cycle: read the failed check names, find the cause
   (`git log` + reading the flagged files usually suffices — CI runs
   `core/validate.py`, a `ruff --select E9,F` lint over `core` and
   `strategy`, and the operator-boundary guard). If the cause lives in my
   paths (`strategy/`, `journal/`), fix it now and note it in the cycle log
   line; if it lives in protected paths, append the evidence to
   `journal/proposals.md`. Red CI is never left standing without one of
   those two actions. On `"unknown"` (API unreachable), log it and move on;
   never scrape around it.

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
   - Settled forecasts are graded the same way (deep retros additionally
     reconcile `journal/forecasts.jsonl` coverage against funnel researched
     entries, and grade skip reasons against settled forecast outcomes).
   - Commit: `git add -A && git commit -m "retro: <one-line lesson>"`.
4. **Scan**: `python3 core/scan.py --hours 336 --limit 800` — queries come from
   `strategy/discovery.py`, which is mine to edit. Read scan's stderr: it
   reports each query's yield, and says loudly if my discovery module was
   unusable and it fell back. If a query is returning nothing useful, fix the
   query rather than lowering my standards.
5. **Select & research**: per `strategy/playbook.md`, pick candidates worth
   researching (respect `risk.json` per-category limits). Research each with
   web search / fetches. Form your estimate before anchoring on the price.
   For sports benchmarks and event status, use `python3 core/odds.py`
   (keyed the-odds-api client: `sports` lists keys, `odds <sport>` returns
   decimal lines for `strategy/tools/devig.py`, `scores <sport>` pins match
   status — the replacement for the 403-blocked odds/live-score sites). It
   enforces a hard monthly credit budget (`quota` shows state; spend is
   logged in `journal/odds-quota.json`): identical calls within 10 minutes
   are cached and free, but budget the rest — roughly 10-12 credits/day
   across all cycles. If it reports the key missing or the budget exhausted,
   log that and skip; never scrape around it.
5b. **Forecast**: for EVERY candidate you researched to a concrete (market,
   outcome, probability) — including no-edge and market-agrees skips:
   `python3 core/forecast.py record --market-id <id> --outcome "<name>" \
     --est-prob <p> --category <cat> --skip-reason <bet|no-edge|market-agrees|...> \
     [--fit-score N] [--note "..."] --strategy-rev $(git rev-parse --short HEAD)`
   No stake, no edge floor — this is how your calibration gets feedback on
   research that doesn't become a bet (scored as brier_delta vs the market
   MID, separately from bets, in score.py). For candidates you intend to
   bet, record the forecast with `--skip-reason bet` BEFORE running `place`.
   Put the returned id in the cycle's funnel row as `forecast_id`. Skips
   where no concrete probability was formed (e.g. benchmark-unreachable)
   get no forecast — never invent an estimate. est_prob is your honest
   belief formed before anchoring on the price, exactly as for bets.
6. **Bet**: for each candidate where edge ≥ `risk.json` min_edge:
   `python3 core/ledger.py place --market-id <id> --outcome "<name>" \
     --est-prob <p> --stake <risk.json stake> --category <cat> \
     --edge-class <info-race|cross-market|book-devig|other> \
     --rationale "<evidence, benchmark, why the market is wrong>" \
     --strategy-rev $(git rev-parse --short HEAD)`
   `--edge-class` is the playbook edge class the bet claims — score.py now
   splits brier_delta by it, so classify honestly, not aspirationally.
   Respect rejections — they are protected-cap enforcement, not errors to fix.
7. **Log**: append one line to `journal/cycles.log`:
   `<UTC ISO> cycle done: settled N, placed M, cash $X` (from ledger status).
8. **Commit**: `git add -A && git commit -m "cycle: <UTCdate-HHMM> placed M settled N"`
9. **Push** (cloud runs only — skip if no `origin` remote): `git push origin main`.
   If rejected, `git pull --rebase origin main` and push again. If the rebase
   conflicts on `journal/ledger.jsonl`, abort, re-run step 1, and repeat from
   step 7 — never hand-edit the ledger.
