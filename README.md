# Fitsek

Faceless, low-friction body recomposition funnel for busy desk workers.

## Local check

```bash
python3 scripts/validate_site.py
python3 -m http.server 8080
```

Open <http://127.0.0.1:8080>.

## Deploy

Public site deploys with GitHub Pages. The optional lead/event API runs separately on the VM from `server/lead_api.py` behind Caddy.

## Secrets

Never commit `.env`, API keys, lead exports, logs, Stripe keys, email provider keys, or Meta tokens.
