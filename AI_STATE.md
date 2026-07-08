# AI_STATE.md

Last updated: 2026-07-08

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
- `automation/meta_ig_publisher.py` stores an approved IG schedule in ignored `var/meta_ig_schedule.json` and publishes due Instagram posts via Graph API from Hermes one-shot cron jobs.
- `automation/meta_token_watch.py` validates/refreshes Meta tokens where Meta permits and alerts for manual re-auth; no tokens in git.
- Cron jobs should be approval/report mode only; do not auto-post social content without explicit user approval.

## Meta state
- FB Page verified by API: `FitSek` (`100185022163250`), category `Shopping & retail`, Page tasks include `CREATE_CONTENT`.
- Meta permissions are now present for Facebook Page scheduling and Instagram content publishing (`pages_manage_posts`, `instagram_basic`, `instagram_content_publish` all granted in `check`).
- 2026-07-08: 7 Facebook Page photo posts were scheduled via Graph API for 2026-07-09 through 2026-07-15 at 19:30 AEST. Verification via `/scheduled_posts` returned 7 unpublished scheduled posts; runtime IDs are kept in ignored `var/meta_created_posts_last.json`.
- 2026-07-08: Instagram Page linkage is API-visible: `@fitsek.wellness` (`17841443568404793`) is returned as the FitSek Page `instagram_business_account`.
- 2026-07-08: 7 Instagram posts are scheduled for 2026-07-09 through 2026-07-15 at 19:30 AEST using one-shot Hermes no-agent cron jobs (`Fitsek IG Publish Day 01..07`) that run `fitsek_ig_publish_due.sh`; runtime schedule/status lives in ignored `var/meta_ig_schedule.json`.
- 2026-07-07 API path update: `automation/meta_autopilot.py` now defaults to Graph API `v25.0`, exposes `python3 automation/meta_autopilot.py permissions` for a safe App Review/API path diagnostic, and stops `fb-draft --confirm` before the write call when `pages_manage_posts` is missing.
