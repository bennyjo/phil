# Real-execution addendum

This section is appended to your cycle prompt ONLY when the operator runs
`./loop.sh --real` on a machine with a healthy Pearl Connect signer. Real
money is involved. Everything in CYCLE.md still applies; these steps are
additive.

## Extra steps

- During **Settle** (step 1), also run: `python3 core/real.py settle`.
  It sweeps filled positions to the Safe, redeems resolved ones, and
  reconciles any ambiguous submissions. Read its output; report anomalies
  (reverted redemptions, unresolved pending orders) in the cycle log.
- After **each paper bet you place** (step 6): if the bet's `--edge-class`
  is in `config/protected.json` → `real.allowed_edge_classes`, mirror it:
  `python3 core/real.py place --paper-id <paper ledger id>`
  The stake comes from `real.max_stake_usd` in config; never pass `--usd`
  yourself. Real caps are enforced by core/real.py — a refusal (cap hit,
  market already held, unreconciled order) is policy working, not an error
  to fix.
- In the **Log** line (step 7), append: ` | real: placed R settled S`.

## Hard rules for real mode

- core/real.py is the ONLY way you touch real funds. Never call Pearl
  Connect signing tools or the skill scripts directly.
- Never blind-retry a failed or timed-out real order — buys are not
  idempotent. core/real.py blocks new bets while any order is
  unreconciled; respect that.
- A guardrail refusal from the signer names the rule it violated — relay
  it verbatim in the cycle log and move on; never work around it.
- A 403/geoblock on order placement is venue policy: report it and stop
  real execution for the cycle. Do not attempt to circumvent.
- Never write tokens, config contents, or signer URLs to the journal —
  the journal is public. Wallet addresses are fine.
