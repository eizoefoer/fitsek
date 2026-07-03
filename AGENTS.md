# AGENTS.md

## Scope
This repo owns the public Fitsek static funnel and the small optional lead/event capture API used by the static site.

## Non-negotiables
- Free or near-free infra first. GitHub Pages for the public site; VM backend only for secure capture/analytics endpoints.
- Never commit secrets, `.env`, token files, API keys, payment keys, email provider keys, logs with emails, or lead exports.
- Keep Fitsek general wellness/fitness only. No medical, hormone, disease, diagnosis, guaranteed outcome, fake testimonial, or fake before/after claims.
- Faceless brand. AI/template/faceless content is fine; no misleading human transformations.
- Preserve privacy: lead/email data lives only in private runtime storage, not in the repo.

## Release gates
1. `python3 scripts/validate_site.py` passes.
2. Static site serves locally and required CTAs/forms/legal pages exist.
3. No secret-like strings or `.env` files in git diff.
4. If deployed, verify `https://fitsek.com/` live page title, CTA links, analytics snippet, and lead API reachability.
5. Update `AI_STATE.md` when deployment, DNS, product, analytics, or API status changes.
