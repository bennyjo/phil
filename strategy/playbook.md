# Strategy Playbook

AGENT-EDITABLE. This file is mine (the trading agent's) to rewrite as I learn.
Every edit must be justified by evidence from settled positions (see
`journal/retros/`). Version: v0 — seeded by the operator, unproven.

## Thesis

I cannot out-research the market on everything. I can win where (a) the market
is thin or inattentive, and (b) public information is retrievable in minutes.
Short-term markets force fast feedback: every settled bet is a data point on
where my research actually beats the price.

### Edge classes (added DEEP-2026-07-31, from the 2/2 vs 0/7 split)

Rank every candidate by WHY the market should be wrong, strongest first:

1. **Structural — information race**: the resolution-relevant fact is already
   public and the book demonstrably hasn't finished repricing (verify at the
   live book, not the mid). Evidence: `2dc417ed68f6` won.
   **Fact-finality requirement (DEEP-2026-08-03):** the fact must be FINAL
   as the resolver will see it — an official print/close/result — not an
   estimate subject to scheduled revision, whenever the bet's margin sits
   inside typical revision noise. Sunday box-office numbers are studio/
   Comscore estimates revised by Monday actuals; `84ec821167d5` bet No at
   0.16 on a "$2M short" (0.6%) margin from such an estimate and was
   marked to ~0.02 within 10h as actuals landed. N outlets repeating one
   provisional figure are ONE source, not N confirmations. Corollary: a
   liquid book holding its price AFTER your headlines are public — or
   moving further against you while you check — is the crowd pricing
   something beyond the headline (revision risk, resolver read), not the
   crowd being slow; the NG win (`2dc417ed68f6`) was the opposite shape,
   an already-final official settlement print.
2. **Structural — cross-market inconsistency**: two related markets (sibling
   1X2 legs, spread-vs-ML) imply contradictory probabilities. Evidence:
   `1e8dec1078ba` won.
   **Validity test (DEEP-2026-08-03):** the sibling's implied probability
   must be actually INCOMPATIBLE with the target market's — work the
   implication out numerically before citing it. A bracket market whose
   range contains the target's threshold discriminates nothing:
   `84ec821167d5` cited the $350-360M bracket (~85% Yes) as contradicting
   beat-record-$357.1M (~84% Yes), but $357.1M is inside the bracket, so
   those prices are perfectly consistent (crowd centered ~$357-360M).
   The claimed inconsistency was an inference error, not a signal.
3. **Book-devig arbitration** (weakest): "my devig of scraped bookmaker odds
   beats the PM price" on a liquid market. A 1-cent-spread PM book with real
   depth is made by someone pricing off the same feeds, live — this class is
   a head-to-head contest with a sharper counterparty and went **0/7 on
   2026-07-30/31** (`1436bb727464`, `8e67cf4882bc`, `83ef29ef9493`,
   `4d5a4304a4d0`, `3cce11272d9d`, `1399450675ba`, `2c4c6a2adc0a`;
   P(0/7 | own ests) ≈ 1%). It requires `risk.json min_edge_book_devig`
   (0.07), not the base `min_edge`, and a power devig (see Estimation).
   Confirmed 2026-07-31/08-01 at zero cost: ~12 clean benchmarks devigged
   across MLB/WNBA/soccer, every tight PM book matched the devigged line
   within 1-2 cents (cycle logs 17:11Z–02:12Z).

Info-race is on watch (DEEP-2026-08-02, marks updated DEEP-2026-08-03):
all three open structural positions are marked against us — the Iran pair
(`b21e42c123a1` est 0.90, mid ~0.045 vs entry 0.15; `d2dd24206542` est
0.98, No mid ~0.395 vs entry 0.92, worsening) unresolved 3+ days past end
date, and `84ec821167d5` (No mid ~0.02 vs entry 0.16, see fact-finality
rule above; its pre-registered grading is in DEEP-2026-08-03 §a). Pre-registered rule-candidate,
to be enacted ONLY if the pair settles as losses: "multi-source verified"
tightens to require at least one non-party primary source (wire service
Reuters/AP/AFP, host-government statement, or the resolver's own named
source) — a consensus composed of state media of the parties to the event
(PressTV, Mehr, TASS, Xinhua on the Iran claims) does not qualify on its
own. If either leg wins, this stays a caution, not a rule.

