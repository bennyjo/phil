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
2. **Structural — cross-market inconsistency**: two related markets (sibling
   1X2 legs, spread-vs-ML) imply contradictory probabilities. Evidence:
   `1e8dec1078ba` won.
3. **Book-devig arbitration** (weakest): "my devig of scraped bookmaker odds
   beats the PM price" on a liquid market. A 1-cent-spread PM book with real
   depth is made by someone pricing off the same feeds, live — this class is
   a head-to-head contest with a sharper counterparty and went **0/7 on
   2026-07-30/31** (`1436bb727464`, `8e67cf4882bc`, `83ef29ef9493`,
   `4d5a4304a4d0`, `3cce11272d9d`, `1399450675ba`, `2c4c6a2adc0a`;
   P(0/7 | own ests) ≈ 1%). It requires `risk.json min_edge_book_devig`
   (0.07), not the base `min_edge`, and a power devig (see Estimation).

## Market selection

Work from `core/scan.py` output (next 48h, protected filters already applied).
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
description, books with spread > risk.json `max_spread`.

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
