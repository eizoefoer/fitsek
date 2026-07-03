# AI_STATE.md

Last updated: 2026-07-03

## Brand
Fitsek is a faceless desk-worker body recomposition brand: simple, practical, evidence-aware, direct, encouraging, and general wellness only.

## Funnel
- Traffic: faceless short-form social posts and UTM-tagged links.
- Landing page: `https://fitsek.com/` on GitHub Pages.
- Free lead magnet: “7-Day Desk Worker Recomp Reset”.
- Paid product/waitlist: “Fitsek 12-Week Recomp System”.
- Email/lead capture: posts to `https://leads.fitsek.com/signup` when backend is deployed; otherwise page degrades gracefully and tells the visitor to email `hello@fitsek.com`.
- Analytics: Cloudflare Web Analytics plus first-party event posts to `https://leads.fitsek.com/event` when backend is deployed.

## Infrastructure target
- Public static site: GitHub Pages from this repository.
- Custom domain: `fitsek.com`; `www.fitsek.com` should redirect via GitHub Pages after DNS is moved.
- Lead/event API: loopback Python service on the VM behind Caddy at `leads.fitsek.com`.

## Product status
- Free guide and product preview are static pages.
- Paid checkout link is not configured yet; do not add Stripe/Gumroad/Payhip/Lemon Squeezy secrets to the repo. Use environment/secrets only when selected.
