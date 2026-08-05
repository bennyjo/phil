# Security policy

## Reporting

Please use GitHub's private vulnerability reporting (Security tab, "Report a
vulnerability") rather than a public issue for anything exploitable. Reports
are read by the human operator, not by the agent.

## Scope

The interesting surface is the money path and the boundaries around it:

- `core/real.py`, the only code that touches real funds, and the caps in
  `config/protected.json` that it enforces.
- The protected-boundary enforcement: `loop.sh`'s revert list and the CI
  boundary guard (`.github/scripts/boundary.sh`).
- The integrity tripwires in `core/validate.py`.

## Threat model, stated honestly

- The agent researches the open web every cycle. Prompt injection through
  market descriptions or web content is the most interesting attack class.
  The design assumes it will eventually happen and bounds the blast radius
  instead of assuming it won't.
- Real exposure is capped in three independent places: per-bet, per-day and
  open-position caps in `config/protected.json` (with hard ceilings enforced
  by CI), the Safe's balance (the operator funds it deliberately small, and
  no code can spend past it), and the Pearl Connect signer's own guardrail,
  which runs outside the agent session.
- Keys never enter any agent session. Signing happens in Pearl Connect's
  local service; the session only names actions.
- The journal is public by design. Wallet addresses may appear there;
  tokens and credentials must not, and secret-scanning push protection is
  enabled as a backstop.

A report that moves money past those bounds, or gets an agent commit past
the protected-file boundary without an `operator:` prefix, is exactly what
this policy is for.
