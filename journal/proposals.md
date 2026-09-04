# Proposals to the operator

Things I cannot change myself, with the evidence for changing them. The daily
deep retro reviews this file and elevates what it agrees with; the human
operator acts. Append, never rewrite history. Format:

## <UTC date> — <one-line ask>
**Evidence:** ...
**Proposed change:** ...
**Status:** open | endorsed by deep-retro | actioned | rejected (reason)

---

## 2026-08-03 — (seed) escalate suspicious absences, don't just log them

**Evidence:** 19 consecutive cycles logged "no qualifying candidate" while the
true cause was that `core/scan.py` could not page past day 0. Every log line
was accurate; none of them said "my instrument may be truncating". The cause
was invisible from inside the loop and cost ~2 days of learning.

**Proposed change:** now implemented by the operator — `strategy/discovery.py`
(I own the queries) and this file (I can escalate). Standing rule for me: if
a structural pattern in my *inputs* looks wrong — all candidates in one bucket,
a whole source class failing, an entire category never appearing — write it
here rather than only noting the symptom in a cycle log.

**Status:** actioned (operator, 2026-08-03)

---

## 2026-08-04 — restore benchmark AND event-status reachability (4th day, scope widened)

**Evidence:** 23 consecutive no-bet cycles 2026-08-03/04, every one on
benchmark failure, not thresholds (max clean devig edge seen 0.028 vs the
0.07 floor). New this window: the reachability problem covers *event status*
too — 2026-08-04 04:16Z found real bookmaker lines with plausible paper edges
on two ATP matches (Draper, Tsitsipas) but Sofascore, Flashscore, ESPN,
TennisExplorer and Olympics.com all 403 from the datacenter IP, so in-play
status could not be verified and both were correctly skipped. Tennis — the
highest-liquidity category the fixed scan now surfaces ($200k-460k books) —
is visible and priceable but structurally untradeable without a status
source.

**Proposed change:** (i) provision an odds API key (the-odds-api.com free
tier, ~500 req/mo, clean JSON for major leagues), and (ii) any one
allowlisted/keyed live-score or schedule source so match status can be
pinned. Together these unblock the two largest liquid categories in the
weekly window and finally give min_edge_book_devig (0.07) real tests.

**Status:** rejected (operator, 2026-08-04 — no odds API key or allowlisted
status source will be provisioned. Stop carrying this item day-to-day.
Strategy must work within what is reachable: WebSearch-derived multi-book
consensus where available, and market types whose benchmarks and event
status don't depend on 403-blocked sports sites — e.g. scheduled
economic/corporate releases, countable-metric markets, and
mechanically-resolving events.
**Re-open condition:** this rejection is contingent, not permanent. If deep
retros find that benchmark/status unreachability is materially blocking the
experiment despite the strategy pivot — e.g. placement rate stays well below
Phase-1 sample needs for ~a week with cycle logs attributing the misses to
unreachable benchmarks rather than thresholds or judgment — raise it as a
NEW proposal citing that evidence, and quantify what fraction of skipped
candidates the key would have unblocked)

---

## 2026-08-04 — Iran pair: manual UMA look is overdue

**Evidence:** `b21e42c123a1` and `d2dd24206542` are 4+ days past their
2026-07-31T23:59Z end date, `umaResolutionStatus` None throughout. Ceasefire
No marked ~0.475 and oscillating 0.355-0.545 across single days — the market
treats a thesis logged as "structurally impossible" as a coin flip, which is
resolver-process information we cannot see from gamma. DEEP-2026-08-02 e.4
set this look for ~2026-08-04; it is now due. The grading of $10 of exposure
(and whether the info-race class goes 2W/4L) turns on WHY this resolves.

**Proposed change:** human look at the UMA proposal/dispute history for both
markets; paste findings into journal/operator-notes.md.

**Status:** actioned (operator, 2026-08-04 — findings in operator-notes.md:
Iran-Gulf resolved No via normal UMA flow and is settled; ceasefire has NO
UMA proposal at all, contested ~50/50, unbounded tail)

---

## 2026-08-04 — loop.sh git hardening (carried)

**Evidence:** the 2026-07-31 silent 46h fork (orphaned local main) shape
remains possible; the 818281b merge fixed the instance, not the startup
sequence.

**Proposed change:** `git fetch origin main && git checkout -B main
origin/main` at cycle start in loop.sh.

**Status:** actioned (operator, 2026-08-04 — fetch + fast-forward-only sync
at cycle start; divergence warns instead of auto-resetting)

---

## 2026-08-04 — core/score.py: edge_class per ledger row + open-position mark-to-market (carried)

**Evidence:** class-level brier_delta (the experiment's primary question:
structural vs book-devig) is hand-assembled in every deep retro from
rationale text; open stuck positions ($10 currently marked to ~$2.9) appear
nowhere in score output, per the operator's own 2026-08-03 note.

**Proposed change:** core/place.py stamps `edge_class` on new ledger rows;
core/score.py groups brier_delta by it and adds an MTM line for open
positions past end date.

**Status:** actioned (operator, 2026-08-04 — ledger.py place now REQUIRES
--edge-class {info-race,cross-market,book-devig,other}; score.py reports
by_edge_class (old rows show as "unclassified"), a luck-adjusted
expected-wins/z line, and best-effort live MTM for open positions
(--skip-mtm to disable). CYCLE.md bet template updated. First run of the
z line over the 17 settled bets: expected wins under own estimates ~10 vs
5 actual, z=-2.61 — estimates look systematically overconfident, not
unlucky)

---

## 2026-08-04 — scheduled-trigger cycles bypass loop.sh's git sync

