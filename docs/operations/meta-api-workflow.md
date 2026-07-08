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
python3 automation/meta_autopilot.py prepare --days 7
python3 automation/meta_autopilot.py fb-draft --days 7        # dry run
python3 automation/meta_autopilot.py fb-draft --days 7 --confirm
python3 automation/meta_autopilot.py fb-schedule --days 7     # dry run
python3 automation/meta_autopilot.py ig-plan --days 7
python3 automation/meta_ig_publisher.py plan --days 7 --overwrite
python3 automation/meta_ig_publisher.py status
python3 automation/meta_ig_publisher.py publish-due --confirm  # cron/wrapper path; publishes only due IG posts
```

## Token/watchdog note

Meta does not provide a standard OAuth refresh token for this flow. `automation/meta_token_watch.py` keeps the saved long-lived user/page tokens validated, attempts allowed token exchange when Meta permits it, and alerts before/manual re-auth is required. Hermes cron job `Fitsek Meta Token Watch` runs this daily and stays silent while healthy.

## Current verified state (2026-07-08)

- Facebook Page found: `FitSek` (`100185022163250`), category `Shopping & retail`, Page tasks include `CREATE_CONTENT`.
- Current token grants all required Facebook/Instagram publish permissions checked by the script: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, and `instagram_content_publish`.
- 7 Facebook Page photo posts were scheduled via Graph API for 2026-07-09 through 2026-07-15 at 19:30 AEST. `/scheduled_posts` verification returned 7 unpublished scheduled posts.
- Instagram Page linkage is now API-visible: `@fitsek.wellness` (`17841443568404793`) is returned as the FitSek Page `instagram_business_account`.
- 7 Instagram posts are scheduled through Hermes one-shot cron jobs at 19:30 AEST from 2026-07-09 through 2026-07-15. The durable local schedule is ignored runtime state at `var/meta_ig_schedule.json`; each job runs `~/.hermes/scripts/fitsek_ig_publish_due.sh`, which calls `automation/meta_ig_publisher.py publish-due --confirm --wait-seconds 180` and prints the returned Instagram media ID only when a post is actually published.

## Proper API path

The automation uses Graph API `v25.0` by default and can be overridden with `META_GRAPH_VERSION`.

After Meta App Review grants the required permissions and a fresh user token is generated:

1. `GET /me/accounts` discovers the FitSek Page, Page access token, and linked Instagram business account.
2. `POST /{page-id}/photos` with `published=false` creates Facebook Page review drafts.
3. `POST /{page-id}/photos` with `published=false` and `scheduled_publish_time` creates scheduled Facebook Page photo posts after approval.
4. Instagram publishing uses `POST /{ig-user-id}/media` followed by `POST /{ig-user-id}/media_publish`; it does not create persistent scheduled drafts in Meta Business Suite. `automation/meta_ig_publisher.py` handles approved future publishing by creating the media container only when a scheduled Hermes cron job fires.

Until `pages_manage_posts` is granted, `fb-draft --confirm` intentionally fails before calling the write endpoint and prints the App Review unblock path.

## Meta API limitation

The public Instagram Graph API can publish media, but it does not create persistent future-scheduled Instagram drafts inside Meta Business Suite. For approved future publishing, keep `var/meta_ig_schedule.json` as ignored runtime state and use one-shot Hermes cron jobs that run `fitsek_ig_publish_due.sh` at the approved times. The publisher creates the IG media container at publish time, then calls `media_publish`, avoiding container expiry. The publisher prefers committed `.jpg` siblings for generated `.png` social assets because Instagram's content publishing path is stricter about image media than Facebook.
