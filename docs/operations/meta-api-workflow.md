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
```

## Token/watchdog note

Meta does not provide a standard OAuth refresh token for this flow. `automation/meta_token_watch.py` keeps the saved long-lived user/page tokens validated, attempts allowed token exchange when Meta permits it, and alerts before/manual re-auth is required. Hermes cron job `Fitsek Meta Token Watch` runs this daily and stays silent while healthy.

## Current verified state (2026-07-08)

- Facebook Page found: `FitSek` (`100185022163250`), category `Shopping & retail`, Page tasks include `CREATE_CONTENT`.
- Current token grants all required Facebook/Instagram publish permissions checked by the script: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, and `instagram_content_publish`.
- 7 Facebook Page photo posts were scheduled via Graph API for 2026-07-09 through 2026-07-15 at 19:30 AEST. `/scheduled_posts` verification returned 7 unpublished scheduled posts.
- Instagram asset `@fitsek.wellness` exists in Meta Business Settings under the FitSek business portfolio, but it is not yet connected to the FitSek Page for composer/API publishing: `/me/accounts?...instagram_business_account` returns `ig_user: null`, direct IG Graph lookup by the Business Settings ID fails, and Meta Business Suite composer still shows only Facebook plus “Connect Instagram”.
- Next IG unblock: in Meta Business Settings → Pages → FitSek → Connect assets → Instagram account → **Log into Instagram**, finish the manual login/authorization flow, then rerun `python3 automation/meta_autopilot.py refresh --write-env && python3 automation/meta_autopilot.py check`.

## Proper API path

The automation uses Graph API `v25.0` by default and can be overridden with `META_GRAPH_VERSION`.

After Meta App Review grants the required permissions and a fresh user token is generated:

1. `GET /me/accounts` discovers the FitSek Page, Page access token, and linked Instagram business account.
2. `POST /{page-id}/photos` with `published=false` creates Facebook Page review drafts.
3. `POST /{page-id}/photos` with `published=false` and `scheduled_publish_time` creates scheduled Facebook Page photo posts after approval.
4. Instagram publishing uses `POST /{ig-user-id}/media` followed by `POST /{ig-user-id}/media_publish`; it does not create persistent scheduled drafts in Meta Business Suite.

Until `pages_manage_posts` is granted, `fb-draft --confirm` intentionally fails before calling the write endpoint and prints the App Review unblock path.

## Meta API limitation

The public Instagram Graph API can publish media, but it does not create persistent future-scheduled Instagram drafts inside Meta Business Suite. For the first 30 days, use the generated outbox/assets for final manual schedule approval. After explicit approval, a cron publisher can post at the scheduled times.