**Evidence:** this session was invoked directly ("Read CYCLE.md and follow
it... once") by an external scheduled trigger, not via `./loop.sh`. loop.sh
has the fetch/fast-forward-only sync at cycle start (from the 2026-08-04 "git
hardening" proposal above), but a session invoked outside loop.sh never runs
it. This session started with a stale local `origin/main` remote-tracking ref
(pointed at 033ff6e from 2026-07-30, ~50 commits and 5 days behind the real
GitHub tip at 5a024eb) and a shallow clone whose truncation boundary
(2026-08-03 10:16Z) made the true history look like two unrelated lineages
under local `git log`/`merge-base`. Verified against GitHub directly (MCP
`list_commits`) that origin's real `main` tip matched the "detached" work
exactly — no actual divergence, no lost commits — then `git fetch origin
main` + reset local `main` to match resolved it this cycle. Same recurring
class of issue as the 06:24Z/10:17Z/15:22Z/17:14Z cycle-log notes, but this
time the local-ref state was stale enough to look like real history
divergence rather than a simple fast-forward, which is what makes it worth
flagging now rather than re-silencing with another local `git checkout -B`.

**Proposed change:** either (a) point the scheduled trigger's prompt at
`./loop.sh 1` instead of raw CYCLE.md so its git-sync guard always runs, or
(b) move the sync logic (fetch + fast-forward local main to origin/main,
warn-not-reset on genuine divergence) into CYCLE.md step 0 itself so it
applies regardless of invocation path. Not something I can fix myself since
it's loop.sh/CYCLE.md/trigger-config, all operator-owned.

**Status:** actioned (operator, 2026-08-04 — commit `6676f9d` added CYCLE.md
step 0 "Sync" with fetch + `checkout -B main origin/main`, commit message
explicitly cites the scheduled-trigger stale-clone class; confirmed by
deep-retro 2026-08-05)

---

## 2026-08-05 — deep-retro sessions still start on stale clones (residual of the item above)

**Evidence:** the CYCLE.md Sync step covers hourly cycle sessions, but the
daily deep-retro trigger follows its own prompt, not CYCLE.md. Today's
deep-retro session started detached at the correct tip but with local `main`
still pointing at pre-handover `033ff6e` (10 commits of dead history, no
common ancestor with origin/main under the shallow clone), and a plain
`git checkout main` + `git pull` dead-ends on "divergent branches". Recovered
in-session via `git reset --hard origin/main`, same as the hourly agents used
to do by hand.

**Proposed change:** prepend the deep-retro trigger prompt's step 1 with the
same sync line CYCLE.md now uses: `git fetch origin main && git checkout -B
main origin/main` (warn, don't reset, if local commits exist). Trigger config
is operator-owned.

**Status:** actioned (operator, 2026-08-05 — deep-retro routine prompt step 1
now opens with the same fetch + fast-forward-only sync CYCLE.md uses, with
the warn-don't-reset rule on genuine divergence; takes effect from the next
04:40Z run; confirmed working by deep-retro 2026-08-06 — that session
synced cleanly at start, no stale-clone recovery needed)

---

## 2026-08-08 — reachability re-opened per the 2026-08-04 re-open condition; odds API provisioned

**Evidence (operator-initiated — the rejection's own re-open test is met):**
placement rate has been near zero for ~a week with cycle logs and deep retros
attributing the misses to unreachable benchmarks, not thresholds or judgment:
DEEP-2026-08-08 counts 15 of 35 researched candidates skipped
benchmark-unreachable in one window (vs no-edge 18, budget 2); the 2026-08-06
window measured min_edge_book_devig binding for the first time only because a
rare reachable line appeared. Meanwhile book-devig is the sole edge class with
a positive settled record post-power-devig-fix (2W/0L, brier_delta -0.0732 at
stamped n=1), so the blocked class is exactly the one the evidence favors.
Quantification the rejection asked for: an odds key would have unblocked the
benchmark-unreachable fraction directly (~43% of last window's researched
candidates), plus the tennis/status class flagged 2026-08-04.

**Change made:** `core/odds.py` (operator-owned, protected) — keyed
the-odds-api.com client: `sports` / `odds <sport>` (decimal, devig-ready) /
`scores <sport>` (event status) / `quota`. Key comes from `ODDS_API_KEY` or
`~/.config/phil/odds-api-key`, never the repo. Hard monthly budget guard at
450 of the 500 free-tier credits, spend tracked publicly in
`journal/odds-quota.json`, 10-min response cache so re-runs are free.
CYCLE.md step 5 now points at it. The agent cannot edit the guard; budget or
default complaints belong here.

**Status:** actioned (operator, 2026-08-08 — key provisioning on the cloud
runner is the remaining step; until the key lands, odds.py exits with
"key not provisioned" and cycles should log that rather than scrape)

## 2026-08-08 — odds.py key provisioned but api.the-odds-api.com is EGRESS_BLOCKED from the cloud runner

**Evidence:** first cloud-runner use of `core/odds.py` after the 2026-08-08
provisioning (this cycle, 22:1x Z): `python3 core/odds.py quota` shows a
valid key state (`used_credits: 0`, no "key not provisioned" exit), but
`python3 core/odds.py sports` fails both transport paths — urllib raises
`Tunnel connection failed: 403 Forbidden`, and the curl fallback (line 104)
also fails: `curl: (56) CONNECT tunnel failed, response 403`. Confirmed
directly: `curl -sS https://api.the-odds-api.com/v4/sports` through the
runner's `$HTTPS_PROXY` returns the same `CONNECT tunnel failed, response
403`. This is the sandbox egress proxy rejecting the CONNECT to
`api.the-odds-api.com`, not a the-odds-api-side auth/quota rejection (which
would be a 401/422 JSON body, handled separately in `fetch()`) — same
failure shape as the documented `clevelandfed.org`/`macromicro.me` blocks in
playbook.md, just not yet on the runner's allowlist. journal/proposals.md's
2026-08-08 entry anticipated a "key not provisioned" failure mode; this is a
different one (key is fine, host is blocked) and playbook.md's new odds.py
section (this cycle's commit) will produce an incorrect "log 'odds key not
provisioned', fall back" line if an agent doesn't distinguish the two exit
paths.

**Proposed change:** add `api.the-odds-api.com` to the cloud runner's
egress allowlist (the operator's own laptop reachability is not in
question — this is specifically the cloud-runner proxy, same class of fix
as the 2026-08-05 10:53Z Kalshi/Manifold allowlist update). Until then,
`core/odds.py` is usable only from the operator's local machine; cloud
cycles should log "odds EGRESS_BLOCKED (cloud runner)" and fall back to
WebSearch, distinct from "key not provisioned".

**Status:** rejected (deep-retro 2026-08-09 — moot/transient: api.the-odds-api.com
was reachable from the cloud runner at 2026-08-09 02:12Z and served a 6-credit
sweep with zero proxy errors, with no visible operator action in between. The
block was flapping, not a standing allowlist gap. Re-file citing at least two
dated CONNECT-403 instances if it recurs, so flapping infra can be
distinguished from a stale allowlist)

---

## 2026-08-08 — Polymarket's own APIs (gamma-api, clob) are now EGRESS_BLOCKED from the cloud runner, not just api.the-odds-api.com

**Evidence:** this cycle (23:1xZ, LIGHT tick), `python3 core/resolve.py`
failed to fetch market 2937525 from `gamma-api.polymarket.com`: `<urlopen
error Tunnel connection failed: 403 Forbidden>` (settled 0 of 19 as a
result — cannot be distinguished from "nothing resolved yet" without this
note). `strategy/tools/quote.py` on the one open position's token
(d2dd24206542, US x Iran ceasefire No) failed both its urllib and curl
fallback paths against `clob.polymarket.com/book`: curl exit 56 (connect
failure). Confirmed at the proxy layer, not app-layer: `curl -sS
"$HTTPS_PROXY/__agentproxy/status"` lists both hosts in
`recentRelayFailures` at 23:13:2x-28Z: `{"kind": "connect_rejected",
"detail": "gateway answered 403 to CONNECT (policy denial or upstream
failure)", "host": "gamma-api.polymarket.com:443"}` and the same for
`clob.polymarket.com:443`. This is the identical failure shape as the
2026-08-08 odds-api entry above (proxy CONNECT 403, not an app 401/404),
but on the two hosts the whole trading loop depends on for settlement and
live-book pricing — every prior cycle today (through 22:13Z) reached both
hosts fine, so this is a new/intermittent allowlist regression, not a
standing gap. Per CYCLE.md's operational note ("if Polymarket APIs are
unreachable, write the failure to journal/cycles.log, commit and push what
is valid, and stop"), this cycle stopped after settle+monitor without
placing bets or attempting scan/research.

**Proposed change:** re-check/re-add `gamma-api.polymarket.com` and
`clob.polymarket.com` to the cloud runner's egress allowlist alongside
`api.the-odds-api.com` — these three are now all showing the same
proxy-level CONNECT-403 pattern. Since these two hosts were reachable
earlier today, also worth checking whether the allowlist is flapping
rather than statically missing an entry.

**Status:** rejected (deep-retro 2026-08-09 — moot/transient: both hosts
served every tick after 23:13Z, including full settle/monitor/quote cycles;
same evidence and same re-file condition as the odds-api entry above)

---

## 2026-08-09 — status update: 2026-08-08 egress-block entries look transient, not standing

**Evidence:** this cycle (02:12Z), `api.the-odds-api.com`, `gamma-api.polymarket.com`,
`clob.polymarket.com`, `clevelandfed.org`, and `xtracker.polymarket.com` were
all reached from the cloud runner with zero proxy errors -- no CONNECT-403s,
no urllib/curl failures. This directly contradicts the two 2026-08-08 entries
above (both reporting `gateway answered 403 to CONNECT` on these same hosts).
Doesn't prove the allowlist was fixed rather than flapping; either way, future
cycles should keep re-testing reachability each time rather than assuming a
prior block still holds (already added as a playbook.md durable note).

**Proposed change:** none needed from the operator unless the block
recurs -- closing the loop on the open items above with this observation.
If a future cycle sees the same CONNECT-403 pattern again, that would argue
for flapping/intermittent infra rather than a one-time fix, worth a look.

**Status:** endorsed by deep-retro (2026-08-09 — correct closing observation;
the durable residue is the playbook rule to re-verify reachability each cycle
rather than trusting yesterday's block. The two 2026-08-08 entries above are
closed as moot on this evidence; recurrence condition documented there)

---

## 2026-08-10 — forecast.py: revision support (supersede a stale open forecast)

**Evidence:** PLBY earnings, 2026-08-10. The 00:23Z cycle recorded forecast
(est 0.28 @ ask 0.25, claimed edge 0.03, no-edge skip). By the 04:16Z cycle
the ask had moved 0.25 → 0.19 and the cycle re-verified the situation
(confirmed a real recency signal, declined the resulting 0.14 claimed edge
per the outside-view veto) — a materially sharper read. forecast.py's
one-live-row rule ("REJECTED: already have an open forecast on this
market+outcome") means the row that will be graded at settlement is the
stale 00:23Z estimate; the current belief is unscored. The docstring already
anticipates this: "revision support is a v2 question, on evidence" — this is
the evidence. The same shape will recur on any multi-day candidate whose
price or facts move between cycles (CPI brackets over the 2 days to release,
primaries over the last polling days).

**Proposed change:** `core/forecast.py record --supersede` (or automatic
when a row for market+outcome is open): write the new row with a
`supersedes: <old_id>` link, mark the old row `superseded` (excluded from
settlement scoring), and have resolve.py grade only the latest row. Keeps
the anti-flooding intent — correlated re-records of an unchanged estimate
should still be rejected (e.g. require |Δest_prob| ≥ 0.05 or a decision
change to supersede). Optionally score superseded rows in a separate
"revised-away" slice; that would measure whether revisions actually improve
estimates, which is calibration data too.

**Workaround until then (in place, playbook §Forecast ledger):** revised
reads recorded in funnel.jsonl notes so retros can weigh the current
estimate at settlement.

**Status:** endorsed by deep-retro (2026-08-11 — the gap now has a settled
worked example: PLBY resolved No with the stale 00:23Z row (est 0.28) as
the graded row and the materially different 04:16Z read (est 0.33)
unscored. Design note from that same settlement: the revision was WORSE
than the original against the outcome, so score revised-away rows as a
separate slice rather than assuming revisions improve estimates —
"do my revisions help?" is itself an open empirical question the
mechanism should answer. Low urgency confirmed; the funnel-note
workaround held up this window)

---

## 2026-08-11 — deep-retro trigger prompt: unshallow before judging divergence

**Evidence:** today's deep-retro session started on a SHALLOW clone
(2-commit boundary) with a stale origin/main ref. `git fetch origin main`
reported a spurious "forced update"; local main vs origin/main showed NO
merge-base and 50 "local-only" vs 50 "origin-only" commits — a textbook
false divergence, indistinguishable at first glance from a real
force-push. The trigger prompt's rule ("if the histories have genuinely
diverged, warn and continue on local state — never reset") is correct for
real divergence but destructive on this artifact: continuing on local
state would have meant auditing and editing a strategy tree 3 days stale,
and pushing conclusions derived from it. `git fetch --unshallow origin`
resolved it instantly — local main was strictly behind, plain
fast-forward, no divergence at all. Same failure family as the 2026-08-04
and 2026-08-05 stale-clone proposals (both actioned), one layer deeper:
those fixed stale REFS, this is the shallow BOUNDARY manufacturing fake
history.

**Proposed change:** in the deep-retro routine prompt's step 1 (and
arguably CYCLE.md step 0 — operator's call), before any behind/diverged
determination: `git rev-parse --is-shallow-repository` and, if true,
`git fetch --unshallow origin` (fall back to `--depth=1000` if the remote
refuses). Only then apply the behind ⇒ checkout -B / diverged ⇒ warn
rule. Trigger prompt and CYCLE.md are operator-owned.

**Status:** actioned (operator, 2026-08-13 — CYCLE.md step 0, loop.sh, and
the deep-retro trigger prompt all unshallow before any behind/diverged
determination; see operator-notes.md 2026-08-13. Confirmed working by
deep-retro 2026-08-14: first session with the guard in the prompt hit the
usual artifact — shallow clone, spurious "forced update" — and resolved it
per the guard: unshallow, plain 0-ahead/160-behind fast-forward, zero
recovery time. Prior history: endorsed 2026-08-12 after a second dated
instance; third benign instance recorded 2026-08-13)

---

## 2026-08-11 — core/score.py: forecasts by_skip_reason slice

**Evidence:** the most informative forecast split this window was
brier_delta by skip reason — no-edge n=41 at -0.0004 (at-market by
construction, as designed) vs architecture-mismatch n=2 at +0.1093 (the
market beat the naive model exactly as the skip reason predicts) vs
market-agrees n=2 at -0.0089 — and it was hand-computed in the deep
retro because score.py's forecasts section slices by category only.
Skip-reason calibration is the selection-grading the 2026-08-05 operator
mandate asked for ("did the skip reasons hold up in hindsight"), and
DEEP retros will need it every day as the disagreement rows settle
(outside-view-veto rows are the ones that grade the veto). Hand-computed
daily stats are the same failure class as the hand-asserted cycle counts
(v1-v3 lineage) — machine-computed or eventually wrong.

**Proposed change:** score.py forecasts section adds `by_skip_reason`
(same fields as by_category: n, wins, brier_agent, brier_market,
brier_delta). Nice-to-have in the same pass: `by_category` and
`by_skip_reason` both computed over settled rows only, with open-row
counts alongside, so slices can't be misread as including open rows.

**Status:** rejected (deep-retro 2026-08-12 — moot: the slice ALREADY
EXISTS. `by_skip_reason` has been in score.py's forecasts section since
operator commit a73bb92 (2026-08-09, the same commit that created the
forecast ledger), verified present in today's score run. DEEP-2026-08-11
hand-computed numbers the instrument already produced and filed this
without running/reading the tool first — same failure family as the
hand-asserted cycle counts. Lesson for future retros: before proposing an
instrument change, run the instrument and grep its source)

---

## 2026-08-13 — deep-retro status pass (no new asks)

**Open-item review, DEEP-2026-08-13:**

- **2026-08-11 unshallow-before-divergence-judgment (endorsed): third dated
  data point, benign form.** Today's deep-retro session again started on a
  shallow clone (50-commit boundary) and `git fetch origin main` again
  printed a spurious `+ 6bb2664...1a651a5 (forced update)`. No recovery time
  was burned this time only because HEAD happened to already sit at the
  origin tip — the artifact (shallow boundary + stale container-image main
  ref at 6bb2664) is still live and every hourly cycle log since 2026-08-12
  carries the same "local main ref stale at 6bb2664" recovery line. The
  endorsement stands; the guard belongs in the trigger prompt before the
  behind/diverged determination.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  unchanged priority.** No material revisions occurred this window (the one
  candidate that moved, AMAT, was correctly held as a duplicate estimate),
  so the funnel-note workaround again cost nothing. Low urgency confirmed
  for a second window.
- No new operator proposals. Nothing this window was blocked on protected
  code: the window's findings (sweep demotion, category-bar taxonomy,
  election-bar extension, recheck stop rule) were all implementable in
  strategy/ and are applied in this commit.

**Status:** informational (statuses of the two open items unchanged)

---

## 2026-08-14 — core/score.py: threshold_sweep No-side counterfactual slice

**Evidence:** the operator's 2026-08-09 note introducing the sweep said
"Only the forecasted outcome side is simulated; opposite-side
counterfactuals are a v2 question if the data argues for it." The data now
argues for it, with a settled worked example. The sweep computes edge as
`est_prob − recorded ask` on the forecasted (Yes) side, so a disagreement
where the model sits far BELOW a wide market — a No-side edge — is
excluded from every bucket. Consequence: the headline both DEEP-2026-08-13
and the risk.json notes have been carrying ("every sweep bucket negative;
zero settled instances of being right against the market") is a claim
about the Yes-side stream only. The settled No-side disagreements to date
both went the agent's way: PPI 5.3% (`5ad483698a95`, est 0.036 vs mid
0.171, No-side edge 0.097 realizable NET of the wide spread at No ask
0.867, bracket resolved No — a flat $5 bet wins +$0.77) and PPI ≥6.0%
(`4908388c9fd7`, est 0.003 vs mid 0.042 — not realizable through the
spread, correctly a non-trade, but still a settled row where the estimate
beat the market's mid). n=2 and event-correlated, worth nothing as edge
evidence yet — but the instrument should count this stream before anyone
concludes from the sweep that the disagreement pipe is uniformly bad.
RETRO-20260813-1707 separately mis-graded these two counterfactuals as
"both would have lost" (corrected in playbook, DEEP-2026-08-14): per-row
fill arithmetic in the instrument would have prevented the narrative error.

**Proposed change:** score.py threshold_sweep adds a No-side pass per
settled forecast row: complement edge = `(1 − est_prob) − (1 − best_bid_at_record)`
= `best_bid_at_record − est_prob`, i.e. buy No at `1 − best_bid`; bucket by
the same floors, report the same fields, in a parallel `threshold_sweep_no`
block (or a `side` field per bucket). Rows lacking `best_bid_at_record`
are skipped and counted. This keeps the existing Yes-side block unchanged
for continuity.

**Status:** endorsed by deep-retro (2026-08-16 — evidence strengthened a
third time: with the Musk 2-day pair settled, the No-side realizable
counterfactual stream is now 3W/3L **+0.32u** (the only positive stream in
the veto ledger) and the Yes-side stream 1W/4L −2.50u. Every conclusion
currently drawn from the sweep — including the risk.json floor-keeping
rationale — is computed over roughly half the disagreement rows, and the
excluded half is the better-performing one. The instrument gap is no
longer hypothetical; per-row hand arithmetic in deep retros is the same
manual-stats failure class score.py exists to prevent. Awaiting operator)

**Status update (deep-retro 2026-08-19): stays endorsed, but the evidence
basis shifts from edge to instrument.** Honest correction: the No-side
stream is no longer positive once correctly summed over all 20 realizable
rows — the 18:16Z 2026-08-18 retro updated the ledger totals (20 trades,
8W/12L, −5.42u) but carried the 17-trade side split forward unchanged, so
the "+0.92u, only positive stream" claim cited here and in DEEP-2026-08-18
was stale the moment the HD earnings (No, −1.00) and Musk weekly fork
(180-199 Yes −1.00, 220-239 No +0.16) rows settled. True split:
**Yes-side 1W/7L −5.50u; No-side 7W/5L +0.08u** — flat, not solidly
positive. That WEAKENS the edge motivation for this slice and the retro
says so plainly. But it is also the SECOND hand-arithmetic failure on this
exact quantity in two days (after the +0.17u→+0.92u correction of
2026-08-18 01:12Z), which is the strongest form of the instrument
argument: a machine-computed No-side slice cannot go stale. Endorsement
stands on that basis; the "excluded half is the better-performing one"
sentence above should now read "the excluded half is the flat one, vs a
clearly negative included half — still a materially different picture
than the sweep reports." Awaiting operator.

---

## 2026-08-14 — deep-retro status pass

- **2026-08-11 unshallow-before-divergence-judgment → actioned & confirmed**
  (status updated above: operator actioned 2026-08-13; first live deep-retro
  test today worked exactly as specified).
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  unchanged priority.** Third consecutive window with zero cost from the
  funnel-note workaround; no material revision occurred this window.
- New proposal above (No-side sweep slice). Everything else this window
  was implementable in strategy/ and is applied in this commit (taxonomy
  split, counterfactual correction, watch_items carrier in schedule.json,
  fat-tail and UK-GDP gradings).

---

## 2026-08-15 — deep-retro status pass

- **2026-08-14 No-side threshold-sweep slice (open): stays open, evidence
  UPDATED — honesty cuts both ways.** DEEP-2026-08-15 completed the veto
  counterfactual ledger (per-row fill arithmetic over all 11 settled
  outside-view-veto rows, playbook table): 5 of the 9 realizable
  disagreement counterfactuals were No-side trades the sweep cannot see —
  including BOTH wins (PPI 5.3% +0.15u, Musk 160-179 +0.61u) and three
  losses (Nordone, Flanagan, Musk 180-199). Corrected framing for this
  proposal: the No-side stream is 2W/3L, −1.24u — materially less bad than
  the Yes-side stream (0W/4L, −4.0u) but NOT positive; the earlier "both
  settled No-side rows went the agent's way" motivation (n=2, PPI-only) is
  superseded. The instrument ask is unchanged and still justified: the
  sweep currently counts only the Yes-side stream, so any conclusion drawn
  from it about "disagreement rows" covers roughly half of them. Awaiting
  operator.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  unchanged priority.** Fourth consecutive window with zero cost from the
  funnel-note workaround; no material revision occurred.
- **No new operator proposals.** Nothing this window was blocked on
  protected code. Informational, with a re-file condition: no routine
  ticks fired between 2026-08-14 10:33Z and 17:23Z (~6 missed hourly
  firings — scheduler/infra side, the agent's pacing file did not defer
  them). Single instance; if a second multi-hour tick gap appears, a
  proposal should cite both dates.

**Status:** informational (No-side sweep evidence updated in place above)

---

## 2026-08-16 — core/forecast.py: guard against inverted-outcome records

**Evidence:** `fe954ed9f325` (Canada GDP MoM "<0.0%", 2026-08-15 17:12Z
cycle). The agent intended "P(Yes)=0.11, matching the market's own 0.107"
but passed `--outcome "No"` with `--est-prob 0.11` — the immutable row now
asserts P(No)=0.11 ⇒ P(Yes)=0.89, a ~0.78 disagreement with the market in
the exact opposite direction of the researched belief. The hourly agent
caught and documented it same-cycle (playbook §operational trap
2026-08-15), and the deep retro has added a watch item excluding the row
from calibration claims at its ~Aug 28 settlement — but the row will still
pollute `by_skip_reason`/`by_category` machine slices forever, and the
failure mode (outcome string vs est_prob referent mismatch) is silent at
record time despite the tool printing everything needed to catch it.

**Proposed change:** `forecast.py record` computes
`|est_prob − market_prob_at_record|` for the named outcome and, when it
exceeds a threshold (0.50 catches only inversions; 0.40 adds margin),
refuses to record unless an explicit `--confirm-extreme` flag is passed.
Genuine extreme disagreements are rare and deliberate (the veto class), so
the flag costs one keystroke exactly when the agent should be pausing
anyway; inversion typos get caught at the only moment they are fixable.
Optionally also: a `voided` status core could stamp on operator request for
rows demonstrated to be recording errors, so machine slices stay clean —
weaker alternative to full revision support (2026-08-10 proposal), which
this complements but does not replace.

**Status:** endorsed by deep-retro (2026-08-17 — no new instance this window
(the recording discipline held), but the graded cost of the existing
instance is now booked: fe954ed9f325 will pollute machine slices at its
~Aug 28 settlement and every retro touching Canada GDP must carry a manual
exclusion forever. A one-flag guard at record time is cheap; the failure
mode is silent exactly when it happens. Awaiting operator)

---

## 2026-08-17 — deep-retro status pass

- **2026-08-14 No-side threshold-sweep slice (endorsed): stays endorsed,
  evidence updated a fourth time.** Japan GDP d684f9caff81 settled as
  another realizable No-side win (+0.85u at recorded bid): the No-side
  counterfactual stream is now 4W/3L **+1.17u** — the veto ledger's only
  positive stream and still invisible to the sweep. Every sweep-derived
  floor argument continues to reason over roughly half the disagreement
  rows, and the excluded half keeps winning. Awaiting operator.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed.**
  Sixth consecutive window at zero cost from the funnel-note workaround
  (no material revision occurred this window).
- **2026-08-16 inverted-outcome guard → endorsed today** (see updated
  Status above).
- No new operator asks. Nothing this window was blocked on protected code:
  the window's findings (carrier checklist, mechanical-econ fork,
  exploration prioritization) were all implementable in strategy/ and are
  applied in this commit.

---

## 2026-08-17 07:45Z — git push silently no-ops when HEAD is detached, unpushed history nearly lost

**Finding:** this cycle started with HEAD detached at `f929a5c`, 34 commits
ahead of the local `main` ref, which was itself equal to `origin/main`
(`ec3eebc`). This is superficially the "recurring container-image artifact"
every prior cycle log has logged and fixed (stale local `main`, detached
HEAD) — but in every one of those prior instances, `origin/main` already
matched the detached HEAD tip (push had succeeded; only the local branch
pointer was stale). This time it didn't: `origin/main` was ~8 hours and 34
commits behind HEAD. The likely mechanism: CYCLE.md step 9 runs
`git push origin main` unconditionally. When HEAD is detached, `git push
origin main` pushes the *local branch ref* `main` (unchanged, still at its
old commit) to the remote — it does NOT push the detached HEAD's commits,
and it prints success/no-op, not an error. So every cycle since whenever
this started was quietly failing to publish its work, while its own sync
step's "no divergence, no data loss" reasoning (comparing origin/main to
the *stale local main*, which matched) never caught it, because both sides
of that comparison were equally stale.

**Recovered this cycle**, no data lost: verified `origin/main` (`ec3eebc`)
was a strict ancestor of detached HEAD (`f929a5c`), then
`git branch -f main HEAD && git checkout main && git push` — a pure
fast-forward, not a rewrite. All 34 commits are now on `origin/main`.

**Risk:** the recovery worked only because the container happened to
persist across all those cycles. This environment's containers are
reclaimed after inactivity — had that happened mid-streak, everything
after `ec3eebc` (retros, playbook edits, forecasts, cycle logs) would have
been unrecoverable, since none of it ever reached the remote.

**Proposed change (loop.sh, operator-owned, not mine to edit):** before
running the cycle prompt, ensure HEAD is attached to `main` — e.g.
`git symbolic-ref -q HEAD >/dev/null || git checkout -B main HEAD` — so a
plain `git push origin main` always pushes what was actually committed.
Alternatively/additionally, CYCLE.md step 9 could `git rev-parse HEAD` and
`git rev-parse main` and refuse to treat the push as done unless they're
equal post-push, catching this class even if the detached-HEAD state
recurs for some other reason.

**Status:** endorsed by deep-retro (2026-08-18 — mechanism analysis
verified: with detached HEAD, `git push origin main` pushes the stale
branch ref and reports success, so the failure is silent by construction
and the cycle's own divergence check compares two equally stale refs.
The near-loss was 34 commits/~8h of the experiment's product, and the
recovery depended on container luck. Either half of the proposed fix —
the loop.sh HEAD-attach guard before the cycle, or a post-push
`rev-parse HEAD == rev-parse origin/main` verification in CYCLE.md step
9 — closes the data-loss window; both together are cheap. This is the
highest-priority operator ask on file. Note the pattern recurred
benignly on 2026-08-18 04:12Z — local main 3 days stale with HEAD
detached at origin's tip — so the trigger state is frequent even when
the push happens to have succeeded. Awaiting operator.)

---

## 2026-08-18 — deep-retro status pass

- **2026-08-17 07:45Z detached-HEAD push no-op → endorsed today** (see
  updated Status above): highest-priority operator ask on file.
- **2026-08-14 No-side threshold-sweep slice (endorsed): stays endorsed,
  evidence updated a fifth time.** No-side counterfactual stream now
  6W/4L **+0.92u** over 10 realizable rows (Oak Street and Spider-Man
  66-68m both No-side wins; Musk 2d <40 the No-side loss) — still the
  veto ledger's only positive stream, still invisible to the sweep. New
  supporting evidence for the instrument argument itself: the 01:12Z
  retro found the hand-carried No-side subtotal stale (+0.17u where the
  true row-sum was +0.92u) — the exact manual-arithmetic failure class
  a machine slice eliminates. Awaiting operator.
- **2026-08-16 forecast.py inverted-outcome guard (endorsed): stays
  endorsed.** No new instance across ~45 rows recorded this window; the
  booked cost of the existing instance (fe954ed9f325, manual exclusion
  forever) is unchanged. Awaiting operator.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  low urgency.** Seventh consecutive window at zero cost from the
  funnel-note workaround.
- No new operator asks from DEEP-2026-08-18: the window's findings
  (carrier-checklist compliance, funnel-line pool counts, four missing
  watch items) were all repairable in strategy/ and are applied in this
  commit.

---

## 2026-08-19 — deep-retro status pass

- **2026-08-17 07:45Z detached-HEAD push no-op (endorsed): stays endorsed,
  still the highest-priority operator ask on file.** Every container start
  this window again came up shallow with a detached HEAD (see the
  schedule.json reason fields, 2026-08-18/19); the hourly agent's manual
  `checkout -B main origin/main` recovery is holding, but the loop.sh
  guard remains unimplemented and the data-loss window remains open.
  Awaiting operator.
- **2026-08-14 No-side threshold-sweep slice (endorsed): stays endorsed
  with materially corrected evidence** — see the status update on the
  entry itself. Short version: the No-side stream is 7W/5L **+0.08u**
  (flat), not +0.92u; the stale figure was a second consecutive
  hand-arithmetic failure on this quantity, which is now the proposal's
  strongest argument. Awaiting operator.
- **2026-08-16 forecast.py inverted-outcome guard (endorsed): stays
  endorsed.** No new instance this window (~16 rows recorded); the booked
  cost (fe954ed9f325, manual exclusion at the ~Aug 28 Canada GDP
  settlement) is unchanged. Awaiting operator.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  low urgency.** Eighth consecutive window at zero cost from the
  funnel-note workaround.
- No new operator asks from DEEP-2026-08-19: the window's findings (stale
  side split, one carrier-checklist miss, a playbook-vs-funnel ruling
  placement gap) were all repairable in strategy/ and are applied in this
  commit.

---

## 2026-08-20 — deep-retro status pass

- **2026-08-17 07:45Z detached-HEAD push no-op (endorsed): stays endorsed,
  still the highest-priority operator ask on file — with one evidence
  CORRECTION.** The 2026-08-19 06:23Z cycle log claims it "recovered 50
  unpushed commits" spanning 2026-08-15T23:14Z–08-19T05:16Z. That
  magnitude is wrong and is struck from this proposal's evidence: two
  independent observations put origin/main far ahead of the claimed
  ec3eebc baseline at the time (DEEP-2026-08-19 fetched ~04:49Z and found
  origin/main ~88 ahead of it; the 05:16Z cycle's own log records
  "origin/main tip 9070888"), a remote cannot regress without a
  force-push, and `git rev-list ec3eebc..084ca12` is 90, not 50 — the
  number reconciles with nothing. Honest reading: the 05:16Z push (from a
  detached HEAD) likely did no-op, leaving at most ONE commit (084ca12)
  unpushed for ~1 hour; the 06:23Z container then judged the remote from
  a stale ref and misreported the recovery's size. What this correction
  gives back is stronger than what it removes: the trigger state recurs
  on essentially every container start, a real (small) no-op instance
  recurred, and the agent's in-cycle git self-diagnosis has now
  misjudged the remote's state twice in one morning — which is exactly
  why the guard belongs in loop.sh, BEFORE the agent runs, not in more
  in-cycle vigilance. Awaiting operator.
- **2026-08-14 No-side threshold-sweep slice (endorsed): stays endorsed**
  on the instrument argument (two documented hand-arithmetic failures on
  this exact quantity, 2026-08-18/19). No veto-class settlements this
  window; evidence unchanged.
- **2026-08-16 forecast.py inverted-outcome guard (endorsed): stays
  endorsed.** No new instance across ~15 rows recorded this window; the
  booked cost (fe954ed9f325, manual exclusion at the ~Aug 28 Canada GDP
  settlement) is unchanged and lands next week.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  low urgency.** Ninth consecutive window at zero cost from the
  funnel-note workaround.
- No new operator asks from DEEP-2026-08-20: the window's two findings
  (missing funnel line on the 18:20Z six-forecast batch; the 06:23Z log
  magnitude error) were repairable in strategy/ and journal/ — funnel
  weld rule added to the playbook, evidence corrected here.

---

## 2026-08-21 — deep-retro status pass

- **2026-08-17 07:45Z detached-HEAD push no-op (endorsed): stays endorsed,
  still the highest-priority operator ask on file, evidence STRENGTHENED
  with two new dated instances.** (i) 2026-08-20 20:15Z: HEAD sat at
  origin/main's tip so the cycle's equality check passed, but
  `refs/heads/main` was 136 commits behind — the cycle's work landed on
  detached HEAD and `git push origin main` was REJECTED ("pushed branch
  tip is behind its remote counterpart"), recovered in-cycle; the agent
  added a playbook guard (98324bf, `git branch -vv` +
  `merge-base --is-ancestor` before any reattach). (ii) 2026-08-20
  19:13Z: a tick judged the shallow-boundary fake divergence and ran
  `reset --hard origin/main` BEFORE unshallowing — verified safe only
  after the fact. In-cycle git self-diagnosis has now misjudged remote
  state three times in two days; the guard belongs in loop.sh, before
  the agent runs. Awaiting operator.
- **2026-08-14 No-side threshold-sweep slice (endorsed): stays endorsed**
  on the instrument argument; no veto-class settlements this window,
  evidence unchanged.
- **2026-08-16 forecast.py inverted-outcome guard (endorsed): stays
  endorsed.** No new instance (~13 rows this window); fe954ed9f325's
  manual-exclusion cost lands at the ~Aug 28 Canada GDP settlement —
  next week.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  low urgency.** Tenth consecutive window at zero cost from the
  funnel-note workaround.
- No new operator asks from DEEP-2026-08-21: the window's findings (two
  funnel-weld violations, clean-feed cap granularity loophole,
  brier_delta sign drift in three retros) were all repairable in
  strategy/ — reconcile.py tool, three backfilled funnel lines, and two
  playbook rules, applied in this commit.

---

## 2026-08-22 — deep-retro status pass

- **2026-08-17 07:45Z detached-HEAD push no-op (endorsed): stays endorsed,
  still the highest-priority operator ask on file.** The trigger state
  (shallow clone + detached HEAD + stale local main) recurred on
  essentially every container start this window (22:21Z, 23:24Z, 04:16Z
  cycle logs all record it); every recovery was clean via the 98324bf
  playbook guard (`merge-base --is-ancestor` before reattach), no new
  data-loss or misjudgment instance. The guard still belongs in loop.sh,
  before the agent runs — a per-cycle manual recovery that has failed
  three separate times historically is not a fix. Awaiting operator.
- **2026-08-14 No-side threshold-sweep slice (endorsed): stays endorsed,
  urgency DOWNGRADED — the edge motivation is dead.** The Aug14-21 Musk
  weekly legs settled 18:11Z and flipped the No-side counterfactual
  stream negative for the first time: 7W/6L, −0.92u over 13 realizable
  rows (deep-retro re-verified row-by-row today). The slice would now be
  instrumenting a net-negative stream on both sides (Yes 1W/8L −6.50u).
  The instrument argument (machine slice vs hand-summed subtotals; two
  documented hand-arithmetic failures) remains valid but is weakening:
  the last two hand-sums (18:15Z retro and today's independent
  verification) were both correct. Keep on file, rank below the git
  guard and the inverted-outcome guard. Awaiting operator.
- **2026-08-16 forecast.py inverted-outcome guard (endorsed): stays
  endorsed.** No new instance (~16 rows recorded this window);
  fe954ed9f325's manual-exclusion cost lands at the ~Aug 28 Canada GDP
  settlement — next week; the deep retros of Aug 28/29 must carry the
  exclusion when grading that cluster. Awaiting operator.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  low urgency.** Eleventh consecutive window at zero cost from the
  funnel-note workaround.
- No new operator asks from DEEP-2026-08-22: the window's findings (weld
  violation #6 with successful mechanical detection, weekly-cap
  gate-ordering slip, Musk generation classification, cross-market
  sensing gap) were all addressable in strategy/ — three playbook rules
  and one classification ruling, applied in this commit.

---

## 2026-08-23 — deep-retro status pass

- **2026-08-17 07:45Z detached-HEAD push no-op (endorsed): stays endorsed,
  still the highest-priority operator ask on file.** The trigger state
  recurred again on essentially every container start this window,
  including this deep-retro session itself (shallow clone, local main ref
  6 commits behind origin, HEAD detached at the true tip — resolved per
  the trigger-prompt guard, plain fast-forward). All recoveries clean via
  the 98324bf playbook guard; no new data-loss instance. A per-cycle
  manual recovery that has misfired three separate times historically is
  still not a fix; the guard belongs in loop.sh, before the agent runs.
  Awaiting operator.
- **2026-08-14 No-side threshold-sweep slice (endorsed, downgraded):
  unchanged.** No No-side settlements this window (the one veto-class
  settlement, TI VISION/Yandex, was Yes-side); both streams remain net
  negative (Yes 1W/9L −7.50u, No 7W/6L −0.92u). Instrument argument
  unchanged; rank below the git guard and the inverted-outcome guard.
  Awaiting operator.
- **2026-08-16 forecast.py inverted-outcome guard (endorsed): stays
  endorsed.** No new instance (~2 rows recorded this window, 27 settled);
  fe954ed9f325's manual-exclusion cost lands at the ~Aug 28 Canada GDP
  settlement — THIS COMING WEEK; the Aug 28/29 deep retros must carry the
  exclusion when grading that cluster. Awaiting operator.
- **2026-08-10 forecast.py revision support (endorsed): stays endorsed,
  low urgency.** Twelfth consecutive window at zero cost from the
  funnel-note workaround; no material revision occurred (Kazakh legs were
  correctly held as unchanged estimates rather than re-recorded).
- No new operator asks from DEEP-2026-08-23: the window's one finding
  (veto-ledger table left stale by the 13:14Z settlement retro) was
  repairable in strategy/ — table row added, totals re-summed, and a
  same-commit table-extension rule welded into the playbook and the
  schedule.json settlement-carrier comment, applied in this commit.

---

## 2026-08-24 — deep-retro status pass

- **2026-08-17 07:45Z detached-HEAD push no-op (endorsed): stays endorsed,
  still the highest-priority operator ask on file.** The trigger state
  recurred on essentially every container start this window (the cycle
  logs of 23:19Z, 00:15Z, 01:13Z and the 03:11Z bet cycle all record
  shallow starts and/or stale local main refs; this deep-retro session
  itself started shallow with local main 34 commits behind — clean
  unshallow, plain fast-forward, no divergence). All recoveries clean via
  the 98324bf playbook guard; no new data-loss instance. The guard still
  belongs in loop.sh, before the agent runs. Awaiting operator.
- **2026-08-10 forecast.py revision support (endorsed): urgency UPGRADED
  from low.** New fact: the book now holds its first long-horizon
  position (de95e5168de3, AfD Sachsen-Anhalt, settles Sep 6 — 13 days
  entry-to-settlement vs ~2 days for every prior bet). The entry estimate
  (0.29 Yes, from politpro's seat model) will meet two more weeks of
  polls and cannot be revised in the ledger; the funnel-note workaround
  covers forecast rows but not an open position's estimate. The staleness
  cost is no longer hypothetical — it is accruing on a live position.
  Awaiting operator.
- **2026-08-16 forecast.py inverted-outcome guard (endorsed): stays
  endorsed.** No new instance (~1 row recorded this window, 17 settled);
  fe954ed9f325's manual-exclusion cost lands at the ~Aug 28 Canada GDP
  settlement — THIS WEEK; the Aug 28/29 deep retros must carry the
  exclusion.
- **2026-08-14 No-side threshold-sweep slice (endorsed, downgraded):
  unchanged.** No veto-class settlements this window; both counterfactual
  streams remain net negative. Rank below the git guard, the revision
  support (upgraded above), and the inverted-outcome guard.
- No new operator asks from DEEP-2026-08-24: the window's one process
  finding (second pool_total funnel omission in two days) was repairable
  in strategy/ — reconcile.py check 3 welds it mechanically, offending
  line backfilled from the cycle log's own count, applied in this commit.

## 2026-08-25 04:16Z — screener subagent output format: 47% batch failure rate

First live run of the screener tier at full 15-batch scale (work_dir
`reports/screener-work/20260825T041433Z`). `subagent_prompt_template`
(core/screen.py, protected) is explicit: step 3 says "write a JSON array"
and gives the exact top-level-array shape. 7 of 15 haiku subagents
(batches 01, 02, 06, 10, 12, 13, 15) instead wrote `{"batch_id": ...,
"scores": [...]}` — a plausible-looking but non-conforming wrapper —
despite identical instructions to the 8 that complied. `screen.py collect`
correctly rejected all 140 markets in those batches (`screen_error: "no
answer for this market in the batch out file"`), so no bad data entered
`journal/screener.jsonl` — the failure was caught, not silent. But it cost
47% of this cycle's screening coverage (160/300 collected) on the tier's
first full-scale run, and I have no lever to fix it: I pass the literal
template per CYCLE.md step 4 ("nothing else"), and the template itself is
correct and unambiguous — this reads as a haiku instruction-following
failure rate on this exact task shape, not a wording gap I can patch from
strategy/screener-prompt.md (which never reaches the output-schema part
of the prompt). Not proposing a specific fix (a stronger schema
reminder, a retry-on-malformed pass in collect, or accepting the loss
rate) — flagging the evidence for the operator to weigh, since the fix
lives in core/screen.py or the subagent invocation, both outside what I
own. Re-check the failure rate on the next few full-scale runs before
treating 47% as stable; n=1 run so far.

**Status:** endorsed by deep-retro (2026-08-25 — endorsed with one factual
correction that changes the framing: this was NOT the tier's first
full-scale run. journal/screener.jsonl holds two 300-market/15-batch runs
on 2026-08-25 — 00:19Z run: 300/300 collected, 0 errors; 04:14Z run:
160/300, 140 lost across 7 malformed batches. Day-1 record is therefore
7/30 batches failed (23%), with per-run variance of 0%→47%, not a stable
47% — the failure is intermittent, which points at output-format
instability under identical prompts rather than a deterministic template
gap. The diagnosis is otherwise verified: the 140 error rows are all
`screen_error: "no answer for this market in the batch out file"`, nothing
malformed entered the pool, and the agent has no lever — the template
lives in protected core/screen.py. Recommended operator fix, cheapest
first: (1) make `screen.py collect` unwrap the one known-shape wrapper
`{"batch_id":..., "scores":[...]}` when the inner array validates — this
recovers the entire observed failure class for a few lines of tolerant
parsing and no re-spend; (2) failing that, a retry-once-on-malformed pass
in collect (costs quota); a stronger schema reminder in the template is
the weakest option since the 00:19Z run shows the current wording can
already achieve 15/15. Keep the agent's own duty as stated: report
collected/expected in every funnel line so the rate stays measured.)
→ **actioned** (operator, 2026-08-25 ~06:35Z — the endorsed cheapest fix
shipped: `screen.py collect` now unwraps the known wrapper shape, see
operator-notes.md. Verified closed by DEEP-2026-08-26: every 300-market
run since the fix collected 300/300 except a single 299/300 (one
malformed row, correctly reported in its funnel line) — cycles.log shows
eight clean-or-near-clean runs against the pre-fix 160/300. The failure
class is closed on current evidence; per the
operator's note, any NEW wrapper variant gets escalated the same way,
never absorbed by agent-side parsing.)

---

## 2026-08-25 — deep-retro status pass

- **2026-08-17 07:45Z detached-HEAD push no-op: ACTIONED (operator,
  2026-08-24, commit bf0e8be).** loop.sh now reattaches main to HEAD
  before each cycle; CYCLE.md step 9 reattaches before pushing and
  verifies HEAD == origin/main after. The highest-priority ask on file
  since Aug 17 is closed. This deep-retro session still started shallow
  with a stale local main (the container-image state persists) but the
  recovery path is now code on the loop.sh side and procedure in
  CYCLE.md — no further carry needed unless a new silent no-op instance
  appears.
- **2026-08-10 forecast.py revision support: ACTIONED (operator,
  2026-08-24, commit 6b29ccd).** `record --supersede` with linked rows
  and the `revised_away` score slice — exactly the endorsed shape,
  including the "measure whether revisions help" design note from the
  PLBY worked example. First expected use: the open AfD forecast
  (f37cee91366b) if polls move before ~Sep 4-5. Zero uses so far;
  revised_away slice empty (settled 0 / open 0) — correct, no material
  revision has occurred since it shipped.
- **2026-08-16 inverted-outcome guard: ACTIONED (operator, 2026-08-24,
  commit 0980816).** `|est_prob - mid| > 0.40` now refused without
  `--confirm-extreme`. The fe954ed9f325 manual exclusion at the ~Aug 28
  Canada GDP settlement is still required (rows are immutable); the
  watch item carries it.
- **2026-08-14 No-side threshold-sweep slice: ACTIONED (operator,
  2026-08-24, commit 877a133).** `threshold_sweep_no` live in score.py;
  first-run numbers already integrated into the playbook (c3492ce). The
  two documented hand-arithmetic failures this instrument prevents are
  now moot.
- **2026-08-25 04:16Z screener output format: endorsed above** (with the
  n=2-runs correction). This is the only open operator ask on file.
- No other new operator asks from DEEP-2026-08-25: the window's two
  process findings (census rows mislabeled `no-edge` — reconcile FAIL,
  fixed by relabel + playbook taxonomy addition; 04:13Z FULL cycle left
  next_full_cycle_after stale — pacing repaired, prose flag, weld only
  if repeated) were both repairable in strategy/, applied in this
  commit.

## 2026-08-25 — banned_question_patterns misses daily-resolution crypto "Up or Down" markets

**Evidence:** Today's 15-batch haiku screener run (20260825T101635Z) surfaced
two markets the screener prompt explicitly says should never reach it:
market_id 3809906 "Bitcoin Up or Down on August 25?" and 3809907 "Ethereum Up
or Down on August 25?" (strategy/screener-prompt.md's Housekeeping section:
"Sub-daily crypto up/down markets are banned upstream ... if one does, that
is a scan bug worth a line in the reason"). `config/protected.json`'s
`banned_question_patterns` is `["Up or Down - .*[0-9]:[0-9]{2}[AP]M-[0-9]",
"Up or Down.*ET$"]` — both regexes match the hourly-candle phrasing
("Up or Down - 3:00PM-4:00PM ET") but neither matches this daily phrasing
("<Asset> Up or Down on <Month> <Day>?"), so `core/scan.py`'s `keep()` lets
it through. This is the same single-token-resolution risk the existing
patterns were written to exclude (a coinflip-adjacent, reaction-speed
question, not a researchable one) — just a phrasing variant the regex
doesn't cover.

**Proposed change:** extend `banned_question_patterns` with a pattern
matching this daily crypto-direction phrasing, e.g.
`"Up or Down on [A-Z][a-z]+ [0-9]{1,2}\\??$"` (or scope it to known tickers,
`"^(Bitcoin|Ethereum) Up or Down on"`, if a broader match is judged too
aggressive) — `core/scan.py`/`config/protected.json` are protected, so I
cannot make this change myself.

**Status:** endorsed by deep-retro (2026-08-26 — verified: both existing
regexes target only the hourly-candle phrasings; "Bitcoin Up or Down on
August 25?" passes `keep()`. Same single-token-resolution/reaction-speed
class the existing patterns exclude, so the gap is an oversight, not a
policy choice. Of the two proposed regexes prefer the date-phrasing one
(`"Up or Down on [A-Z][a-z]+ [0-9]"`, unanchored) over the ticker list —
it also covers future non-BTC/ETH assets in the same daily template —
but either closes the observed gap.)

**Status update (operator, 2026-08-26): ACTIONED.** The endorsed
date-phrasing regex `"Up or Down on [A-Z][a-z]+ [0-9]"` is now the third
entry in `banned_question_patterns`. Verified against the two observed
market questions (3809906, 3809907) plus a non-BTC/ETH variant of the
same template; hourly-candle phrasings still match the original two
patterns, and non-crypto questions are unaffected. `core/validate.py`
passes.

## 2026-08-26 — watch.py new_market fired well under its own liquidity floor

**Evidence:** TRIGGERED cycle 01:22:26Z fired on `newmarket:3894452` ("HOU@NYY
O/U 12.5"). `strategy/watchlist.json`'s `new_market.min_liquidity` is 5000,
and `core/watch.py`'s `check_new_markets()` filters on gamma's
`liquidityNum` before firing — but when I fetched the same market's gamma
record moments later it read `"liquidityNum": 7.5597`, three orders of
magnitude under the floor. The market is a live in-game MLB total on a game
already in the bottom 7th (5-5, verified via MLB Stats API linescore) — the
CLOB book itself carries real depth (bid/ask sizes ~9000+ each side, spread
0.04), so the market is tradable; it's specifically gamma's `liquidityNum`
that doesn't reflect it. Two readings: (a) this field is transient/stale
right after a market's order book goes live (mine and watch.py's reads were
~20min apart, `enableOrderBook`+`orderMinSize` suggest a just-activated CLOB
market), so the floor check raced a field that hadn't populated yet; or (b)
`liquidityNum` measures something other than order-book depth for this
market type and never reflects it. Either way the floor is meant to keep
`new_market` from firing on thin/uninteresting listings, and it fired on
one anyway.

**Why this matters beyond one cycle:** the underlying market this happened
to surface was also a live in-progress sports game total — a repricing-race
shape my architecture can't research fast enough to trade (declined as
`architecture-mismatch`, forecast `8c7125bdfa3b`). If `liquidityNum` is
generally slow to populate right when a CLOB book activates, `new_market`
may be structurally biased toward firing on freshly-listed, still-live
sports markets specifically — the ones I'm least equipped to act on — while
its floor works as intended everywhere else. One instance isn't a pattern
yet; flagging so a second instance is recognized rather than treated as a
one-off.

**Proposed change:** `core/watch.py` is protected, so I cannot change the
liquidity source myself. Options for the operator to consider: check
`enableOrderBook`+CLOB book depth directly (already fetched via
`strategy/tools/quote.py`'s book endpoint) instead of, or in addition to,
gamma's `liquidityNum`; or add a short grace delay after `createdAt` before
trusting `liquidityNum` for freshly-listed markets.

**Status:** endorsed by deep-retro (2026-08-26 — consolidated with the
three later entries below: four fires in one session, two distinct
symptoms (this entry's liquidityNum underflow n=1; one-sided unfillable
post-listing books n=4), one shared root cause — gamma listing time is
not research-opportunity time for in-game sports totals. Cheapest fix
first: suppress or tag `new_market` fires whose gamma record carries a
`gameStartTime` already in the past (a field the watcher's fetch already
returns — no extra call, and it addresses the timing cause directly
where liquidity-source changes only address one symptom); the book-depth
liquidity check remains worth considering independently for the n=1
underflow. Until actioned the agent-side bleed is bounded: one narrow
gamma fetch + a correct decline per fire, capped at 6 fires/day.)

**Status update (operator, 2026-08-26): ACTIONED — the consolidated
`gameStartTime` suppression, covering this entry and the three below.**
`check_new_markets()` now skips any listing whose `gameStartTime` parses
and is already in the past at check time. Verified against live gamma
records for three of the four fired markets (3894452 start 23:05Z,
3894923 start 23:40Z, 3895121 start 01:40Z — all pre-fire), and that
non-sports markets carry no `gameStartTime` and are unaffected. A
missing or unparseable field fails open (the fire still happens), so
the guard cannot silently blind the trigger. The book-depth liquidity
check for the n=1 `liquidityNum` underflow is NOT included — it stays
open as a separate consideration if a post-fix instance recurs.

## 2026-08-26 — second `new_market` fire on an already-decided in-game total, this time with a one-sided empty book (not a liquidityNum miss)

**Evidence:** TRIGGERED cycle 01:52:53Z fired on `newmarket:3894923`
("TEX@CWS O/U 16.5", resolves Over at combined runs >=17). This time
`liquidityNum` was 10087.8 — well over the 5000 floor, so the prior entry's
specific liquidityNum-underflow bug did NOT repeat. What did repeat is the
broader shape flagged there ("flagging so a second instance is recognized"):
`new_market` fired on a market for a game already live in progress, past the
point where the outcome is researchable in the pre-game sense. Here it went
further — by the time I checked MLB Stats API's linescore (top 6th, 1-2
outs), combined runs were ALREADY 17, so Over was already mechanically
decided (runs are monotonic; barring a wipe-the-game cancellation, which the
market's own rules only invoke for full-game abandonment with no makeup,
this cannot revert). True P(Over)~0.99. But the CLOB book for the Over token
had ZERO asks (bids only, up to 0.61) — nothing to buy against — while the
Under token (the near-certain loser) had asks from 0.39. `core/ledger.py`
correctly rejects this (`no asks in the book`), and even if an ask appears
on Over once the book catches up, it will almost certainly clear
`config/protected.json`'s `max_entry_price` 0.95 (a mechanically-certain
outcome reasonably prices at ~0.98-1.00), so the cap would block it too.
Both instances now share one root cause candidate: `new_market` treats a
freshly-*listed* gamma market as equivalent to a freshly-*startable*
research opportunity, but for sports segment/total markets tied to a game
already underway, "freshly listed" can mean "freshly listed after the game
— or even the whole decision — has already happened," which is a different
and mostly untradeable animal (either raced or already-resolved-but-book-
lagging). The two symptoms differ (sub-floor liquidityNum vs a one-sided
book past the outcome's decision point) but the trigger-timing cause looks
shared.

**Proposed change:** still not mine to fix (`core/watch.py`,
`config/protected.json`). Beyond the prior entry's liquidity-source options,
this instance suggests a second, independent mitigation worth considering:
for `new_market` fires specifically, a quick live-game-state check (the kind
`core/odds.py scores` already does) before firing on anything tagged as a
live sports segment/total market — either suppressing the fire or tagging it
so the agent knows to expect a repricing-race/already-decided shape rather
than spending a narrow gamma fetch discovering that live. Two instances now;
recommend treating this as a real pattern rather than waiting for a third.

**Status:** endorsed by deep-retro (2026-08-26 — see the consolidated
endorsement on the first entry above; the `gameStartTime`-in-the-past
suppression covers this instance too, and would have caught 3894923
before the fire: the game was mechanically decided pre-listing.)

## 2026-08-26 — third `new_market` fire on already-live in-game totals (2 games, 3 markets, one cycle)

**Evidence:** TRIGGERED cycle 02:23Z fired on `newmarket:3895012`,
`newmarket:3895006`, `newmarket:3895005` together — CLE@LAA O/U 10.5 and O/U
9.5 (bottom 2nd, 4-0, ~45min post-commence) and TEX@CWS O/U 20.5 (bottom
7th, 11-7=18 combined runs). Same shape as the two prior entries above: all
three markets were listed after their games were already underway, not
pre-game. This time `core/forecast.py`'s own CLOB book read makes the
untradeable part concrete rather than inferred: all three books were wide
and one-sided (3895012 bid=0.19/ask=0.99, 3895006 bid=0.14/ask=0.98,
3895005 bid=0.43/ask=0.94) — asks near 1.0 regardless of which side a quick
pace-extrapolation model favored, so even where a real edge might exist
(e.g. TEX@CWS: ~3 more runs needed over ~2.5 remaining half-innings at an
already-elevated scoring pace, est ~0.60 Over vs a stale-looking 0.29
last-trade price) the actual fillable ask (0.98) makes the trade a clear
loser. Third instance in one session; the pattern (in-game listing timing)
and now also its practical consequence (unfillable/mispriced book on the
side any live-state model would favor) look confirmed rather than
coincidental.

**Proposed change:** unchanged from the prior two entries — still not mine
to fix (`core/watch.py`, `config/protected.json`). Given three instances
now share both the timing cause and the same book-unfillability symptom,
recommend treating `new_market` fires tagged as sports segment/total
markets as a distinct category the agent should triage with a live-game-state
check before spending any research budget, rather than continuing to
rediscover the same shape live each time. Marking this the confirming third
instance per the prior entry's own recommendation.

**Status:** endorsed by deep-retro (2026-08-26 — see the consolidated
endorsement on the first entry; pattern-confirming third instance, and
the 04:16Z retro's settlement grading adds that the pace model behind
these fires is 2W/2L on the model side — no skill being left on the
table by suppressing them.)

## 2026-08-26 — fourth `new_market` fire on an already-live in-game total (same session)

**Evidence:** TRIGGERED cycle 02:41Z fired on `newmarket:3895121` (PIT@SD
O/U 4.5), listed after the game was already in the bottom of the 4th
(1 out, 0-0, MLB Stats API gamePk 823259) — same timing shape as the prior
three entries. Book-unfillability symptom repeats too: Over bid/ask
0.34/0.99, Under bid/ask 0.07/0.99, both asks pinned near 1.0 regardless of
which side the pace-extrapolation model favored (est 0.59 Over). Fourth
instance in one session (after 3894452, 3894923, and the 3895012/3895006/
3895005 triple) — adding this purely as a running tally; the pattern and
its consequence are already fully evidenced by the prior three entries and
this changes no conclusion, just the count.

**Status:** endorsed by deep-retro (2026-08-26 — running-tally entry,
folded into the consolidated endorsement on the first 2026-08-26 entry;
no separate ask.)

## 2026-08-26 — deep-retro status pass

**Evidence/summary:** six statuses moved this pass. The 2026-08-25
screener output-format proposal is closed as actioned (operator shipped
the tolerant unwrap ~06:35Z; eight subsequent runs verify the failure
class closed — 300/300 on all but one 299/300). The daily crypto
Up/Down `banned_question_patterns` gap is endorsed (verified against the
config regexes; date-phrasing variant preferred). The four `new_market`
in-game-fire entries are endorsed as ONE consolidated pattern with a
concrete cheapest fix: suppress or tag fires whose gamma
`gameStartTime` is already in the past — it addresses the shared timing
cause, would have pre-empted all four fires including the
mechanically-decided 3894923, and costs no extra API call. No new
operator asks from DEEP-2026-08-26: the window's other findings (pacing
weld → reconcile.py check 4; fact-final/info-race ledger taxonomy
split; GTA VI liquid-book grading fork) are all agent-side and applied
in the same commit.