NOT an edge class — **resolver-interpretation reads** (graded
DEEP-2026-08-01): "I checked the exact resolution source and it says X"
where the reading requires a judgment call (UI toggle, table choice, which
mirror). The ai-leaderboard pair (`7e753de88823`+`0bf9fe3785c6`, one
decision, -$10) lost while the operator verified the named source three
times over 22h — including after resolution — and it never moved
(journal/operator-notes.md). The fact was right; the resolution process
read it differently. Treat these below book-devig; the §Estimation
resolver-process red-flag rule applies.

## Market selection

**Scan horizon (OPERATOR EDIT 2026-08-03, see journal/operator-notes.md):**
default to
`python3 core/scan.py --hours 168 --min-volume-24h 0 --min-total-volume 50000`.
The `--min-total-volume` flag is new (operator patch to core/scan.py, same
date) and is REQUIRED to see past today: results page in endDate order and the
near-term universe is thousands of sub-daily markets deep, so `--hours` alone
never escapes the current day — verified, 1004/1004 candidates were day-0.
With the flag, the same scan surfaces ATP/WTA main-draw tennis 5–7 days out
(liquidity $200k–460k), central-bank decisions, and countable-metric markets.
Do NOT also apply a 24h-volume floor on a weekly window: an event five days
out legitimately has little volume today, so that filter re-creates the bug.
Evidence for all of this: 19 straight no-bet cycles on 2026-08-02/03. The 48h
window structurally selects for
whatever clears the volume filter *soon* — Icelandic, Argentine second-tier
and lower-league fixtures — which are exactly the events with no searchable
sharp benchmark, so research fails and no bet is possible. Well-covered
events (major European leagues, MLB/NBA/NFL/WNBA, big esports finals,
scheduled earnings and macro releases) mostly sit 2–7 days out. Longer
horizon also means slower feedback; that is an accepted cost, since feedback
is already gated by resolution lag, not by bet frequency. Revisit if the
weekly window produces placements without improving hit quality.

**Coverage precondition (OPERATOR EDIT 2026-08-03):** before spending research
effort on a candidate, spend ONE search establishing whether a sharp benchmark
is retrievable at all (a real bookmaker line for this exact market, an analyst
consensus, an official schedule/print). If nothing sharp is retrievable, drop
the candidate immediately and move on — do not build an estimate on aggregator
"prediction model" numbers. Scraping consumer odds portals directly does not
work from the cloud runner: forebet/oddsportal/oddspedia 403 datacenter IPs
(this is site-level bot blocking, NOT the sandbox egress policy — the earlier
"recurring egress block" diagnosis in cycle logs was wrong). WebSearch results
do work; use them.

**Prefer mechanically-resolving markets.** Consistent with the fact-finality
rule, markets that resolve off an official print, close, or scoreboard
(earnings, macro releases, match results) beat markets needing a judgment call
about a source or a rules reading — the ai-leaderboard and Iran pairs cost $20
between them on resolution-process risk, and both are still unresolved or lost.

**`end_date` is not the actual match/event time for tennis draws (2026-08-03
finding).** Six National Bank Open / Canadian Open / DC Open candidates in
one scan all carried `end_date` of 2026-08-09 or 2026-08-10 (the tournament's
last day), but WebSearch on the actual matchups showed real scheduled times
of 2026-08-02/08-03 — e.g. Berrettini vs Navone: scan `end_date` 2026-08-10,
actual scheduled time 2026-08-03 16:35 UTC (today); Frech vs Jeanjean and
Boisson vs Ruzic: actual dates 2026-08-02 (yesterday), yet their live books
were still mid-range (0.70-0.88), not resolved-looking. `end_date` for these
markets is evidently a tournament-level fallback/dispute deadline, not the
match's real time — do not assume a scan candidate is safely pre-match
because its `end_date` looks days out. Verify the actual scheduled time (or
live status) per-candidate before researching or betting; if it can't be
pinned down, treat as possible in-play and skip (same reasoning as the
esports in-play rule). This cycle, Fritz vs Jodar showed a similarly
suspicious pattern independent of this issue: pre-match sportsbook odds
implied Fritz ~65%, but the live PM book was 0.92-0.93 bid/ask with >20k
depth — almost certainly in-play with Fritz already dominant, so the
sportsbook "benchmark" was stale, not the PM price. Skipped.

Work from `core/scan.py` output (protected filters already applied).
Prefer, in order:
1. **Earnings-beat markets** (`Will X beat quarterly earnings?`) — resolve
   same evening. Research: consensus EPS estimate, whisper numbers, the
   company's historical beat rate (most large caps beat 75–85% of quarters),
   recent guidance, peer results this season. Suspect mispricing when the
   price is far from the historical beat base rate without news to justify it.
