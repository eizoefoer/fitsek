#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/fitsek
current="$(gh api repos/eizoefoer/fitsek/pages --jq '.https_enforced' 2>/dev/null || echo false)"
if [ "$current" = "true" ]; then
  exit 0
fi
out="$(gh api --method PUT repos/eizoefoer/fitsek/pages -F https_enforced=true 2>&1 || true)"
if printf '%s' "$out" | grep -qi 'certificate does not exist yet'; then
  exit 0
fi
new="$(gh api repos/eizoefoer/fitsek/pages --jq '.https_enforced' 2>/dev/null || echo false)"
if [ "$new" = "true" ]; then
  echo 'Fitsek GitHub Pages HTTPS enforcement enabled.'
else
  echo "Fitsek HTTPS enforcement check needs attention: $out"
fi