**Status:** informational (open operator asks after this pass: the
crypto-pattern extension and the consolidated new_market fix, both
endorsed above)

## 2026-08-27 — deep-retro status pass

**Evidence/summary:** both operator asks left open by the 2026-08-26 pass
were actioned by the operator the same day and are verified closed here:
the daily crypto Up/Down `banned_question_patterns` extension (commit
0db77ca, regex verified present in config and matching the observed
3809906/3809907 phrasings) and the consolidated `new_market` in-game-fire
suppression (commit 0a13990, watch.py now skips listings whose gamma
gameStartTime is past at check time; zero in-game fires in the subsequent
window vs four the day before). No new operator asks from DEEP-2026-08-27:
the window's findings are all agent-side and applied in the same commit —
reconcile.py checks 5 (veto-settlement table duty; three prose-rule misses
on 2026-08-26 alone) and 6 (FULL-cycle funnel-line presence; the 09:24Z
line-less FULL masked its own 99-minute pacing breach), the six missing
counterfactual-table rows (Crowley, PCE MoM x3, BoK pair), and the
mechanical-econ fork tally. NOTE the fork decision lands tomorrow
(DEEP-2026-08-28/29, pre-registered): if the condition holds after Canada
GDP settles, THAT retro files an operator-visible carve-out proposal
touching real-eligibility taxonomy — flagging it a day ahead so it is not
a surprise ask.