2. **Soccer daily match markets** — resolve at final whistle. Research: recent
   form, injuries/rotation news, home/away splits, league table stakes,
   odds at conventional bookmakers (the sharpest available benchmark — if
   Polymarket materially diverges from bookmaker-implied probability, that is
   the signal).
3. **Esports pre-match only** (never in-play — the book moves faster than I
   can research). Research: team ratings (HLTV for CS, etc.), map pools,
   recent roster changes. Thin books here: check the spread before trusting
   the price.
4. **Short-horizon news/politics** — only when a resolution-relevant fact is
   already public but not yet priced. Caveat (2026-07-30): "not yet priced"
   must mean the BOOK, not the scan mid. Near-resolution markets (commodity
   daily closes, IPO-day closes) show stale mids while makers have already
   moved asks to 0.98+. The window between fact-public and book-repriced is
   usually gone by the time scan surfaces it — verify with the live book
   before spending research time.

Avoid: anything the protected config bans (sub-daily crypto), in-play markets,
markets whose resolution criteria I don't fully understand after reading the
description, books with spread > risk.json `max_spread` (scope below).

### Spread-rule scope (DEEP-2026-08-01)

`max_spread` is a HARD veto for book-devig / benchmark-derived bets and for
any market where my own estimate is uncertain: a wide book there means the
benchmark comparison is unreliable and the market is telling me something I
don't know (correctly applied to ENA/XRP retrospective-fact markets,
2026-08-01 03:11Z).

Narrow exception — **structural info-race only**: positions are held to
resolution (never exited) and fill at the ask, so exit liquidity is
irrelevant; a wide bid/ask on a market whose resolving fact is verified by
multiple independent sources is the signature of the inattentive book this
class targets (both structural wins came from 0.01–0.06-spread books; all
seven book-devig losses from 1-cent books). A bet may exceed `max_spread`
only if ALL hold: (1) info-race class, fact multi-source verified;
(2) edge at the ASK ≥ `risk.json min_edge_wide_book` (0.30); (3) the cycle
log explicitly states the bid/ask/spread and invokes this exception.

Violation on record: `b21e42c123a1` (2026-07-31 23:15Z) was placed at
spread 0.13 with no mention of the spread in the cycle log — a silent skip
of a written check. Whatever a bet's merits, a rule that seems wrong gets
flagged in a retro and proposed for change; it does not get silently
ignored. Every placement's cycle-log entry must state the spread check
from now on.

## Open-position monitoring (DEEP-2026-08-02)

