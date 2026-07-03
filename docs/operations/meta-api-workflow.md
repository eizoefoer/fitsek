# Fitsek Meta API Workflow

## Current publishing policy

- First 30 days: approval-first. Create drafts/outbox and review before posting.
- After 30 days: full auto-posting can be enabled only after explicit approval.
- Never bypass Meta app review or use unapproved permissions.
- Store tokens in `~/.hermes/.env`, never in git.

## Required environment variables

```bash
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

## Current verified state (2026-07-03)

- Facebook Page found: `FitSek` (`100185022163250`), category `Shopping & retail`, Page tasks include `CREATE_CONTENT`.
- Linked Instagram Business Account was not returned by the API (`ig_user: null`): either the IG account is not linked to the Page/Business asset or the token lacks IG permissions.
- Current token grants `pages_show_list` and `pages_read_engagement`, but not `pages_manage_posts`; Meta rejected draft creation with `(#200) pages_manage_posts ... need to be approved by App Review`.
- Next unblock: grant/request `pages_manage_posts`, `instagram_basic`, and `instagram_content_publish`, then run `refresh --write-env` and `fb-draft --confirm` again.

## Meta API limitation

The public Instagram Graph API can publish media, but it does not create persistent future-scheduled Instagram drafts inside Meta Business Suite. For the first 30 days, use the generated outbox/assets for final manual schedule approval. After explicit approval, a cron publisher can post at the scheduled times.
