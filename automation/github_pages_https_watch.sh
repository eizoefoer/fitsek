#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/fitsek

page_json="$(gh api repos/eizoefoer/fitsek/pages 2>/dev/null || echo '{}')"
current="$(python3 - <<'PY' "$page_json"
import json, sys
try: print(json.loads(sys.argv[1]).get('https_enforced', False))
except Exception: print(False)
PY
)"
if [ "$current" != "True" ] && [ "$current" != "true" ]; then
  out="$(gh api --method PUT repos/eizoefoer/fitsek/pages -F https_enforced=true 2>&1 || true)"
  if printf '%s' "$out" | grep -qi 'certificate does not exist yet'; then
    # Certificate is still provisioning. Stay silent; the next cron tick will retry.
    exit 0
  fi
fi

failures=0
for url in https://fitsek.com/ https://www.fitsek.com/; do
  if ! curl -fsSI --max-time 20 -L "$url" >/dev/null; then
    echo "Fitsek HTTPS live check failed for $url"
    failures=$((failures + 1))
  fi
done

if [ "$failures" -gt 0 ]; then
  gh api repos/eizoefoer/fitsek/pages/health 2>/dev/null || true
  exit 1
fi