**Status:** informational (open operator asks after this pass: none)

## 2026-08-28 ~07:15Z: real-mode session cannot push, and cannot repair branch refs (operator action needed)

Evidence, this session (operator-machine REAL-mode FULL cycle, 06:35-07:15Z):

- `git push origin main` / `git push origin HEAD:main` hung until timeout 3x
  (2-3 min each, exit 143). `git fetch` is instant, so the network is fine;
  the hang pattern matches a credential-helper prompt that a non-interactive
  session cannot answer (SSH URL fails fast with no key, so the HTTPS helper
  is the only auth path).
- Every workaround was permission-blocked in this session: env-prefixed
  `GIT_TERMINAL_PROMPT=0 git push`, `git -c credential.helper= push`,
  `git config` (even reads), `gh auth status`.
- Separately, after resolving the 06:41Z-vs-06:55Z parallel-cycle rebase, every
  ref-moving command was permission-blocked (`git rebase --continue` (editor),
  `git rebase --quit`, `git checkout`/`switch`/`branch -f`/`update-ref`), so the
  merged commit had to be created on a DETACHED HEAD and local `main` is stuck
  on the pre-rebase orphan.

State the operator must repair (see cycle log line 2026-08-28T06:55:00Z):

- The TRUE merged state is the detached-HEAD commit chain ending at the commit
  containing this proposal (parent 0ac4b09, grandparent 6b16795 = origin/main).
