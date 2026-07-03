# Fitsek

Faceless, low-friction body recomposition funnel for busy desk workers.

## Repo structure

- `site/` — GitHub Pages static landing site.
- `content/social/` — 30-day social calendar and post drafts for Instagram/Facebook approval-mode scheduling.
- `content/email/` — email/nurture copy.
- `products/free-lead-magnet/` — free lead magnet source.
- `products/paid-recomp-system/` — minimum viable paid product files.
- `assets/social/` — generated faceless social visuals/templates.
- `automation/` — reporting/check scripts; no secrets.
- `analytics/` — schema, manual metrics template, generated reports.
- `docs/` — strategy, compliance, operations.
- `server/` — optional VM lead/event API.

## Local checks

```bash
python3 scripts/validate_site.py
python3 -m http.server 8080 -d site
```

## Release

GitHub Pages deploys `site/` after `scripts/validate_site.py` passes.

## Security

Never commit `.env`, API keys, lead exports, logs with emails, Meta tokens, Stripe/payment keys, or email provider credentials.
