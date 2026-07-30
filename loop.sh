#!/usr/bin/env bash
# Run trading cycles headlessly. Usage: ./loop.sh [cycles] [sleep_minutes]
set -euo pipefail
cd "$(dirname "$0")"

CYCLES="${1:-1}"
SLEEP_MIN="${2:-45}"

for i in $(seq 1 "$CYCLES"); do
  echo "=== cycle $i/$CYCLES $(date -u +%FT%TZ) ==="
  claude -p "$(cat CYCLE.md)" \
    --allowedTools "Read" "Glob" "Grep" "WebSearch" "WebFetch" \
      "Edit" "Write" \
      "Bash(python3 core/*)" "Bash(git add:*)" "Bash(git commit:*)" \
      "Bash(git rev-parse:*)" "Bash(git log:*)" "Bash(git diff:*)" \
    --permission-mode acceptEdits || echo "cycle $i failed; continuing"

  # Enforce the protected boundary: revert any agent edits to core/config.
  if ! git diff --quiet HEAD -- core/ config/protected.json CYCLE.md loop.sh CLAUDE.md; then
    echo "WARNING: agent touched protected files — reverting" >&2
    git checkout -- core/ config/protected.json CYCLE.md loop.sh CLAUDE.md
  fi
  PROTECTED_IN_LAST_COMMITS=$(git log --oneline -5 --name-only | grep -cE '^(core/|config/protected|CYCLE\.md|loop\.sh|CLAUDE\.md)' || true)
  if [ "$PROTECTED_IN_LAST_COMMITS" -gt 0 ]; then
    echo "WARNING: protected files appear in recent commits — review manually" >&2
  fi

  [ "$i" -lt "$CYCLES" ] && sleep $((SLEEP_MIN * 60))
done
