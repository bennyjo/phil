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

**Status:** open

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

**Status:** open
