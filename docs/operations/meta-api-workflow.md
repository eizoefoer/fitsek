# Fitsek Meta API Workflow

## Current publishing policy

- First 30 days: approval-first. Create drafts/outbox and review before posting.
- After 30 days: full auto-posting can be enabled only after explicit approval.
- Never bypass Meta app review or use unapproved permissions.
- Store tokens in `~/.hermes/.env`, never in git.

## Required environment variables

```bash
META_GRAPH_VERSION=v25.0                 # optional override; defaults to current Graph API path in automation
META_FITSEK_APP_ID=...
META_FITSEK_APP_SECRET=...
META_FITSEK_ACCESS_TOKEN_SHORT_TERM=...   # fresh user token
# Optional after discovery/exchange:
META_FITSEK_LONG_USER_ACCESS_TOKEN=...
META_FITSEK_PAGE_ACCESS_TOKEN=...
META_FITSEK_PAGE_ID=...
META_FITSEK_IG_USER_ID=...
META_FITSEK_ASSET_BASE_URL=https://raw.githubusercontent.com/eizoefoer/fitsek/main/site/assets/social
```

Required permissions for Facebook Page preparation/scheduling:

- `pages_show_list`
- `pages_manage_posts`
- `pages_read_engagement`

Required for Instagram publishing:

- `instagram_basic`
- `instagram_content_publish`

## Commands

```bash
python3 automation/meta_autopilot.py check
python3 automation/meta_autopilot.py permissions  # safe App Review/API path diagnostic
python3 automation/meta_autopilot.py refresh --write-env   # exchange a fresh short token and persist page/IG IDs
python3 automation/meta_token_watch.py --quiet-ok          # silent when healthy; alerts when re-auth/action is required
python3 automation/meta_autopilot.py prepare --days 21 --posts-per-day 3
python3 automation/social_copy.py audit --days 21
python3 automation/meta_autopilot.py fb-draft --days 21 --posts-per-day 3        # dry run
python3 automation/meta_autopilot.py fb-schedule --days 21 --posts-per-day 3    # dry run
python3 automation/meta_autopilot.py ig-plan --days 7 --posts-per-day 3
python3 automation/meta_ig_publisher.py plan --days 7 --posts-per-day 3 --overwrite
python3 automation/meta_ig_publisher.py status
python3 automation/meta_ig_publisher.py publish-due --confirm  # cron/wrapper path; publishes only due IG posts
python3 automation/verify_posts.py --json --window-hours 6     # check live/scheduled FB + IG state
```

## Token/watchdog note

Meta does not provide a standard OAuth refresh token for this flow. `automation/meta_token_watch.py` keeps the saved long-lived user/page tokens validated, attempts allowed token exchange when Meta permits it, and alerts before/manual re-auth is required. Hermes cron job `Fitsek Meta Token Watch` runs this daily and stays silent while healthy.

## Current verified state (2026-07-08)

- Facebook Page found: `FitSek` (`100185022163250`), category `Shopping & retail`, Page tasks include `CREATE_CONTENT`.
- Current token grants all required Facebook/Instagram publish permissions checked by the script: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, and `instagram_content_publish`.
- Public copy is generated through `automation/social_copy.py`; `python3 automation/social_copy.py audit --days 21` must pass before Meta scheduling. This prevents internal labels such as `CTA:` and repetitive boilerplate from reaching public posts.
- Current weekly social-manager rhythm: 3 unique posts per day at 09:00, 13:00, and 17:00 AEST, using the first 21 calendar rows for the 7-day batch.
- Instagram Page linkage is API-visible: `@fitsek.wellness` (`17841443568404793`) is returned as the FitSek Page `instagram_business_account`.
- Instagram uses a recurring no-agent due-check cron (`Fitsek IG Publish Due Check`, every 15 minutes) that runs `~/.hermes/scripts/fitsek_ig_publish_due.sh`. The publisher stays silent when no post is due and prints returned media IDs only when it publishes.
- `Fitsek Social Publish Verification` runs `~/.hermes/scripts/fitsek_social_verify.sh` every 30 minutes. It is silent on OK and alerts if a due FB/IG post is missing after the grace window or Meta API verification fails.

## Proper API path

The automation uses Graph API `v25.0` by default and can be overridden with `META_GRAPH_VERSION`.

After Meta App Review grants the required permissions and a fresh user token is generated:

1. `GET /me/accounts` discovers the FitSek Page, Page access token, and linked Instagram business account.
2. `POST /{page-id}/photos` with `published=false` creates Facebook Page review drafts.
3. `POST /{page-id}/photos` with `published=false` and `scheduled_publish_time` creates scheduled Facebook Page photo posts after approval.
4. Instagram publishing uses `POST /{ig-user-id}/media` followed by `POST /{ig-user-id}/media_publish`; it does not create persistent scheduled drafts in Meta Business Suite. `automation/meta_ig_publisher.py` handles approved future publishing by creating the media container only when a scheduled Hermes cron job fires.

Until `pages_manage_posts` is granted, `fb-draft --confirm` intentionally fails before calling the write endpoint and prints the App Review unblock path.

## Meta API limitation

The public Instagram Graph API can publish media, but it does not create persistent future-scheduled Instagram drafts inside Meta Business Suite. For approved future publishing, keep `var/meta_ig_schedule.json` as ignored runtime state and run a recurring due-check cron (`fitsek_ig_publish_due.sh`) every 15 minutes. The publisher creates the IG media container only when a scheduled post is due, then calls `media_publish`, avoiding container expiry. The publisher prefers committed `.jpg` siblings for generated `.png` social assets because Instagram's content publishing path is stricter about image media than Facebook.

Do **not** create one cron entry per calendar slot with five-field cron expressions such as `0 13 15 7 3`: cron can treat day-of-month and day-of-week as OR, which can fire on unintended dates. Use ISO one-shot schedules or the recurring due-check publisher instead.

**Note on Facebook scheduled posts:** In the Graph API, every organic post includes the flag `is_eligible_for_promotion: true`. This does **not** mean the post is running as an ad; it merely indicates the post can later be boosted into a paid campaign if you choose. The posts you scheduled via `fb-schedule` remain organic, unpublished until their scheduled time, and include the attached image/video you provided.
