#!/usr/bin/env python3
"""Build Fitsek's organic image/Reel/Story funnel plan without publishing it.

The Instagram API can publish images and Reels but Meta's current Content Publishing
API does not support Stories. Story rows are therefore explicit Business Suite work,
not fake API jobs. The resulting JSON is consumed by meta_ig_publisher.py and
verify_posts.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import social_copy

ROOT = Path(__file__).resolve().parents[1]
AEST = dt.timezone(dt.timedelta(hours=10), name="AEST")
DEFAULT_ASSET_BASE = "https://raw.githubusercontent.com/eizoefoer/fitsek/main/"
REEL_ASSETS = {
    "walking": "site/assets/social/profile-reels/with-audio/desk-walking-pad-reel-vo.mp4",
    "meal": "site/assets/social/profile-reels/with-audio/meal-prep-reel-vo.mp4",
    "gym": "site/assets/social/profile-reels/with-audio/gym-progression-reel-vo.mp4",
}
# One daily feed item plus one Story: three Reels and four feed images each week.
WEEKLY_SEQUENCE = (
    ("reel", 3, "walking"),
    ("feed_image", 8, None),
    ("reel", 9, "meal"),
    ("feed_image", 11, None),
    ("reel", 4, "gym"),
    ("feed_image", 12, None),
    ("feed_image", 13, None),
)
STORY_PROMPTS = (
    "Story 1: desk-day movement poll; Story 2: show the one small action; Link sticker to fitsek.com/go.",
    "Story 1: checklist slider; Story 2: invite a saved reset; Link sticker to fitsek.com/go.",
    "Story 1: meal-template question box; Story 2: repeatable plate reminder; Link sticker to fitsek.com/go.",
    "Story 1: progression poll; Story 2: one-lift tracking prompt; Link sticker to fitsek.com/go.",
    "Story 1: weekly check-in slider; Story 2: choose one lever; Link sticker to fitsek.com/go.",
    "Story 1: workday friction question; Story 2: simple next step; Link sticker to fitsek.com/go.",
    "Story 1: Sunday plan prompt; Story 2: invite the free reset; Link sticker to fitsek.com/go.",
)


def as_utc(date: dt.date, hour: int, minute: int = 0) -> tuple[int, str, str]:
    local = dt.datetime.combine(date, dt.time(hour, minute), tzinfo=AEST)
    utc = local.astimezone(dt.timezone.utc)
    return int(utc.timestamp()), utc.isoformat(), local.isoformat()


def asset_url(asset_path: str, base: str) -> str:
    return base.rstrip("/") + "/" + asset_path.lstrip("/")


def row_by_day() -> dict[int, dict[str, str]]:
    return {int(row["day"]): row for row in social_copy.read_calendar()}


def build_plan(days: int, start_date: dt.date, asset_base: str = DEFAULT_ASSET_BASE) -> dict:
    if days < 1:
        raise ValueError("days must be at least one")
    rows = row_by_day()
    posts: list[dict] = []
    for offset in range(days):
        date = start_date + dt.timedelta(days=offset)
        format_name, asset_day, reel_key = WEEKLY_SEQUENCE[offset % len(WEEKLY_SEQUENCE)]
        row = rows[asset_day]
        timestamp, iso_utc, iso_aest = as_utc(date, 9)
        title = social_copy.title_key(row)
        if format_name == "reel":
            asset_path = REEL_ASSETS[str(reel_key)]
            media_type = "REELS"
            funnel_stage = "consideration"
        else:
            asset_path = f"site/assets/social/post-{asset_day:02d}.jpg"
            media_type = "IMAGE"
            funnel_stage = "awareness"
        posts.append(
            {
                "plan_id": f"ig-{date.isoformat()}-feed",
                "day": asset_day,
                "title": title,
                "format": format_name,
                "media_type": media_type,
                "publication_mode": "instagram_graph_api",
                "funnel_stage": funnel_stage,
                "asset_path": asset_path,
                "asset_url": asset_url(asset_path, asset_base),
                "caption": social_copy.polished_caption(row, "instagram"),
                "destination_url": social_copy.INSTAGRAM_BIO_URL,
                "link_in_bio": social_copy.INSTAGRAM_BIO_URL,
                "scheduled_publish_time_utc": timestamp,
                "scheduled_publish_time_iso_utc": iso_utc,
                "scheduled_publish_time_aest": iso_aest,
                "status": "scheduled",
            }
        )
        story_timestamp, story_iso_utc, story_iso_aest = as_utc(date, 18)
        story_asset = REEL_ASSETS["walking" if offset % 2 == 0 else "meal"]
        posts.append(
            {
                "plan_id": f"ig-{date.isoformat()}-story",
                "day": asset_day,
                "title": f"{title} story companion",
                "format": "story",
                "media_type": "STORY",
                "publication_mode": "business_suite_manual",
                "funnel_stage": "engagement_to_lead",
                "asset_path": story_asset,
                "asset_url": asset_url(story_asset, asset_base),
                "story_brief": STORY_PROMPTS[offset % len(STORY_PROMPTS)],
                "destination_url": social_copy.INSTAGRAM_BIO_URL,
                "scheduled_publish_time_utc": story_timestamp,
                "scheduled_publish_time_iso_utc": story_iso_utc,
                "scheduled_publish_time_aest": story_iso_aest,
                "status": "manual_scheduled",
            }
        )
    return {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": "mixed_format_funnel_v1",
        "timezone": "Australia/Brisbane",
        "calendar_days": days,
        "cadence": "one image-or-Reel at 09:00 AEST and one Story at 18:00 AEST daily",
        "format_mix": {"feed_image": sum(p["format"] == "feed_image" for p in posts), "reel": sum(p["format"] == "reel" for p in posts), "story": sum(p["format"] == "story" for p in posts)},
        "story_api_limit": "Instagram Content Publishing API does not support Stories; publish these rows in Business Suite and mark them published in the ledger.",
        "posts": posts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--start-date", help="YYYY-MM-DD in AEST; defaults to tomorrow")
    parser.add_argument("--asset-base-url", default=DEFAULT_ASSET_BASE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    start = dt.date.fromisoformat(args.start_date) if args.start_date else dt.datetime.now(AEST).date() + dt.timedelta(days=1)
    plan = build_plan(args.days, start, args.asset_base_url)
    text = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