- Local `main` (0607fe3) is the pre-rebase orphan; its content is fully
  contained in 0ac4b09. Fix: `git checkout -B main <tip of detached chain>`
  then `git push origin main`.

Proposals:
1. Ensure the real-mode agent can push non-interactively (cached credential or
   a helper that never prompts), or have loop.sh do the push after the agent
   exits.
2. Allowlist the minimal git ref plumbing the CYCLE.md procedure itself
   requires (`checkout -B main`, `rebase --continue/--quit`), since step 0 and
   step 9 mandate exactly those commands and this session could not run them.
3. The 06:41Z/06:55Z collision shows true simultaneity beats the 20-minute
   collision guard (both runners started ~06:35Z). One instance; if it recurs,
   consider a lock or start-jitter. Logged here per the "causes get fixed in
   proposals" rule.

**Status:** actioned (operator, 2026-08-29)

1. **Push moved off the agent.** `loop.sh` now pushes after the cycle exits,
   from the operator's interactive shell where the keychain is already
   unlocked. Root cause confirmed: the credential helper is
   `!gh auth git-credential`, which reads the token from the macOS keyring;
   a keyring prompt cannot be answered inside `claude -p`, so the push hung
   while `fetch` (no credential needed on a public repo) stayed instant.
   `CYCLE.md` step 9 now stops before the push when `PHIL_PUSH_BY_LOOP` is
   set, so an unpushed commit on this machine is expected rather than a
   discrepancy to diagnose. Cloud runs are unchanged and still push
   themselves.
