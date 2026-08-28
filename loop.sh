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

  # With HEAD detached, `git push origin main` pushes the stale local branch
  # ref and reports success - the cycle's commits never reach the remote
  # (2026-08-17: 34 commits nearly lost). Reattach main to HEAD before any
  # sync or push logic can judge state.
  if ! git symbolic-ref -q HEAD >/dev/null; then
    echo "WARNING: HEAD detached — reattaching main to HEAD" >&2
    git checkout -B main HEAD
  fi

  # Sync with origin before cycling so a stale local main can never silently
  # fork for days (the 2026-07-31 orphaned-history incident). Fast-forward
  # only; a genuine divergence needs a human, not an automatic reset.
  if git remote get-url origin >/dev/null 2>&1; then
    # A shallow clone manufactures fake divergence (no merge-base, spurious
    # "forced update") — unshallow before any behind/diverged judgment.
    if [ "$(git rev-parse --is-shallow-repository 2>/dev/null)" = "true" ]; then
      git fetch --unshallow origin 2>/dev/null \
        || git fetch --deepen=1000 origin 2>/dev/null \
        || echo "WARNING: could not unshallow clone" >&2
    fi
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
  # wallet_info MCP tool plus the mech marketplace tools, and deny the
  # session the token file (journal is public — the bearer token must never
  # be readable, let alone committed).
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

  # No "Bash(git push:*)": on this machine loop.sh owns the push (see the
  # push block below). The ref plumbing is allowlisted because CYCLE.md
  # step 9 and its rebase path mandate exactly these commands, and a
  # permission-blocked "checkout -B" strands the cycle's commits on a
  # detached HEAD (2026-08-28).
  CMD=(claude -p "$PROMPT"
       --allowedTools "Read" "Glob" "Grep" "WebSearch" "WebFetch"
         "Edit" "Write" "Task"
         "Bash(python3 core/*)" "Bash(git add:*)" "Bash(git commit:*)"
         "Bash(git rev-parse:*)" "Bash(git log:*)" "Bash(git diff:*)"
         "Bash(git status:*)" "Bash(git symbolic-ref:*)"
         "Bash(git merge-base:*)" "Bash(git rev-list:*)"
         "Bash(git fetch:*)" "Bash(git checkout -B main origin/main)"
         "Bash(git checkout -B main HEAD)"
         "Bash(git rebase --continue)" "Bash(git rebase --abort)"
         "Bash(git rebase --quit)"
         "Bash(git pull:*)")
  if [ "$PEARL_UP" -eq 1 ]; then
    # wallet_info is read-only; the mech_* tools buy predictions from the
    # Olas mech marketplace (~$0.01 USDC each, paid by the service safe) per
    # CYCLE.md step 5a. No other signing tools are exposed.
    CMD+=("mcp__pearl-connect__wallet_info"
          "mcp__pearl-connect__mech_tools"
          "mcp__pearl-connect__mech_request"
          "mcp__pearl-connect__mech_result"
          --mcp-config "$STORE/.mcp.json"
          --disallowedTools "Read($STORE/.mcp.json)")
  fi
  CMD+=(--permission-mode acceptEdits)

  # PHIL_PUSH_BY_LOOP tells CYCLE.md step 9 to commit but not push — the push
  # happens below, in this shell. GIT_TERMINAL_PROMPT/GIT_ASKPASS make any
  # stray credential lookup fail fast instead of hanging on a keyring prompt
  # no headless session can answer; GIT_EDITOR stops `git rebase --continue`
  # from opening an editor and blocking forever.
  PHIL_PUSH_BY_LOOP=1 \
  GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=/usr/bin/true GIT_EDITOR=true \
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

  # Push from this shell, not from the agent. The credential helper is
  # `gh auth git-credential`, which reads the token from the macOS keyring —
  # a keyring prompt is unanswerable inside `claude -p`, so pushes there hang
  # until timeout and the cycle's commits never leave the machine
  # (2026-08-28: three hangs, commits stranded on a detached HEAD). This shell
  # is the interactive one the operator started, where the keychain is already
  # unlocked. CI remains the guard on protected-path commits.
  if git remote get-url origin >/dev/null 2>&1; then
    if ! git symbolic-ref -q HEAD >/dev/null; then
      echo "WARNING: HEAD detached after cycle — reattaching main to HEAD" >&2
      git checkout -B main HEAD
    fi
    if ! git push origin main; then
      echo "push rejected — rebasing onto origin/main and retrying" >&2
      if git pull --rebase origin main; then
        git push origin main \
          || echo "WARNING: push still failing after rebase — resolve manually" >&2
      else
        # Never hand-resolve a ledger conflict here; leave it for the operator.
        git rebase --abort 2>/dev/null || true
        echo "WARNING: rebase onto origin/main failed — commits are local only, resolve manually" >&2
      fi
    fi
  fi

  [ "$i" -lt "$CYCLES" ] && sleep $((SLEEP_MIN * 60))
done
