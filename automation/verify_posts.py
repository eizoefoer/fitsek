#!/usr/bin/env python3
"""Verify Fitsek Facebook and Instagram social posts.

Default mode prints a human-readable status. Cron mode (`--quiet --fail-on-missing-due`)
stays silent when everything is fine and exits non-zero only when a due post is missing
or an API check fails.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = Path.home() / ".hermes" / ".env"
IG_SCHEDULE_PATH = ROOT / "var/meta_ig_schedule.json"
FB_CREATED_PATH = ROOT / "var/meta_created_posts_last.json"
STATE_PATH = ROOT / "var/meta_state.json"
DEFAULT_GRAPH_VERSION = "v25.0"
AEST = dt.timezone(dt.timedelta(hours=10), name="AEST")


def load_env() -> None:
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def graph_version() -> str:
    raw = env("META_GRAPH_VERSION", DEFAULT_GRAPH_VERSION).lstrip("/")
    return raw if raw.startswith("v") else f"v{raw}"


def graph_url(path: str) -> str:
    return f"https://graph.facebook.com/{graph_version()}/{path.lstrip('/')}"


def graph_get(token: str, path: str, params: dict | None = None) -> dict:
    params = dict(params or {})
    params["access_token"] = token
    url = graph_url(path) + "?" + urllib.parse.urlencode({k: str(v) for k, v in params.items() if v is not None})
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            return json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"Meta API HTTP {exc.code} for {path}: {body[:800]}") from exc


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def resolve_ig_user_id(token: str) -> str:
    if env("META_FITSEK_IG_USER_ID"):
        return env("META_FITSEK_IG_USER_ID")
    state = load_json(STATE_PATH, {})
    ig = state.get("ig_user") or (state.get("selected_page") or {}).get("instagram_business_account") or {}
    if ig.get("id"):
        return str(ig["id"])
    data = graph_get(token, "me/accounts", {"fields": "instagram_business_account{id,username}", "limit": 100})
    for page in data.get("data", []):
        linked = page.get("instagram_business_account") or {}
        if linked.get("id"):
            return str(linked["id"])
    raise RuntimeError("Could not determine linked Instagram business account ID")


def ts_to_aest(ts: int | float | str | None) -> str | None:
    if ts is None:
        return None
    return dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc).astimezone(AEST).isoformat()


def check_fb(token: str, page_id: str, now: int, since: int, grace_seconds: int) -> dict:
    scheduled = graph_get(
        token,
        f"{page_id}/scheduled_posts",
        {"fields": "id,message,scheduled_publish_time,is_published,permalink_url", "limit": 100},
    ).get("data", [])
    recent = graph_get(
        token,
        f"{page_id}/posts",
        {"fields": "id,message,created_time,is_published,permalink_url", "since": since, "limit": 100},
    ).get("data", [])
    created = load_json(FB_CREATED_PATH, {"created": []}).get("created", [])
    scheduled_by_id = {p.get("id"): p for p in scheduled}
    missing_due = []
    checked_due = []
    for item in created:
        post_id = item.get("id")
        scheduled_ts = int(item.get("scheduled_publish_time_utc") or 0)
        if not scheduled_ts or scheduled_ts + grace_seconds > now:
            continue
        checked_due.append(post_id)
        if post_id in scheduled_by_id and not scheduled_by_id[post_id].get("is_published"):
            missing_due.append({"id": post_id, "title": item.get("title"), "scheduled_aest": ts_to_aest(scheduled_ts), "reason": "still_unpublished_in_scheduled_posts"})
    return {
        "scheduled_count": len(scheduled),
        "recent_count": len(recent),
        "checked_due_count": len(checked_due),
        "missing_due": missing_due,
        "recent": [
            {"id": p.get("id"), "created_time": p.get("created_time"), "message_preview": (p.get("message") or "")[:120], "permalink_url": p.get("permalink_url")}
            for p in recent[:10]
        ],
    }


def check_ig(token: str, ig_user_id: str, now: int, since: int, grace_seconds: int) -> dict:
    media = graph_get(
        token,
        f"{ig_user_id}/media",
        {"fields": "id,caption,timestamp,media_type,permalink,media_url", "since": since, "limit": 100},
    ).get("data", [])
    plan = load_json(IG_SCHEDULE_PATH, {"posts": []})
    missing_due = []
    link_issues = []
    checked_due = []
    media_ids = {m.get("id") for m in media if m.get("id")}
    for post in plan.get("posts", []):
        scheduled_ts = int(post.get("scheduled_publish_time_utc") or 0)
        if not scheduled_ts or scheduled_ts + grace_seconds > now:
            continue
        checked_due.append(post.get("title"))
        published_id = post.get("published_media_id")
        missing_reason = None
        if post.get("status") != "published":
            missing_reason = "not_marked_published"
        elif not published_id:
            missing_reason = "missing_published_media_id"
        elif scheduled_ts >= since and published_id not in media_ids:
            missing_reason = "published_media_id_not_in_recent_media"
        if missing_reason:
            missing_due.append({
                "day": post.get("day"),
                "title": post.get("title"),
                "scheduled_aest": ts_to_aest(scheduled_ts),
                "status": post.get("status"),
                "published_media_id": published_id,
                "reason": missing_reason,
            })
        elif post.get("comment") and not post.get("comment_id"):
            # A comment is link enrichment, not proof that the underlying media
            # failed to publish. Keep it visible in reports without making the
            # high-frequency post-delivery watchdog fail forever when Meta denies
            # optional instagram_manage_comments access.
            link_issues.append({
                "day": post.get("day"),
                "title": post.get("title"),
                "scheduled_aest": ts_to_aest(scheduled_ts),
                "published_media_id": published_id,
                "reason": "comment_not_posted" if not post.get("comment_error") else "comment_post_failed",
                "error": post.get("comment_error"),
            })
    return {
        "schedule_count": len(plan.get("posts", [])),
        "recent_count": len(media),
        "checked_due_count": len(checked_due),
        "missing_due": missing_due,
        "link_issues": link_issues,
        "recent": [
            {"id": m.get("id"), "timestamp": m.get("timestamp"), "media_type": m.get("media_type"), "caption_preview": (m.get("caption") or "")[:120], "permalink": m.get("permalink")}
            for m in media[:10]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-hours", type=float, default=4)
    parser.add_argument("--grace-minutes", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--fail-on-missing-due", action="store_true")
    args = parser.parse_args()

    load_env()
    token = env("META_FITSEK_PAGE_ACCESS_TOKEN") or env("META_FITSEK_LONG_USER_ACCESS_TOKEN")
    page_id = env("META_FITSEK_PAGE_ID")
    if not token or not page_id:
        raise SystemExit("Missing META_FITSEK_PAGE_ACCESS_TOKEN/META_FITSEK_PAGE_ID")

    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    since = now - int(args.window_hours * 3600)
    grace_seconds = args.grace_minutes * 60
    ig_user_id = resolve_ig_user_id(token)

    errors = []
    try:
        fb = check_fb(token, page_id, now, since, grace_seconds)
    except Exception as exc:
        fb = None
        errors.append({"platform": "facebook", "error": str(exc)})
    try:
        ig = check_ig(token, ig_user_id, now, since, grace_seconds)
    except Exception as exc:
        ig = None
        errors.append({"platform": "instagram", "error": str(exc)})

    missing = []
    if fb:
        missing.extend({"platform": "facebook", **item} for item in fb.get("missing_due", []))
    if ig:
        missing.extend({"platform": "instagram", **item} for item in ig.get("missing_due", []))

    report = {
        "checked_at_utc": dt.datetime.fromtimestamp(now, tz=dt.timezone.utc).isoformat(),
        "window_hours": args.window_hours,
        "grace_minutes": args.grace_minutes,
        "facebook": fb,
        "instagram": ig,
        "errors": errors,
        "missing_due": missing,
    }

    should_fail = bool(errors) or (args.fail_on_missing_due and bool(missing))
    if args.quiet and not should_fail:
        return 0
    if args.json or args.quiet:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=== Fitsek social verification ===")
        print(f"Checked: {report['checked_at_utc']}")
        print(f"Facebook: {fb['scheduled_count'] if fb else 'error'} scheduled, {fb['recent_count'] if fb else 'error'} recent")
        print(f"Instagram: {ig['schedule_count'] if ig else 'error'} scheduled, {ig['recent_count'] if ig else 'error'} recent")
        if missing:
            print("Missing due posts:")
            for item in missing:
                print(f"- {item}")
        elif not errors:
            print("No due-post gaps found.")
        if errors:
            print("Errors:")
            for error in errors:
                print(f"- {error}")
    return 1 if should_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
