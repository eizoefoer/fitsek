# AI_STATE.md

Last updated: 2026-07-03

## Brand
Fitsek is a faceless desk-worker body recomposition brand: simple, practical, evidence-aware, direct, encouraging, and general wellness only.

## Funnel
Traffic → `fitsek.com` → free lead magnet → email/list → paid digital product/waitlist → weekly analytics improvement.

- Free lead magnet: `7-Day Desk Worker Recomp Reset`.
- Paid product: `Fitsek 12-Week Recomp System` MVP files exist under `products/paid-recomp-system/`.
- Email/lead capture: posts to `https://leads.fitsek.com/signup`; first-party events post to `/event`.
- Analytics: Cloudflare Web Analytics plus first-party events/leads in `/var/lib/fitsek` on the VM.
- Social channels: Instagram + Facebook Page first, manual Meta Business Suite scheduling/approval mode for at least 30 days.

## Infrastructure
- Public static site: GitHub Pages from `site/` in this repository.
- Custom domain: `fitsek.com`; `www.fitsek.com` CNAME to GitHub Pages.
- Lead/event API: `server/lead_api.py`, systemd service `fitsek-leads.service`, proxied by Caddy as `leads.fitsek.com`.
- No payment checkout is connected yet. Use no-monthly-fee option when user sets account: Stripe Payment Link, Gumroad, Payhip, Lemon Squeezy, or Ko-fi.

## Automation
- `automation/business_review.py` writes daily/weekly/monthly reports to `analytics/reports/`.
- `automation/meta_autopilot.py` prepares Meta social outbox and can create FB Page drafts/scheduled posts once Meta grants `pages_manage_posts`.
- `automation/meta_token_watch.py` validates/refreshes Meta tokens where Meta permits and alerts for manual re-auth; no tokens in git.
- Cron jobs should be approval/report mode only; do not auto-post social content without explicit user approval.

## Meta state
- FB Page verified by API: `FitSek` (`100185022163250`), category `Shopping & retail`, Page tasks include `CREATE_CONTENT`.
- Linked IG Business Account was not returned by API as of 2026-07-03; check Page↔IG linking and token permissions.
- Current blocking permission: token/app lacks `pages_manage_posts`; Meta API rejected draft creation with App Review/permission error.
