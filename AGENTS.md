# AGENTS.md

## Scope
This repo owns Fitsek: the static funnel, content system, digital products, analytics/reporting scripts, and optional lead/event API.

## Operating principle
Optimise for profitable validation, not overbuilding. Build the smallest useful system that can publish consistently, capture leads, sell a simple digital product, measure performance, and improve every week.

## Non-negotiables
- Free or near-free resources first. GitHub Pages for the public site; VM backend only for secure capture/analytics endpoints.
- Never commit secrets, `.env`, token files, API keys, payment keys, Meta credentials, lead exports, screenshots/logs containing secrets, or local configs.
- Keep Fitsek general fitness/wellness only. No medical, hormone, disease, diagnosis, guaranteed outcome, fake testimonial, or fake before/after claims.
- Faceless brand. AI/template/faceless content is fine; never present generated people as real customers.
- Meta/Instagram/Facebook: manual approval/scheduling first 30 days. Use approved permissions only. Do not bypass app review, spam, mass-post, or manipulate engagement.

## Release gates
1. `python3 scripts/validate_site.py` passes.
2. Static site serves locally from `site/` and required CTAs/forms/legal pages exist.
3. No secret-like strings or `.env` files in git diff.
4. If deployed, verify `https://fitsek.com/` live page title, CTA links, analytics snippet, and lead API reachability.
5. Update `AI_STATE.md` when deployment, DNS, product, analytics, cron, or API status changes.

## Content requirements
Every social draft must include hook, caption, CTA, hashtags, visual brief, suggested format, destination URL with UTM, and funnel stage.
