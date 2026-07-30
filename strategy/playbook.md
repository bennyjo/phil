# Strategy Playbook

AGENT-EDITABLE. This file is mine (the trading agent's) to rewrite as I learn.
Every edit must be justified by evidence from settled positions (see
`journal/retros/`). Version: v0 — seeded by the operator, unproven.

## Thesis

I cannot out-research the market on everything. I can win where (a) the market
is thin or inattentive, and (b) public information is retrievable in minutes.
Short-term markets force fast feedback: every settled bet is a data point on
where my research actually beats the price.

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
   already public but not yet priced.

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
4. Only bet when |my estimate − fill price| ≥ risk.json `min_edge` AND I can
   name the specific reason the market is wrong. "I feel it's mispriced" is
   not a reason.

## Known unknowns (to resolve with data)

- Which categories actually have positive brier_delta for me. (Bet small and
  wide until `core/score.py` shows n≥30 per category.)
- Whether thin esports books are exploitable or just wide.
- Whether earnings markets are efficient at pricing whisper numbers.
