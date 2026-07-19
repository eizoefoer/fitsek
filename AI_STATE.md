# AI_STATE.md

Last updated: 2026-07-18

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
- 2026-07-10: GitHub Pages custom domain HTTPS was re-triggered by clearing/re-adding `fitsek.com`; `https_enforced` is now `true`, `https://fitsek.com/` returns `200`, and `https://www.fitsek.com/` redirects to the apex.
- Lead/event API: `server/lead_api.py`, systemd service `fitsek-leads.service`, proxied by Caddy as `leads.fitsek.com`.
- No payment checkout is connected yet. Use no-monthly-fee option when user sets account: Stripe Payment Link, Gumroad, Payhip, Lemon Squeezy, or Ko-fi.

## Brand/assets
- 2026-07-10: Added Fitsek SVG logo/favicon/web manifest plus faceless photorealistic website/social images under `site/assets/photoreal/`, `site/assets/social/`, and derivative `site/assets/brand/` paths. Provenance lives in `docs/brand-image-provenance.md`, `docs/assets/photoreal-faceless-image-set-2026-07-10.md`, and `docs/assets/prompts/photoreal-faceless/`. These images are synthetic brand/lifestyle visuals and must not be represented as real customer proof, testimonials, before/after results, or medical evidence.
- 2026-07-19: The live Instagram audit found the actual profile still had a default avatar and a text-only feed despite earlier website assets. The profile/reels refresh branch adds a dedicated high-legibility avatar, three faceless photographic social images, and three 1080×1920 eight-second H.264 reels under `site/assets/social/profile-reels/`. Repository assets are not proof of a live profile update; Meta profile/avatar and media publishing must be verified after the branch is deployed.

## Analytics / measurement
- 2026-07-10: Cloudflare Web Analytics is installed on every public page. `site/app.js` also emits first-party `page_view`, `click`, `outbound_intent`, `section_view`, `scroll_depth`, and signup outcome events to `https://leads.fitsek.com/event`; heatmap-style reporting is aggregate-only via `automation/heatmap_report.py`, with no session recording enabled.
- 2026-07-18: Site refresh PR #3 merged to `main`; GitHub Actions run `29652456060` passed validate+deploy, live `https://fitsek.com/` served the new photoreal hero/assets and Cloudflare beacon, and `https://leads.fitsek.com/event` accepted curl/browser live-check events with HTTP 202.

## Agent/CI state
- 2026-07-09: Agent harness policies include SDLC/IaC/CI/human-collaboration rules in `system/sdlc-iac-ci.md`; meaningful repo work should use feature/fix/agent branches or worktrees, existing CI first, IaC/rollback records for infra changes, and human worker job-ledger rows for accepted human changes.
- GitHub Pages workflow validates pushes to `main` and pull requests targeting `main`; deploy is skipped for pull requests and runs only for non-PR workflow events.

## Automation
- `automation/business_review.py` writes daily/weekly/monthly reports to `analytics/reports/`.
- `automation/meta_autopilot.py` prepares Meta social outbox with a copy-polish gate and can create FB Page drafts/scheduled posts once Meta grants `pages_manage_posts`.
- `automation/social_copy.py` turns the raw calendar into public-facing social-manager copy and fails audits if internal labels such as `CTA:` leak into captions.
- `automation/meta_ig_publisher.py` stores an approved IG schedule in ignored `var/meta_ig_schedule.json` and publishes due Instagram posts via Graph API from the recurring Hermes due-check cron.
- `automation/verify_posts.py` checks FB/IG live publishing state and powers the silent verification cron.
- `automation/meta_token_watch.py` validates/refreshes Meta tokens where Meta permits and alerts for manual re-auth; no tokens in git.
- Cron jobs should be approval/report mode only; do not auto-post social content without explicit user approval.

## Meta state
- FB Page verified by API: `FitSek` (`100185022163250`), category `Shopping & retail`, Page tasks include `CREATE_CONTENT`.
- Meta permissions are now present for Facebook Page scheduling and Instagram content publishing (`pages_manage_posts`, `instagram_basic`, `instagram_content_publish` all granted in `check`).
- 2026-07-08: Facebook scheduled-post copy has been moved behind the `automation/social_copy.py` polish gate. The current weekly rhythm is 3 polished, unique photo posts/day at 09:00, 13:00, and 17:00 AEST for 2026-07-09 through 2026-07-15. `/scheduled_posts` verification returned 21 unpublished scheduled posts, zero `CTA:`/`Fitsek rule:` copy leaks, and media attached to every post; runtime IDs are kept in ignored `var/meta_created_posts_last.json`.
- 2026-07-08: Instagram Page linkage is API-visible: `@fitsek.wellness` (`17841443568404793`) is returned as the FitSek Page `instagram_business_account`.
- 2026-07-08: 21 Instagram posts are queued in ignored `var/meta_ig_schedule.json` for 2026-07-09 through 2026-07-15 at 09:00, 13:00, and 17:00 AEST each day. A single recurring no-agent cron `Fitsek IG Publish Due Check` runs `fitsek_ig_publish_due.sh` every 15 minutes, stays silent when no post is due, and prints Meta media IDs only when publishing.
- 2026-07-08: `Fitsek Social Publish Verification` runs `fitsek_social_verify.sh` every 30 minutes and stays silent unless a due FB/IG post is missing after the grace window or Meta verification fails.
- 2026-07-07 API path update: `automation/meta_autopilot.py` now defaults to Graph API `v25.0`, exposes `python3 automation/meta_autopilot.py permissions` for a safe App Review/API path diagnostic, and stops `fb-draft --confirm` before the write call when `pages_manage_posts` is missing.
