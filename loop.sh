#!/usr/bin/env bash
# Run trading cycles headlessly.
# Usage: ./loop.sh [cycles] [sleep_minutes] [--real]
#   --real: append REAL.md to the prompt so qualifying paper bets get a $1
#           real twin via Pearl Connect (requires PEARL_CONNECT_STORE and a
#           healthy local connect signer; downgrades to paper otherwise).
set -euo pipefail
cd "$(dirname "$0")"

REAL_MODE=0
ARGS=()
for a in "$@"; do
  [ "$a" = "--real" ] && REAL_MODE=1 || ARGS+=("$a")
done
CYCLES="${ARGS[0]:-1}"
SLEEP_MIN="${ARGS[1]:-45}"

for i in $(seq 1 "$CYCLES"); do
  echo "=== cycle $i/$CYCLES $(date -u +%FT%TZ) ==="

  # Sync with origin before cycling so a stale local main can never silently
  # fork for days (the 2026-07-31 orphaned-history incident). Fast-forward
  # only; a genuine divergence needs a human, not an automatic reset.
  if git remote get-url origin >/dev/null 2>&1; then
    if git fetch origin main 2>/dev/null; then
      if git merge-base --is-ancestor HEAD origin/main; then
        git checkout -B main origin/main
      elif ! git merge-base --is-ancestor origin/main HEAD; then
        echo "WARNING: local main and origin/main have diverged — resolve manually" >&2
      fi
    else
      echo "WARNING: could not fetch origin/main; cycling on local state" >&2
    fi
  fi

  # Pearl Connect attach: when the local signer is up, expose its read-only
  # wallet_info MCP tool and deny the session the token file (journal is
  # public — the bearer token must never be readable, let alone committed).
  # The probe must positively identify the connect signer: every Pearl agent
  # serves /healthcheck on 8716, and a full trader FSM also reports
  # is_healthy=true — but only connect's body is bare (no "rounds" field).
  PEARL_UP=0
  STORE="${PEARL_CONNECT_STORE:-}"
  if [ -n "$STORE" ] && [ -f "$STORE/.mcp.json" ]; then
    HC="$(curl -sf -m 2 http://127.0.0.1:8716/healthcheck 2>/dev/null || true)"
    if echo "$HC" | grep -q '"is_healthy": *true' \
       && ! echo "$HC" | grep -q '"rounds"'; then
      PEARL_UP=1
    fi
  fi

  PROMPT="$(cat CYCLE.md)"
  if [ "$REAL_MODE" -eq 1 ]; then
    if [ "$PEARL_UP" -eq 1 ] \
       && python3 core/real.py doctor 2>/dev/null | grep -q '"ready": true'; then
      PROMPT="$(cat CYCLE.md REAL.md)"
    else
      echo "WARNING: --real requested but Pearl Connect signer not ready — running paper-only cycle" >&2
    fi
  fi

  CMD=(claude -p "$PROMPT"
       --allowedTools "Read" "Glob" "Grep" "WebSearch" "WebFetch"
         "Edit" "Write"
         "Bash(python3 core/*)" "Bash(git add:*)" "Bash(git commit:*)"
         "Bash(git rev-parse:*)" "Bash(git log:*)" "Bash(git diff:*)"
         "Bash(git fetch:*)" "Bash(git checkout -B main origin/main)"
         "Bash(git pull:*)" "Bash(git push:*)")
  if [ "$PEARL_UP" -eq 1 ]; then
    CMD+=("mcp__pearl-connect__wallet_info"
          --mcp-config "$STORE/.mcp.json"
          --disallowedTools "Read($STORE/.mcp.json)")
  fi
  CMD+=(--permission-mode acceptEdits)

  "${CMD[@]}" || echo "cycle $i failed; continuing"

  # Enforce the protected boundary: revert any agent edits to core/config.
  PROTECTED_PATHS=(core/ config/ .github/ CYCLE.md REAL.md loop.sh CLAUDE.md LICENSE README.md .gitignore)
  if ! git diff --quiet HEAD -- "${PROTECTED_PATHS[@]}"; then
    echo "WARNING: agent touched protected files — reverting" >&2
    git checkout -- "${PROTECTED_PATHS[@]}"
  fi
  PROTECTED_IN_LAST_COMMITS=$(git log --oneline -5 --name-only | grep -cE '^(core/|config/|\.github/|CYCLE\.md|REAL\.md|loop\.sh|CLAUDE\.md|LICENSE|README\.md|\.gitignore)' || true)
  if [ "$PROTECTED_IN_LAST_COMMITS" -gt 0 ]; then
    echo "WARNING: protected files appear in recent commits — review manually" >&2
  fi

  [ "$i" -lt "$CYCLES" ] && sleep $((SLEEP_MIN * 60))
done
