#!/usr/bin/env bash
# Hermes no-agent cron wrapper for Fitsek social verification.
# Missing due posts are actionable alerts, not scheduler faults: stdout is
# delivered, then exit 0. Meta/API verifier errors remain non-zero.
set -euo pipefail
export PATH="$HOME/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
# A deployed Hermes cron script lives outside the repo; default to the canonical
# checkout but allow a worktree path for local validation.
ROOT="${FITSEK_ROOT:-/home/ubuntu/fitsek}"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
set +e
"$PYTHON_BIN" automation/verify_posts.py --quiet --json --fail-on-missing-due --window-hours 6 --grace-minutes 30
status=$?
set -e

# verify_posts: 0=healthy, 1=missing due post (alert delivered), 2=API/runtime failure.
if [[ "$status" -eq 1 ]]; then
  exit 0
fi
exit "$status"
