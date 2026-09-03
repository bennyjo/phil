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

## Tick types

Every invocation runs as one of three ticks:

- **FULL**: the whole procedure below.
- **LIGHT**: step 1 and the open-position monitor only, then log, commit, stop.
  Entered from the collision guard (step 0) or from pacing (step 0b).
- **TRIGGERED**: invoked by the watch routine when `core/watch.py check`
  reported `trigger: true` this session. Skip step 0b's pacing and step 4's
  broad scan: the candidate set is the verdict's `context` array (plus at most
  one narrow gamma fetch when the trigger is a new market). Every other step
  runs normally, scoped to those candidates. Before placing any bet, check the
  ledger for an existing open position on the same market - a duplicate inside
  the hour means the watcher double-fired: log it, do not re-bet. Triggered
  cycles do not count toward `min_full_cycles_per_day`.

## Procedure

0. **Sync**: first, if `git rev-parse --is-shallow-repository` prints
   `true`, run `git fetch --unshallow origin` (if the remote refuses, fall
   back to `git fetch --deepen=1000 origin`) — a shallow boundary
   manufactures fake divergence ("forced update" fetch lines, no
   merge-base), and no behind/diverged judgment is valid until it is gone.
   Then `git fetch origin main` (if it fails or there is no origin,
   note it in the cycle log line and continue on local state). If local
   `main` is strictly behind `origin/main`, fast-forward:
   `git checkout -B main origin/main`. If the histories have genuinely
   diverged, log a warning for the operator and continue on local state —
   never reset over local commits. Then the **collision guard**: if
   `origin/main`'s tip is a `cycle:` or `cycle(triggered):` commit committed
   less than 20 minutes ago, another runner just cycled — run this invocation
   as a LIGHT tick (step 1 and the open-position monitor only), regardless of
   pacing state. A TRIGGERED invocation is exempt and proceeds through the
   guard (`core/watch.py` already applied its own suppression before firing),
   with one exception: if the tip is a `cycle(triggered):` commit less than 45
   minutes old naming the same trigger key, demote to LIGHT.

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
4. **Scan & screen**: `python3 core/scan.py --hours 336 --limit 800 |
   python3 core/screen.py prepare` — queries come from `strategy/discovery.py`,
   which is mine to edit. Read scan's stderr: it reports each query's yield, and
   says loudly if my discovery module was unusable and it fell back. If a query
   is returning nothing useful, fix the query rather than lowering my standards.
   Then screen the pool with my own subagents - there is no API path, the
   screening judgment runs on the subscription:
   - Read `prepare`'s JSON header on stdout: `work_dir`, `batches` (one entry
     per batch file), `screened_pool`, `dropped_by_reason`, and
     `subagent_prompt_template`. `strategy/screener-strata.json` tunes which
     markets reach the pool; `dropped_by_reason` says what the strata cut.
   - Spawn ONE Task subagent PER BATCH FILE, all in parallel in a single
     message (model `haiku` when the Task tool lets me choose it, otherwise the
     default). Give each subagent exactly `subagent_prompt_template` with the
     literal `NN` replaced by that batch's `nn`, and nothing else. Each writes
     `<work_dir>/out-NN.json` itself; I do not relay its answers.
   - When every subagent has finished: `python3 core/screen.py collect --dir
     <work_dir>`. It validates the out files, computes divergence, appends
     `journal/screener.jsonl`, and prints the top rows plus a stderr summary
     (collected X/Y, escalated N, day batches Q/CAP).
   Research allocation in step 5 STARTS from collect's top divergences - but
   the screener ranks, it does not gate: watch items, the mechanical-econ
   calendar and the sibling census still claim their research slots under the
   existing rules. The funnel line gains three mandatory fields: `screened`,
   `escalated`, `screener_batches`. If `prepare` reports quota exhaustion, the
   Task tool is unavailable, or `collect` yields nothing, fall back to the
   current unscreened selection and say so in the funnel line.
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
5a. **Mech second opinion** (only when the `mcp__pearl-connect__mech_*`
   tools are present in this session - operator-machine runs with the Pearl
   Connect signer up; cloud cycles skip this step entirely): for candidates
   you researched to a concrete estimate, buy an independent prediction from
   the Olas mech marketplace (~$0.01 USDC per request, paid from the service
   safe). The point is comparison: over time, learn which mech tools are
   informative and say so in retros.
   - Form your OWN estimate first, before requesting. The mech's answer is
     evidence like any other: if it honestly moves your belief, your
     recorded est-prob moves - but always note your pre-mech estimate.
   - **Current test focus (operator, 2026-09-03):** the three Polygon
     predict mechs run mech-predict v0.21.29 and newly serve
     `superforcaster-market-aware` next to `superforcaster-polymarket-v4`.
     Exercise the new tool deliberately:
     - Mechs (all price 10000 = 0.01 USDC, all report `offchain_capable:
       false`, so pass `legacy_on_chain=true` - verified end to end
       2026-09-03): service 21 `0x76a9a29441c7acd072b03e63911f0e177de56ab7`,
       service 44 `0xe7f818513a48d74c99b8bde153bee0b70dbb300b`, service 25
       `0x45f25db135e83d7a010b05ffc1202f8473e3ae7d`. Rotate `priority_mech`
       across the three from one candidate to the next so every mech gets
       exercised; note in retros if one mech behaves differently.
     - Primary request per candidate: `superforcaster-market-aware`. For
       at least one candidate per cycle also send the same prompt to
       `superforcaster-polymarket-v4` on the same mech (a paired
       comparison). That is the one case where a candidate may get two
       requests.
     - Prompt: one precise resolution question (criteria, resolution
       source, deadline in UTC - never just the market title), the market
       question itself as a single sentence ending in `?`, and no other
       `?` sentences. Do NOT put the market price in the prompt: the tool
       reads market context only from a `request_context` field that
       `mech_request` cannot send, so it runs blind here
       (`market_prob_seen` is null) and its `p_independent` stays a true
       price-free estimate to compare against yours and the mid.
     - Read the whole delivery: the `result` JSON (`p_yes`, `p_no`,
       `confidence`, `info_utility`, `researchability` 0..1,
       `research_class` R / REVIEW / NR-*, `research_reason`,
       `evidence_quality`, `market_prob_seen`, `p_independent`) and
       `metadata.params` (`parse_tier` template/clause/raw,
       `scan_truncated`, `null_reason` when p_yes is null, `model`). A null
       `p_yes` with a `null_reason` is a designed outcome (unsearchable
       question), not a failure - record it as such.
     - Log EVERY request, including failures, right after it returns:
       `python3 core/mechlog.py record --market-id <id> --mech <address> \
         --tool <tool> --request-id <your id> --own-p <pre-mech p> \
         --market-p <mid> --result-json '<result string>' \
         --params-json '<metadata.params as JSON>' \
         --latency-ms <execution_latency_ms> [--error "..."]`
       (`journal/mech-requests.jsonl`; retros grade it).
     - Things worth calling out in the cycle summary and retros: the mech's
       `research_class`/`researchability` versus your own read of whether
       the question is mechanical or interpretive; `parse_tier` other than
       `clause` (the search query was not the market question);
       `scan_truncated` true; `p_independent` differing from `p_yes` (it
       should not while the tool is blind); errors or timeouts; and how
       market-aware compares with v4, you, and the market at settlement.
   - `mech_tools()` lists live mechs; call it again with
     `priority_mech=<address>` for a mech's tool names and price
     (`max_delivery_rate`, base units of its payment asset).
   - Call `mech_request` with `tool`, `priority_mech`, `legacy_on_chain`
     set as above, `max_payment` 20000 (0.02 USDC), and a `request_id` you
     invent, so a retry can never pay twice.
   - Record the comparison in the step-5b forecast `--note` (and in a
     bet's rationale) as `own:<pre-mech p> mech:<tool>=<p_yes>
     r=<researchability> cls=<research_class>`, so retros can grade the
     mech against you and against the market.
   - No mech failure is ever blocking: insufficient funds, a guardrail
     refusal, a timeout, an unreachable mech - log one line (and a
     `mechlog.py record --error`) and proceed without the second opinion.
     On timeout you may poll each id in `pending_request_ids` once with
     `mech_result`; do not wait beyond that, and never re-send a request
     whose outcome you don't know without its original `request_id`.
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
   On a TRIGGERED cycle the detail that follows opens with
   `(TRIGGERED cycle: <key>` before anything else, so the tick type stays
   greppable.
8. **Commit**: `git add -A && git commit -m "cycle: <UTCdate-HHMM> placed M settled N"`
   A TRIGGERED cycle commits as
   `cycle(triggered): <UTCdate-HHMM> <key> placed M settled N` instead - the
   key in the subject is what watch.py's 45-minute same-key guard reads.
9. **Push** (cloud runs only — skip if no `origin` remote): first, if
   `git symbolic-ref -q HEAD` prints nothing, HEAD is detached — reattach
   with `git checkout -B main HEAD` (from a detached HEAD, `git push origin
   main` pushes the stale branch ref and reports success while your commits
   never leave the container).

   **If the environment variable `PHIL_PUSH_BY_LOOP` is set, stop step 9
   here.** You are running on the operator's machine, where the git
   credential lives in the OS keyring and a push from this session hangs on
   a prompt you cannot answer. `loop.sh` pushes for you after you exit. Do
   the detached-HEAD reattach above (the runner needs `main` pointing at
   your work), then log the cycle as normal — an unpushed commit is expected
   here, not a discrepancy to diagnose.

   Otherwise, `git push origin main`.
   If rejected, `git pull --rebase origin main` and push again. If the rebase
   conflicts on `journal/ledger.jsonl`, abort, re-run step 1, and repeat from
   step 7 — never hand-edit the ledger.
   Finally, verify the push took: `git fetch origin main`, then
   `git rev-parse HEAD` and `git rev-parse origin/main` must print the same
   hash. If they differ, the push did not publish your work — do not log it
   as done; diagnose (detached HEAD again? rejected push?) and repeat this
   step until the hashes match or you have written the discrepancy into the
   cycle log line for the operator.
