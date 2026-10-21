## What this changes

## Why

<!-- Link the issue. Engine changes need an issue first; see .github/CONTRIBUTING.md. -->

## Checks

- [ ] No changes to `strategy/` or `journal/`. The agent owns them.
- [ ] `python3 core/validate.py` passes.
- [ ] `python3 -m unittest discover -s core -p 'test_*.py'` passes.
- [ ] Commits that touch operator-owned paths start with `operator:`.
- [ ] No keys, tokens, or credentials in the diff.
