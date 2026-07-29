#!/usr/bin/env python3
"""Approval-triggered Instagram publisher for Fitsek.

Instagram Graph API cannot create durable future scheduled drafts in Meta Business
Suite. This script stores an approved local schedule and publishes due posts at
their approved times via media container + media_publish.

Secrets are read from ~/.hermes/.env and never printed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import social_copy

ROOT = Path(__file__).resolve().parents[1]
AUTOMATION_DIR = ROOT / "automation"
ENV_PATH = Path.home() / ".hermes" / ".env"
SCHEDULE_PATH = ROOT / "var" / "meta_ig_schedule.json"
STATE_PATH = ROOT / "var" / "meta_state.json"
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
    raw = env("META_GRAPH_VERSION") or DEFAULT_GRAPH_VERSION
    raw = raw.strip().lstrip("/")
    return raw if raw.startswith("v") else f"v{raw}"


def graph_url(path: str) -> str:
    return f"https://graph.facebook.com/{graph_version()}/{path.lstrip('/')}"


def urlencode(values: dict[str, object]) -> str:
    clean = {k: str(v) for k, v in values.items() if v is not None}
    return urllib.parse.urlencode(clean)


def graph(method: str, path: str, token: str, params: dict | None = None, data: dict | None = None) -> dict:
    params = dict(params or {})
    data = dict(data or {})
    if method == "GET":
        params["access_token"] = token
        req = urllib.request.Request(f"{graph_url(path)}?{urlencode(params)}")
    else:
        data["access_token"] = token
        req = urllib.request.Request(graph_url(path), data=urlencode(data).encode(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"Meta API error {exc.code}: {body}") from exc


def load_outbox_posts(days: int, posts_per_day: int = 3) -> list[dict]:
    sys.path.insert(0, str(AUTOMATION_DIR))
    import meta_autopilot  # type: ignore

    meta_autopilot.load_env()
    # In this script, days means calendar days. Build one unique post per slot.
    return meta_autopilot.build_outbox(days * posts_per_day, posts_per_day=posts_per_day)


def discover_ig_user_id() -> str:
    if env("META_FITSEK_IG_USER_ID"):
        return env("META_FITSEK_IG_USER_ID")
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text())
        ig = state.get("ig_user") or (state.get("selected_page") or {}).get("instagram_business_account") or {}
        if ig.get("id"):
            return str(ig["id"])
    raise SystemExit("No META_FITSEK_IG_USER_ID found. Run: python3 automation/meta_autopilot.py refresh --write-env && python3 automation/meta_autopilot.py check")


def publish_token() -> str:
    # The connected Page token is the normal token for Instagram Graph publishing.
    token = env("META_FITSEK_PAGE_ACCESS_TOKEN") or env("META_FITSEK_LONG_USER_ACCESS_TOKEN")
    if not token:
        raise SystemExit("No Meta publish token found in ~/.hermes/.env")
    return token


def iso_utc(ts: int | float) -> str:
    return dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc).isoformat()


def iso_aest(ts: int | float) -> str:
    return dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc).astimezone(AEST).isoformat()


def instagram_asset_url(item: dict) -> str:
    """Return an IG-safe public asset URL.

    Instagram content publishing is stricter than Facebook about image media;
    prefer committed JPG siblings for generated PNG social images when present.
    """
    asset_url = str(item["asset_url"])
    asset_path = str(item.get("asset_path") or "")
    local_path = ROOT / asset_path if asset_path else None
    if asset_url.lower().endswith(".png") and local_path and local_path.suffix.lower() == ".png":
        jpg_path = local_path.with_suffix(".jpg")
        if jpg_path.exists():
            return asset_url[:-4] + ".jpg"
    return asset_url


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_plan(days: int, overwrite: bool = False, posts_per_day: int = 3) -> dict:
    load_env()
    ig_user_id = discover_ig_user_id()
    if SCHEDULE_PATH.exists() and not overwrite:
        return json.loads(SCHEDULE_PATH.read_text())
    posts = load_outbox_posts(days, posts_per_day=posts_per_day)
    plan = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": "ig_graph_scheduled_cron_publish",
        "graph_version": graph_version(),
        "ig_user_id": ig_user_id,
        "schedule_path": str(SCHEDULE_PATH),
        "calendar_days": days,
        "posts_per_day": posts_per_day,
        "copy_polished": True,
        "note": "Instagram Graph API has no durable future scheduled drafts; approved posts are published by Hermes cron at scheduled times.",
        "posts": [],
    }
    for item in posts:
        ts = int(item["suggested_scheduled_publish_time_utc"])
        day = int(item["day"])
        # Instagram does not render caption URLs as reliably as a bio/comment link.
        # Keep a clean link-in-bio CTA in every caption and post a tracked direct
        # link as the first comment after the media is live.
        caption = str(item["instagram_caption"])
        if "link in bio" not in caption.lower():
            caption = f"{caption}\n\nMore desk-worker fitness tools: Link in bio: fitsek.com"
        slug = social_copy.slugify(str(item.get("title") or f"fitsek-day-{day}"))
        comment = (
            "Start here → "
            f"https://fitsek.com/?utm_source=instagram&utm_medium=comment&utm_campaign=day{day:02d}_{slug}"
        )
        plan["posts"].append(
            {
                "day": day,
                "title": item.get("title"),
                "asset_url": instagram_asset_url(item),
                "source_asset_url": item["asset_url"],
                "asset_path": item.get("asset_path"),
                "caption": caption,
                "link_in_bio": "https://fitsek.com/",
                "comment": comment,
                "scheduled_publish_time_utc": ts,
                "scheduled_publish_time_iso_utc": iso_utc(ts),
                "scheduled_publish_time_aest": iso_aest(ts),
                "status": "scheduled",
            }
        )
    write_json(SCHEDULE_PATH, plan)
    return plan


def load_plan() -> dict:
    load_env()
    if not SCHEDULE_PATH.exists():
        return make_plan(days=7, overwrite=False)
    return json.loads(SCHEDULE_PATH.read_text())


def save_plan(plan: dict) -> None:
    plan["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(SCHEDULE_PATH, plan)


def summarize(plan: dict) -> dict:
    posts = plan.get("posts", [])
    counts: dict[str, int] = {}
    for post in posts:
        counts[post.get("status", "unknown")] = counts.get(post.get("status", "unknown"), 0) + 1
    return {
        "mode": plan.get("mode"),
        "ig_user_id": plan.get("ig_user_id"),
        "schedule_path": str(SCHEDULE_PATH),
        "count": len(posts),
        "counts": counts,
        "posts": [
            {
                "day": p.get("day"),
                "title": p.get("title"),
                "scheduled_publish_time_aest": p.get("scheduled_publish_time_aest"),
                "status": p.get("status"),
                "published_media_id": p.get("published_media_id"),
            }
            for p in posts
        ],
    }


def wait_for_container(container_id: str, token: str, timeout_seconds: int = 120) -> dict:
    deadline = time.time() + timeout_seconds
    last = {}
    while True:
        last = graph("GET", container_id, token, params={"fields": "id,status_code,status"})
        status_code = last.get("status_code")
        if status_code in {"FINISHED", "ERROR", "EXPIRED"}:
            return last
        if time.time() >= deadline:
            return last
        time.sleep(5)


def publish_post(post: dict, ig_user_id: str, token: str, container_timeout: int) -> dict:
    media_type = str(post.get("media_type") or "IMAGE").upper()
    if media_type == "REELS":
        payload = {
            "media_type": "REELS",
            "video_url": post["asset_url"],
            "caption": post["caption"],
            "share_to_feed": "true",
        }
    elif media_type == "IMAGE":
        payload = {"image_url": post["asset_url"], "caption": post["caption"]}
    else:
        raise ValueError(f"Unsupported Instagram media_type for day {post.get('day')}: {media_type}")
    container = graph(
        "POST",
        f"{ig_user_id}/media",
        token,
        data=payload,
    )
    container_id = container.get("id")
    if not container_id:
        raise RuntimeError(f"Meta did not return an Instagram media container id for day {post.get('day')}: {container}")
    post["container_id"] = container_id
    post["container_created_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    status = wait_for_container(container_id, token, timeout_seconds=container_timeout)
    post["container_status"] = status
    if status.get("status_code") not in {None, "FINISHED"}:
        raise RuntimeError(f"Instagram media container {container_id} not ready for day {post.get('day')}: {status}")
    published = graph("POST", f"{ig_user_id}/media_publish", token, data={"creation_id": container_id})
    media_id = published.get("id")
    if not media_id:
        raise RuntimeError(f"Meta did not return a published Instagram media id for day {post.get('day')}: {published}")
    post["published_media_id"] = media_id
    post["published_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    comment_id = None
    comment = str(post.get("comment") or "").strip()
    if comment:
        try:
            posted_comment = graph("POST", f"{media_id}/comments", token, data={"message": comment})
            comment_id = posted_comment.get("id")
            if not comment_id:
                raise RuntimeError(f"Meta did not return an Instagram comment id: {posted_comment}")
            post["comment_id"] = comment_id
            post["comment_posted_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        except Exception as exc:
            # The media itself is live. Preserve the retryable comment failure rather
            # than marking the content unpublished or attempting a duplicate publish.
            post["comment_error"] = str(exc)
            post["comment_error_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    post["status"] = "published"
    return {
        "day": post.get("day"),
        "title": post.get("title"),
        "container_id": container_id,
        "published_media_id": media_id,
        "comment_id": comment_id,
    }


def publish_due(confirm: bool, wait_seconds: int, container_timeout: int, verbose: bool = False) -> int:
    plan = load_plan()
    ig_user_id = str(plan.get("ig_user_id") or discover_ig_user_id())
    token = publish_token()
    now = int(time.time())
    pending = [p for p in plan.get("posts", []) if p.get("status") != "published"]
    due = [p for p in pending if int(p["scheduled_publish_time_utc"]) <= now]
    if not due and wait_seconds > 0:
        future = sorted(pending, key=lambda p: int(p["scheduled_publish_time_utc"]))
        if future:
            seconds_until = int(future[0]["scheduled_publish_time_utc"]) - now
            if 0 < seconds_until <= wait_seconds:
                time.sleep(seconds_until)
                now = int(time.time())
                due = [p for p in pending if int(p["scheduled_publish_time_utc"]) <= now]
    if not due:
        if verbose:
            print(json.dumps({"published": [], "note": "No due Instagram posts."}, indent=2))
        return 0
    if not confirm:
        print(json.dumps({"dry_run_due": [{"day": p.get("day"), "title": p.get("title")} for p in due]}, indent=2))
        return 0
    published = []
    errors = []
    for post in due:
        try:
            published.append(publish_post(post, ig_user_id, token, container_timeout=container_timeout))
            save_plan(plan)
        except Exception as exc:  # Save exact non-secret failure for resume.
            post["status"] = "error"
            post["last_error"] = str(exc)
            post["last_error_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            errors.append({"day": post.get("day"), "title": post.get("title"), "error": str(exc)})
            save_plan(plan)
            break
    result = {"published": published, "errors": errors, "schedule_path": str(SCHEDULE_PATH)}
    print(json.dumps(result, indent=2))
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--days", type=int, default=7, help="Calendar days to schedule")
    p.add_argument("--posts-per-day", type=int, default=3)
    p.add_argument("--overwrite", action="store_true")
    sub.add_parser("status")
    p = sub.add_parser("publish-due")
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--wait-seconds", type=int, default=0)
    p.add_argument("--container-timeout", type=int, default=120)
    p.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if args.cmd == "plan":
        print(json.dumps(summarize(make_plan(args.days, overwrite=args.overwrite, posts_per_day=args.posts_per_day)), indent=2))
        return 0
    if args.cmd == "status":
        print(json.dumps(summarize(load_plan()), indent=2))
        return 0
    if args.cmd == "publish-due":
        return publish_due(args.confirm, args.wait_seconds, args.container_timeout, args.verbose)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
