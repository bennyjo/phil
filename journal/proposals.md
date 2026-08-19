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