2. **Ref plumbing allowlisted.** `loop.sh` adds `git checkout -B main HEAD`,
   `git rebase --continue/--abort/--quit`, and the read-only
   `status`/`symbolic-ref`/`merge-base`/`rev-list` probes. The agent also
   runs with `GIT_EDITOR=true` so `rebase --continue` cannot block on an
   editor, and `GIT_TERMINAL_PROMPT=0` + `GIT_ASKPASS=/usr/bin/true` so any
   stray credential lookup fails fast instead of hanging.
   `Bash(git push:*)` was removed: the runner owns the push now.
3. **Collision guard** left as-is, per the proposal's own read that one
   instance does not justify a lock. Still open if it recurs.

## 2026-08-28 — deep-retro status pass (recovered session)

Read every proposal above. No open hourly-agent proposals required a
status decision this pass: the 2026-08-28 ~07:15Z push/ref-plumbing item
was actioned by the operator (2026-08-29, loop.sh owns the push, plumbing
allowlisted) — acknowledged, nothing to add; the collision-guard sub-item
stays open on its own recurrence condition. All older items carry their
existing statuses.

New, from DEEP-2026-08-28:

1. **Operator ask — .gitignore entries for cycle working files.** FULL
   cycles have been committing per-run scratch at repo root:
   `scan-stderr.txt`, `scan.stderr`, `screen-prepare.json`,
   `screen.stderr`, `subagent-template.txt` (see 0d5d51a, 0ac4b09,
   ca570d1). Deleted from the tree in the DEEP-2026-08-28 commit, but
   they will recur on the next FULL cycle unless ignored. Ask: add to
   .gitignore (operator-owned): `scan-stderr.txt`, `scan.stderr`,
   `screen-prepare.json`, `screen_prepare.json`, `screen.stderr`,
   `subagent-template.txt`, `reports/` — or, better, a `work/` prefix
   convention the cycle procedure can be pointed at later.

2. **Informational — blend re-open condition tracking.** score.py
   blend[disagreement]: w_opt 0.622, delta −0.0058, n=70. The operator's
   2026-08-25 re-open bar is n≥100 with w_opt≤0.9: the weight condition
   now clears with room, the n condition is 70/100. No ask yet; if the
   slice reaches n≥100 with w_opt still ≤0.9, that firing is the
   operator-visible re-raise the 08-25 note pre-authorized.

3. **Informational — mechanical-econ carve-out enacted** (agent-owned
   change, flagged here for operator visibility per the DEEP-2026-08-17
   pre-registration): playbook §Mechanical-econ carve-out, band
   0.10–0.20, named-reachable-benchmark gate, one bet per print,
   pre-registered kill switch (4 events / 6 bets, net≤0 or dBrier
   non-majority → full revert). Evidence and the UMich exclusion
   reasoning in DEEP-2026-08-28.md.

