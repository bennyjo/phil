# Contributing

This repo has an unusual contribution policy, because the repo is an
experiment and part of it is not human-editable by design.

## What is not accepted

**Pull requests to `strategy/` or `journal/`.** The agent's own edits to its
playbook, risk policy, tools, discovery queries and pacing ARE the
experiment; its git history is the product. A human improvement to the
strategy, however good, contaminates the data. The same goes for the
journal, which is the experiment's record.

## What is considered

**Engine changes** (`core/`, `config/`, `CYCLE.md`, `loop.sh`, CI). These
are operator-owned and deliberately conservative: the engine's job is to be
an honest, stable instrument, not a feature surface. Open an issue first and
expect a high bar. Protected-file commits carry an `operator:` prefix and CI
enforces that boundary on every push.

## What is welcome

- Issues for engine bugs (wrong fills, scoring errors, settlement mistakes).
- Questions about how the experiment works.
- Forks. The license is Apache-2.0; run your own Phil, change anything you
  like, and compare notes.

## Before you open a pull request

Run the checks that CI runs. They need only Python 3 and, for the lint
step, [ruff](https://docs.astral.sh/ruff/):

```bash
python3 core/validate.py
python3 -m unittest discover -s core -p 'test_*.py'
ruff check --select E9,F core strategy
```

Commits that touch operator-owned paths (`core/`, `config/`, `.github/`,
`.claude/`, `CYCLE.md`, `REAL.md`, `loop.sh`, `CLAUDE.md`, `LICENSE`,
`README.md`, `.gitignore`) need a subject that starts with `operator:`, for
example `operator: fix settlement of voided markets`. The CI boundary guard
treats any other commit that touches them as an agent commit and fails the
push.

Never put keys, tokens, or the contents of a Pearl Connect `.mcp.json` in an
issue, a pull request, or a commit. For a vulnerability, follow the
[security policy](SECURITY.md) instead of opening a public issue.

## Code of conduct

Everyone who takes part in this project follows the
[code of conduct](CODE_OF_CONDUCT.md).

## One expectation

Phil, the agent, does not read issues or pull requests. A human does. Please
write for the human.
