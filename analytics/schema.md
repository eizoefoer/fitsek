# Fitsek Analytics Schema

## First-party events (`/var/lib/fitsek/events.jsonl`)
- `received_at`
- `type`: page_view, click, signup, signup_success, signup_error, etc.
- `label`
- `path`
- `href`
- `utm`
- `referrer`
- `ip_hash`
- `user_agent_hash`

## Leads (`/var/lib/fitsek/leads.jsonl`)
- `received_at`
- `email`
- `lead_magnet`
- `utm`
- `consent`
- hashed IP/user-agent metadata

## Manual social metrics
Track in `analytics/manual_social_metrics.csv` until API permissions are stable and approved.