**Status:** informational (open operator asks after this pass: the
.gitignore entries, item 1)

## 2026-08-29 — deep-retro status pass

Read every proposal above. No new hourly-agent proposals since the last
pass; all prior statuses stand. Updates:

- **.gitignore ask (2026-08-28 item 1): still open.** No scratch files
  recurred at root this window (the cleanup held behaviorally), but the
  ignore entries remain the durable fix.
- **Blend re-open tracking (2026-08-28 item 2):** blend[disagreement]
  n=71, w_opt 0.636, delta −0.0053. One new row since yesterday; w_opt
  wiggled 0.622→0.636 (noise). n bar 71/100 — no ask, tracking continues.
- **Mechanical-econ carve-out:** zero qualifying events yet. The
  DEEP-2026-08-29 gate-2 variance clause (playbook) narrows eligibility
  ahead of the Sep 1–5 econ cluster: dispersion must be sourced like the
  mean, so the NFP set stays forecast-only unless a quoted consensus-miss
  spread is found at re-check. Agent-owned change, informational only.

**Status:** informational (open operator asks after this pass: the
.gitignore entries, unchanged)

## 2026-08-30 14:12Z — new market-construction quirk: title window ≠ resolution window on late-created touch markets

Screener escalated 3954519 "Will Bitcoin reach $80,000 August 24-30?"
(forecast 9618a7d0872d). Gamma's own slug is
`will-bitcoin-reach-80k-august-24-30-2026-from-august-28` and the
description states price action *before market creation* does not count
— this instance was created 2026-08-28T16:57Z, three days after the
title's stated window start, so the actual eligible window is
creation→endDate, not the displayed Aug24-30. This is the same species
of bug as the already-logged BoI Aug31/Sep1 rescheduled-meeting pair
(schedule.json watch items) but on a *templated recurring series*
(crypto touch-anytime brackets) rather than a one-off reschedule —
worth checking whether other touch-anytime series legs (gas, WTI, gold)
ever get re-created mid-window the same way, since a stale `startDate`
read there would silently overstate touch probability the same way it
nearly did here. No config/core change requested — this is a read-the-
description-not-just-the-title discipline note for my own research step,
now written up so it isn't re-discovered from scratch next time.

**Status:** informational, agent-owned discipline note (no operator
action needed)

## 2026-08-30 — deep-retro status pass

Read every proposal above. No new hourly-agent proposals since the
2026-08-29 pass; all prior statuses stand. Updates:

- **.gitignore ask (2026-08-28 item 1): still open.** No scratch-file
  recurrence this window either; the ignore entries remain the durable fix.
- **Blend re-open tracking:** blend[disagreement] n=73, w_opt 0.651,
  delta −0.0048. w_opt is under the operator's 0.9 bar for a second
  consecutive day, but n is 73/100 — no ask yet, tracking continues.
- **Real-mode push fix (operator-actioned 2026-08-29): observed working.**
  Real-ledger settle sweeps record cleanly (DepositWallet empty, nothing
  to sweep); no further operator action needed.
- **Context for the operator, no action asked:** both Lake America No
  legs (bbe450e04eb9 $5 @0.668, 6f7dfb5b7c0c $5 @0.38) marked ~0.001
  after all five rename-deadline markets converged to ~0.998 Yes on
  2026-08-30 03:52Z; with GTA VI (c6f16acc55d9, mid 0.017) that is ~$15
  of the $20 open effectively dead, settling Sep 1–4. The fix is
  agent-owned and enacted (playbook fact-finality gate, DEEP-2026-08-30):
  claimed edge > 0.10 now requires an already-immutable fact or a live
  cross-market inconsistency — documented-but-unfinished processes no
  longer qualify. No config/ or core/ change needed.

**Status:** informational (open operator asks after this pass: the
.gitignore entries, unchanged)

## 2026-08-31 — deep-retro status pass

Read every proposal above. One new hourly-agent item since the 2026-08-30
pass:

- **2026-08-30 14:12Z title-window ≠ resolution-window quirk: ENDORSED,
  and now evidence-backed at n=1.** The very market that surfaced the
  quirk (3954519, BTC touch-$80k "Aug 24-30" actually created Aug 28)
  settled No on 2026-08-31: the window-corrected read (est No 0.88 vs mid
  0.80, forecast 9618a7d0872d) WON, and the naive title-window read would
  have been badly wrong (BTC touched $81k inside the *title* window but
  before creation). Status stays informational/agent-owned; the
  read-the-description discipline is confirmed useful, not just
  theoretical.

Tracking updates:

- **Blend re-open tracking:** blend[disagreement] n=78, w_opt 0.720,
  delta −0.0032 (score.py this run). Third consecutive pass with w_opt
  under the operator's 0.9 bar; n now 78 of the required 100. No ask yet —
  at the current settlement rate the n≥100 gate is roughly a week out;
  the ask should be filed by the deep retro that first sees n≥100 with
  w_opt still ≤0.9.
- **.gitignore ask (2026-08-28): still open**, still the only outstanding
  operator ask. No scratch-file recurrence this window.
- **No new operator asks from this pass.** The window's two defects
  (spread-trap escalation waste, and the two veto rows my own resolve run
  settled) were both agent-owned and fixed in this commit
  (strategy/screener-prompt.md hard rule; playbook counterfactual-ledger
  extension).

**Status:** informational (open operator asks after this pass: the
.gitignore entries, unchanged)

## 2026-09-01 — deep-retro status pass

Read every proposal above. No new hourly-agent proposals since the
2026-08-31 pass.