Positions are held to resolution — never exited — but their live prices
are free information about the resolver. **REQUIRED line in every cycle
log, no exceptions** (sharpened DEEP-2026-08-03 after 10 of 19 cycles
silently skipped it — including 23:11Z, the cycle that placed
`84ec821167d5` and missed the start of its 0.14 collapse): for each open
position past its market end date, fetch the current book and log
`position id, entry, live bid/ask, mid, adverse move`; if none qualify,
log the literal line "open-position monitor: none past end date". Any
adverse move ≥ 0.10 from entry must be called out explicitly.
Evidence: `d2dd24206542` repriced from ~0.08 Yes at entry to ~0.545 Yes
over 2026-08-01/02 — 46 points against us on a thesis logged as
"structurally impossible" — and ~28 consecutive cycle logs repeated
"awaiting official resolution" without noticing. A sustained multi-day
adverse repricing on an unresolved market is resolver-process evidence
(dispute, rules reading we don't have) and feeds the position's eventual
grading; it is NOT a reason to exit (we can't) or to average in (ledger
forbids add-ons).

## Estimation method

1. Read the resolution criteria in the market description. Bet on what
   *resolves*, not what's likely in spirit.
2. Form an independent estimate BEFORE looking hard at the market price
   (anchoring guard). Write the estimate down in the rationale.
3. Identify the sharpest external benchmark (bookmaker odds, analyst
   consensus, base rates) and reconcile.
   - **Devig with `strategy/tools/devig.py`, and use the POWER number for any
     side priced below ~0.60.** Proportional (divide-by-sum) devig spreads
     the vig evenly, but books load vig onto longshots (favorite-longshot
     bias) — at typical 5-7% overrounds it inflates the cheap side by
     ~0.5-1.5 cents (Sun ML +144: proportional 0.390 vs power 0.381), a
     quarter-to-a-third of a 0.04 "edge". All 7 losing bets of
     2026-07-30/31 bought the cheaper side (0.34-0.52) off proportional
     devigs (DEEP-2026-07-31).
   - **Check line freshness before calling a divergence an edge.** Scraped
     aggregators lag; PM sports makers don't. If ANY book already matches
     PM's number, or reports are mixed, assume PM reflects the current line
     and the gap is a line move you saw late — not edge. Evidence:
     `8e67cf4882bc` (entry note said "one book 4.5" while betting against
     -4.5; Sky covered) and `1436bb727464` (aggregator "consensus 188-189"
     vs PM 185.5; Under hit).
4. Only bet when |my estimate − fill price| ≥ the min edge for the edge
   class (`min_edge` for structural, `min_edge_book_devig` for book-devig
   arbitration) AND I can name the specific reason the market is wrong.
   "I feel it's mispriced" is not a reason.
   - **A literal source-reading vs a >0.90 market consensus is a resolver-
     process red flag, not just a confident fact.** Evidence (2026-07-31):
     `7e753de88823` (Moonshot Yes) bet that a named leaderboard source
     showed Moonshot on top; the operator verified that exact source
     directly, three times spanning 22h including 2.5h *after* resolution,
     and it never moved off the same reading — yet the market resolved the
     other way, at ~93% confidence priced in advance. The market's price
     predicted the resolution better than the literal source read did. When
     your reading of a resolution-relevant source disagrees with a >0.90
     consensus, that consensus likely embeds something about HOW the
     resolver reads the source (which table/toggle/view, dispute
     precedent) that a fact-only check doesn't capture. Before betting
     against that kind of consensus, name specifically what the crowd
     might be missing about the *resolution process* — not just re-confirm
     the fact. This applies to resolution reads requiring a judgment call
     (UI settings, which mirror/table); it does not apply to mechanical
     resolution sources (a number printed in an official filing/API),
     which aren't implicated by this evidence.
5. **Check the live book first** (`python3 strategy/tools/quote.py
   <clob_token_id>`, token ids are in scan output; if the sandbox blocks it,
   `curl -s "https://clob.polymarket.com/book?token_id=<id>" -o reports/book_<x>.json`
   and read the file — fetch into `reports/` not `/tmp`; the sandbox blocks
   reading `/tmp` (learned 2026-07-30 cycle 3). Delete the scratch files
   before committing. `scan.py` outcome_prices are stale mids; fills happen
   at the best ask. Apply `min_edge` to the ASK, not the scan price.
   Evidence (2026-07-30 cycle): REF "No" scan mid 0.833 → ask 0.999
   (rejected); NG "Up" scan mid 0.915 → filled 0.95, edge collapsed to 0.02;
   WTI "Down" scan mid 0.926 → best ask 0.98 vs est 0.97 (negative edge,
   skipped). Stale mids cut BOTH ways: Corinthians win scan mid 0.455 →
   live book 0.42/0.43 (2026-07-30 cycle 4) — a marginal-looking edge on
   the mid can be a qualifying edge at the ask, so check the book before
   discarding near-threshold candidates too.

6. **One position per market+outcome** — the ledger rejects add-ons even at a
   better price (2026-07-30 cycle 5: Corinthians Yes re-entry at 0.42 vs held
   0.43 rejected). If new evidence strengthens a held position, capture the
   edge via a correlated sibling market instead: e.g. holding "Team A win Yes",
   the extra edge showed up in "Team B win No" (devig 0.78 vs ask 0.74) —
   sibling 1X2 legs are priced independently enough to diverge.
   Sharpened (DEEP-2026-07-31) — know which pair type you're building:
   - **Hedge-like pair** (e.g. "A win Yes" + "B win No": a draw splits them):
     partial offset, acceptable. Evidence: `2c4c6a2adc0a`+`1e8dec1078ba`
     went 1W/1L on a draw, net -$3.24.
   - **Same-direction pair** (e.g. "A win No" + "B win Yes": both lose if A
     wins): this is doubled event exposure, not extra edge capture. Only
     take it when each leg independently clears its edge threshold, and
     never exceed `risk.json max_stake_per_event_usd` on one underlying
     event. Evidence: `821d54f6b7c8`+`53283a95e7bb` (open) — $10 rides on
     "Bucaramanga doesn't win".
   - Retros must grade a correlated pair as ONE decision (net P&L per
     event), not as independent wins/losses.

## Known unknowns (to resolve with data)

- Which categories actually have positive brier_delta for me. (Bet small and
  wide until `core/score.py` shows n≥30 per category.)
- Whether thin esports books are exploitable or just wide.
- Whether earnings markets are efficient at pricing whisper numbers.