- **.gitignore ask (2026-08-28): ACTIONED by the operator** (commit
  0d760c1, operator-notes 2026-08-31 ~21:30Z). Scratch filenames ignored
  plus a `work/` directory convention for per-run working files; the
  operator asked that this be marked actioned on this pass — done. The
  cycle-procedure pointer at `work/` is agent-owned and can land whenever
  the relevant playbook/CYCLE-adjacent steps are next touched (CYCLE.md
  itself is operator-owned; the agent's own file references are not).

Tracking updates:

- **Blend re-open tracking:** blend[disagreement] n=90, w_opt 0.70,
  delta −0.0044 (score.py this run). Fourth consecutive pass with w_opt
  under the operator's 0.9 bar; n now 90 of the required 100. No ask yet
  — at the current settlement rate the n≥100 gate is 1-2 passes out; the
  ask files the first pass that sees n≥100 with w_opt still ≤0.9.
- **2026-08-30 title-window quirk note:** unchanged, endorsed at n=1;
  no new instances this window.

**No new operator asks from this pass.** The window's two defects were
agent-owned and fixed same-day by the hourly agent (position-monitoring
sign-check rule, RETRO-20260831-1619) or closed by this retro (touch-
family gate ruling; screener spread-trap fix regraded effective 63%→22%).

**Status:** informational (open operator asks after this pass: NONE —
first pass with a clean slate since 2026-08-28)

## 2026-09-02 — deep-retro status pass

No new proposals from the hourly agent this window (2026-09-01 04:46Z →
2026-09-02 04:21Z). No open operator asks carried in. One tracked
condition fired and is reported here as promised:

**Blend re-open gate: FIRED ON THE LETTER, recommendation is DO NOT
ADOPT.** The operator's 2026-08-25 condition ("think n ≥ 100 and w_opt
≤ 0.9 on the disagreement slice") is now met numerically: n=111 settled
disagreement rows, w_opt=0.892. But the material half of the condition
("w_opt drops materially below 1.0") is not: the improvement at w_opt is
−0.0005 brier vs the market (brier 0.1427 vs 0.1432), and the trajectory
as n grew is the tell — w_opt 0.622 at n=70 → 0.70 at n=90 → 0.892 at
n=111, i.e. the apparent below-market optimum is converging TOWARD the
market as the sample fills in, the signature of a small-sample artifact,
not a stable blending edge. A 0.0005 brier improvement would also never
survive fill costs as a trading rule. Status: gate condition formally
discharged (this is the ask the DEEP-2026-09-01 pass promised to file at
n≥100); recommendation is no adoption and no build. score.py prints the
sweep every run for free, so passive tracking continues; suggested
re-raise bar if the operator wants one kept on file: w_opt ≤ 0.80
sustained at n ≥ 150.

Status: REPORTED — operator may close the 2026-08-25 blend re-open
condition as resolved-negative, or set the new bar above.

Housekeeping noted for the record (agent-side, already fixed, no operator
action): the 2026-09-01 08:19Z LIGHT tick deferred grading of 2 settled
forecasts on a "carrier rule is ledger-only" reading that contradicts
schedule.json's own "settles ANYTHING" wording; both rows were routine
market-agrees/no-edge wins (Iran blackout daa8218bb25d, JPM $1T
38e50222e784), graded 19h late in DEEP-2026-09-02, and the rule wording
is now explicit that forecast-only settlements carry the same duty.

## 2026-09-03 — deep-retro status pass

No new proposals from the hourly agent this window (2026-09-02 04:48Z →
2026-09-03 04:21Z). Actions on tracked items:

- **Blend re-open condition (operator, 2026-08-25): RESOLVED-NEGATIVE —
  closed.** Per the operator's 2026-09-03 ~00:20Z note, the 2026-08-25
  condition is closed as a small-sample artifact (fired on the letter at
  n=111/w_opt 0.892, improvement −0.0005 brier, trajectory converging
  toward the market). The replacement bar on file: w_opt ≤ 0.80 at
  n ≥ 150, sustained across two consecutive deep-retro passes both at
  n ≥ 150, with improvement at w_opt ≥ 0.002 brier vs market. No
  calibrate.py, no blend rule until then.
- **Blend tracking line (this run's score.py):** blend[disagreement]
  n=114, w_opt 0.915, delta −0.0003. Moving away from the new bar, as
  the operator's trajectory read predicted.
- **gnhf forward test (operator, pre-registered 2026-09-02): acknowledged,
  hands off.** strategy/policy.py v3 is the object under test
  (`core/replay.py --after 2026-09-02T00:14:36Z`, ≥15 forward bets,
  criteria mechanical, daily CI trigger). This retro audited but did not
  touch it; nothing from its in-sample replay scores was adopted into
  risk.json or the playbook. The one crossover noted for the record: its
  longshot-bias finding agrees with the bet ledger's own calibration
  (all 6 settled bets with est <0.5 lost) and with the standing
  sub-0.10-price rule — convergent evidence, not yet adoption evidence.

**No new operator asks from this pass.** Open operator asks after this
pass: NONE.

**Status:** informational

## 2026-09-04 00:40Z — collision-guard gap: two concurrent FULL cycles both bet the same leg

**Structural finding, not a request to work around a protected rule.**
Two FULL cycles ran essentially simultaneously starting ~00:16-00:26Z: a
cloud cycle (this one) and an operator-machine real-mode cycle. Both
started from the same tip (`e3d2cb7`, an `operator:` commit, not a
`cycle:`/`cycle(triggered):` commit), so CYCLE.md step 0's collision
guard — which only checks whether the tip is a recent cycle commit — did
not fire for either. Both independently scanned, screened, researched
the August 2026 NFP bracket set via the mechanical-econ carve-out
(different sourcing details, same conclusion), and placed a $5 bet on
the identical leg (market 3403942, "add 0-50k", No side, ~$0.67 entry).
The operator-machine cycle's push (via `loop.sh`) landed on origin/main
first; this cycle's `git push` was rejected, and the follow-up
`git pull --rebase` hit a genuine conflict on `journal/ledger.jsonl`
(two distinct valid rows for the same market+outcome) — aborted per
CYCLE.md step 9's explicit rule rather than hand-resolved. This cycle
reset to the already-pushed state and declined to place a second bet on
the same leg (see the `declined` entry in `strategy/funnel.jsonl` for
this cycle, `2026-09-04T00:16:34Z`).

No capital-safety issue: two $5 bets on the same leg would have summed
to exactly `max_stake_per_event_usd` (10.0), not over it, and the second
bet was never actually placed. The real cost was research/compute
duplication (two independent 15-batch haiku screening runs, two
independent NFP research passes) and a `journal/screener-quota.json`
lost-update race (both cycles read the day's usage as 0 and wrote 15;
corrected by hand this cycle to 30/600 to reflect both runs — the
formula itself is fine, the race is in reading-then-writing without a
lock, same shape as the ledger collision).

**What I'm flagging, not fixing:** the collision guard's definition of
"another runner just cycled" (tip is a `cycle:`/`cycle(triggered):`
commit < 20min old) misses the case where the tip is a non-cycle commit
(an `operator:` commit here) but another FULL cycle is *concurrently in
flight* from that same tip. A guard keyed only on the committed tip
can't see a concurrent uncommitted run by construction — this may need
something outside what a single agent invocation can enforce (a lock
file, a shorter polling/backoff window, or accepting occasional
duplicate bets as a bounded cost given the $10/event cap already bounds
the downside). Leaving the mechanism design to the operator; recording
the evidence per CYCLE.md's "a structural oddity in my inputs is a
proposal, not a shrug."

**Status:** ENDORSED (DEEP-2026-09-04) — see the 2026-09-04 deep-retro
status pass below for the remedy sketch; operator decision pending.
`core/screen_rank.py`, `journal/screener-rank-decision.md`
and `strategy/screener-filters.json` also landed in the operator-machine
cycle's commit (`d9158ee`, message prefix `cycle:` not `operator:`) --
these read as operator-authored (the file's own docstring says "PROTECTED
CORE" and references `journal/operator-notes.md`), most likely picked up
by that cycle's `git add -A` from files staged in the working directory
rather than written by the agent. Not reverted (reverting real operator
work would be its own mistake) and not this cycle's call to make either
way -- flagged for visibility since it crossed the boundary-guard's
commit-prefix convention.

**CI confirmation (00:41Z):** `core/ci.py` now reports `d9158ee` failing
the `Agent/operator boundary` check, confirming the cause diagnosed
above (core/screen_rank.py etc. landing in a non-`operator:`-prefixed
commit). Per CYCLE.md step 0c, the cause lives in a protected path
(`core/`), so the required action is documenting it here rather than
attempting a fix — already done above before this confirmation arrived.
No agent-side fix applies: the boundary guard is protected-path CI, and
correcting it (re-committing those files under an `operator:` prefix, or
`loop.sh`'s revert-on-protected-change logic) is the operator's/loop.sh's
move, not mine to make.

## 2026-09-04 — operator-machine and cloud histories have diverged for three ticks; loop.sh cannot push

**Symptom (hourly agent, 01:29Z, 02:33Z, 03:53Z ticks on the operator
machine, real mode):** `git fetch origin main` succeeds, but local `main`
and `origin/main` are genuinely diverged. Local carries the operator
commit 099039f (gnhf 3) plus the 00:26Z, 01:29Z, 02:33Z and 03:53Z cycle
and retro commits; origin carries the cloud commits 0664b36 (cycle
00:38Z), 6a23fd0 (chore) and 7ea4781 (cycle 02:14Z). Per CYCLE.md step 0
the agent continued on local state each time and never reset, which is
the correct rule, but nothing publishes: `PHIL_PUSH_BY_LOOP=1` hands the
push to `loop.sh`, whose non-fast-forward path is `git pull --rebase`
then push, and the rebase cannot apply because both sides appended to
`journal/cycles.log`, both sides rewrote `strategy/schedule.json`, and
both sides settled different rows in `journal/forecasts.jsonl` (the cloud
02:14Z tick settled the Sakkari row; the operator 02:33Z tick settled it
again locally, then this tick settled five GTA VI rows). loop.sh aborts
the rebase and warns; the next tick starts from the same diverged state.

**Cause:** two runners cycling on the same hours. The step-0 collision
guard only demotes a tick that lands within 20 minutes of the other
runner's commit; it does not handle sustained parallel runners whose
pushes interleave. The cloud routine kept cycling while `./loop.sh
--real` was running on the operator machine, and the first rejected push
made every later local commit unpushable.

**What the agent cannot do:** resolve the conflicts. `forecasts.jsonl`
and `ledger.jsonl` are core-written; hand-merging them is forbidden.
`loop.sh` and CYCLE.md are operator-owned.

**Asks (operator):**
1. Reconcile once by hand: merge origin's three commits into local main
   keeping BOTH sides' journal rows (cycles.log and funnel.jsonl are
   append-only, union them; schedule.json take the newer reason and the
   union of watch-item checkpoints; forecasts.jsonl needs both sides'
   settlement fields, then `python3 core/resolve.py` to re-settle
   idempotently), then push.
2. Prevent the recurrence structurally: pause the cloud routine while the
   operator loop runs (or have loop.sh pause it), and consider a
   `.gitattributes` `merge=union` driver for the append-only journal
   files (`journal/cycles.log`, `strategy/funnel.jsonl`,
   `journal/screener.jsonl`, `journal/mech-requests.jsonl`) so an
   interleaved push only ever conflicts on files that carry state.

**Status:** OPEN operator ask. Until reconciled, every operator-machine
cycle's work (including RETRO-20260904-0340's counterfactual-table
extension and four forecast rows) exists only locally.

## 2026-09-04 — deep-retro status pass

Audit window 2026-09-03 04:30Z → 2026-09-04 04:30Z. Full analysis in
journal/retros/DEEP-2026-09-04.md.

**Collision-guard gap (hourly agent, 2026-09-04 00:40Z): ENDORSED.**
The finding is correct and well-evidenced: a tip-commit-based guard
cannot see a concurrent in-flight run by construction, and the same
read-modify-write race independently hit journal/ledger.jsonl (push
conflict) and journal/screener-quota.json (lost update, 15 vs 30).
The agent's handling was exemplary — declined the duplicate bet,
aborted the conflicted rebase per rule, hand-corrected the quota with
an audit note. Remedy sketch, both halves operator-owned (loop.sh /
core/): (1) a lock file or lease pushed as a lightweight ref at cycle
start, honored by both runners; or (2) accept duplicate bets as a
bounded cost (the $10/event protected cap held here by exactly $0) and
fix only the quota race, which unlike the ledger has no conflict
detection at all. Recommend at minimum half (2): the quota race is
silent and cumulative; the ledger race at least fails loudly at push.
Status: OPEN — operator ask.

**NEW operator ask — cure the d9158ee boundary breach.** Commit
d9158ee (`cycle:` prefix) carries core/screen_rank.py,
journal/screener-rank-decision.md and strategy/screener-filters.json —
operator gnhf-run-3 artifacts swept from the working tree by the
cycle's `git add -A`. CI's boundary guard correctly fails it, and every
subsequent push inherits a red history check until it is blessed or
re-attributed. Only the operator can cure this (re-commit under
`operator:`, amend the guard's allowlist for that sha, or whatever
loop.sh's revert logic prescribes); no agent-side fix is legal. The
agent-side halves are done: files audited (screener-filters.json is
dormant, nothing live reads it), nothing reverted, provenance
documented. Status: OPEN — operator ask.

**Tracked conditions (one-liners, per standing instructions):**
- Blend: blend[disagreement] n=122, w_opt=0.837, delta −0.0012 — bar
  (≤0.80 at n≥150, delta ≥0.002, sustained ×2) not met, drifting away.
- Screener replay: 18,047 rows scored; live rev f7ddad12 excess
  +0.0033, z +2.1 — unchanged from operator's gnhf run 2 note;
  screener-prompt.md untouched per freeze.
- gnhf policy v3 forward test: 34 forward rows, 3 bets, pnl +2.71,
  brier_delta −0.0114 — under the ≥15-bet bar, insufficient data,
  hands off.

Open operator asks after this pass: **2** (collision-guard mechanism,
d9158ee boundary cure).

## 2026-09-04 08:xxZ — `core/screen.py collect` exits 1 on its own summary line after the per-runner quota change (hourly agent)

**Symptom (this cycle, operator machine, work dir
`reports/screener-work/20260904T080505Z`):** `python3 core/screen.py
collect --dir ...` validated all 15 out files, appended 300 rows to
`journal/screener.jsonl`, wrote the `collected` marker and printed the
top-15 rows on stdout, then crashed:

```
File "core/screen.py", line 902, in cmd_collect
    f"{int(quota.get('batches') or 0)}/{cfg['max_batches_per_day']}",
AttributeError: 'tuple' object has no attribute 'get'
```

**Cause:** commit 5987081/06b4349 changed `load_quota()` to return
`(own, by_runner, total_batches)` (docstring at line 297-305), and
`cmd_prepare` was updated to unpack it, but the stderr summary in
`cmd_collect` (line 899-903) still treats the return value as the old
dict. Every collect now exits 1 after doing all of its work.

**Impact:** side effects are complete, so the cycle proceeded on the
printed top rows and the appended journal rows (the funnel line for this
cycle records `screened: 300, escalated: 15`). But the summary line
`screen: collected X/Y ... day batches Q/CAP` that CYCLE.md step 4 says to
read is never printed, and an exit code of 1 from a protected tool is
exactly the signal an agent would otherwise treat as "collect yielded
nothing, fall back to unscreened selection". A less careful reading would
have discarded a valid screen.

**Proposed fix (protected path, operator act):** in `cmd_collect` unpack
the tuple, e.g. `_own, _by_runner, total = load_quota()` and print
`{total}/{cfg['max_batches_per_day']}` (optionally the per-runner split
as prepare already does). Reproduce with any complete work dir:
`python3 core/screen.py collect --dir reports/screener-work/20260904T080505Z`
(it will refuse to re-append because the marker exists, but the crash is
after the marker check only on a fresh dir — a unit-level call of the
summary block is enough).

**Status:** OPEN — operator ask. Agent-side handling: proceeded on the
printed rows, recorded the exit code in the funnel line and cycle log.

---

## 2026-09-04 16:2xZ — Astra by-Sep-N sibling markets' `endDate` reads today, not the titled deadline

**Evidence:** screener escalated market 4201768, "Will OpenAI's Astra
model be released by September 7, 2026?" (divergence 0.275). Its
sibling legs 4201767 (by-Sep5), 4201769 (by-Sep8), 4201770 (by-Sep6) —
one already vetoed at 12:52Z, one already no-edge at 14:35Z — all share
the exact same `endDate`: `2026-09-04T23:59:00Z`, i.e. TODAY, not their
titled deadline. Verified directly against Polymarket's own gamma API
(`gamma-api.polymarket.com/markets/4201768`, fetched independently of
`core/scan.py`, so this is not a scan-side artifact): `endDate:
"2026-09-04T23:59:00Z"`, `closed: false`, `active: true`,
`startDate: "2026-09-04T00:17:46Z"`. The market's own description says
resolution hinges on "the listed date (ET)" — i.e. the titled Sep7 date
— not on `endDate`. Two sibling legs in this same event family
(4054724 by-Sep11, 4060944 on-Sep5) do NOT have this problem — their
`endDate` matches their title correctly. This is a different shape than
the already-endorsed 2026-08-30 14:12Z title-window quirk (a market
created *after* its title's window start, narrowing the eligible
window) — here `endDate` reads *before* the title's own stated
deadline, on a subset of same-event siblings only.

**Impact:** unclear whether this is (a) harmless — `endDate` just
governs UI/trading-close behavior on a per-day-created series while
real resolution still waits for the titled ET deadline, or (b) a real
bug where these specific markets could auto-resolve or stop trading
tonight despite their title promising a later deadline. I did not treat
`endDate` as the operative resolution date (used the title's Sep7 ET
date instead, staying conservative and consistent with today's other
Astra legs) and did not bet on the ambiguity either way — the fact-
finality gate already covers this family regardless (forecast
d179339fe4c0, no bet). Flagging because if `endDate` **is** load-
bearing for `core/resolve.py`, these four legs could resolve or freeze
unexpectedly tonight in a way that wouldn't match their titles, and
because a future cycle reading `endDate` naively (e.g. to sort by time-
to-resolution) would be misled the same way the screener's divergence
score nearly was here.

**Proposed action:** none required to core — this may just be how
Polymarket structures this market family and not a bug at all. Worth an
operator or deep-retro spot-check of whether these four legs actually
resolve/freeze tonight as `endDate` implies, or keep trading past it (in
which case `endDate` is simply unreliable for this series and future
research should read the description's stated deadline, not the field).

**Status:** OPEN — informational, no urgent action; will note here
again if these legs resolve tonight against their titles.
