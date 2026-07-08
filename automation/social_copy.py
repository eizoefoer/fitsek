#!/usr/bin/env python3
"""Fitsek social copy polish gate.

Turns the raw content calendar into public-facing Facebook/Instagram copy.
The goal is to stop internal labels like "CTA:" and repetitive AI-ish
boilerplate from reaching scheduled posts.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import unicodedata
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CALENDAR = ROOT / "content/social/30-day-calendar.csv"
AEST = dt.timezone(dt.timedelta(hours=10), name="AEST")
DEFAULT_SLOTS = [(9, 0), (13, 0), (17, 0)]
DISCLAIMER = "General fitness education only. Results vary."
HASHTAGS = "#deskworkerfitness #bodyrecomposition #fatlossbasics #walkingpad #highprotein #fitsek"

BODY_COPY: dict[str, str] = {
    "Desk Worker Recomp Mistake": """Your week has meetings, commutes, late meals and low-energy days. The plan has to fit that, not fight it.

Start with the boring base:
- 2 strength sessions
- daily steps you can actually repeat
- 2 protein anchors
- one honest weekly review

Small enough to repeat beats perfect once.""",
    "2-Meal Protein Fix": """If appetite is low, six meals usually makes the plan harder.

Start with two reliable protein anchors instead:
- one earlier in the day
- one later in the day
- easy carbs and colour around them
- no complicated meal prep needed

Make the default meal obvious before you chase a perfect diet.""",
    "Walking Pad Protocol": """The walking pad works when it becomes boring.

Try this setup:
- 10 minutes after one meal
- one easy meeting walk
- one short block before you shut the laptop

Keep the pace easy. The win is showing up often enough that steps stop feeling like a separate task.""",
    "Gym Progression Rule": """Random hard sets feel productive, but they make progress hard to see.

Pick one simple rule for the next 4 weeks:
- same main lifts
- same rep range
- add reps before load
- stop 1-2 reps before form falls apart

You do not need a new workout every Monday. You need evidence that the old one is moving.""",
    "Why the Scale Lied This Week": """One weigh-in can lie. A week of behaviour tells you more.

Before you panic, check:
- did steps hold?
- did protein land?
- did training happen?
- did sleep or stress spike?

If the actions are stable, review the trend instead of punishing yourself for one number.""",
    "Low Appetite Muscle Gain": """Low appetite is a friction problem first.

Make eating easier before you try to eat more:
- keep one repeatable breakfast or lunch
- use liquid calories when chewing feels like a chore
- add protein to food you already eat
- keep snacks visible, not theoretical

Small upgrades count when they happen every day.""",
    "What I’d Do Starting at 25–30% Body Fat": """At 25-30% body fat, the worst move is usually the harshest one.

Before cutting hard, build the base:
- lift 2-3 times a week
- walk most days
- hit two protein anchors
- review the week honestly

Small plan first. Bigger changes later.""",
    "Save This Recomp Checklist": """Use this before you change the whole plan.

Ask four questions:
- did I train?
- did I walk?
- did I hit protein anchors?
- did I review the week without guessing?

If one answer is missing, fix that first.""",
    "1-Minute Meal Template": """When the day is busy, do not start from recipes.

Use a simple plate:
- protein anchor
- easy carb
- fruit or veg
- sauce you actually like

The meal does not need to be impressive. It needs to be repeatable on a work day.""",
    "Sunday Recomp Check-In": """Your Sunday check-in should not become a life reset.

Look at the week, choose one lever, and leave the rest alone:
- steps
- protein anchors
- training consistency
- sleep window

One clear change is easier to measure than five emotional ones.""",
}

VISUAL_HOOKS: dict[str, str] = {
    "Desk Worker Recomp Mistake": "Stop copying plans built for someone else's week.",
    "2-Meal Protein Fix": "Low appetite? Start with two protein anchors.",
    "Walking Pad Protocol": "Make steps boring enough to repeat.",
    "Gym Progression Rule": "Use one progression rule for 4 weeks.",
    "Why the Scale Lied This Week": "One weigh-in is not the whole story.",
    "Low Appetite Muscle Gain": "Make eating easier before eating more.",
    "What I’d Do Starting at 25–30% Body Fat": "Skip the crash diet. Build the base first.",
    "Save This Recomp Checklist": "Check the basics before changing everything.",
    "1-Minute Meal Template": "Build a desk-day meal without overthinking it.",
    "Sunday Recomp Check-In": "Change one lever, not your whole life.",
}

VISUAL_TITLES: dict[str, str] = {
    "Desk Worker Recomp Mistake": "Desk-worker recomp mistake",
    "2-Meal Protein Fix": "2-meal protein fix",
    "Walking Pad Protocol": "Walking pad protocol",
    "Gym Progression Rule": "Simple gym progression",
    "Why the Scale Lied This Week": "Why the scale jumped",
    "Low Appetite Muscle Gain": "Low-appetite muscle gain",
    "What I’d Do Starting at 25–30% Body Fat": "Starting at 25-30% body fat?",
    "Save This Recomp Checklist": "Save this recomp checklist",
    "1-Minute Meal Template": "1-minute meal template",
    "Sunday Recomp Check-In": "Sunday recomp check-in",
}

CTA_COPY: dict[str, str] = {
    "download": "Get the free 7-Day Desk Worker Recomp Reset:",
    "join": "Join the Fitsek list:",
    "waitlist": "Join the 12-week system waitlist:",
    "save": "Save this for your next check-in.",
    "comment": "Want the starter reset? Comment RESET.",
    "share": "Share this with a desk worker who needs a simpler plan.",
}

BAD_PUBLIC_PATTERNS = [
    re.compile(r"\bCTA\s*:", re.I),
    re.compile(r"Fitsek rule\s*:", re.I),
    re.compile(r"honest tracking\s*—\s*not perfection", re.I),
    re.compile(r"I would not", re.I),
    re.compile(r"\(Posted at \d{2}:\d{2} AEST\)", re.I),
]


def read_calendar(path: Path = CALENDAR) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def title_key(row: dict[str, str]) -> str:
    return (row.get("post_title") or row.get("title") or "").strip()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.replace("%", "pct")
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return normalized or "fitsek-post"


def destination_url(row: dict[str, str], platform: str) -> str:
    day = int(row.get("day") or 0)
    slug = slugify(title_key(row))
    source = "instagram" if platform.lower().startswith("inst") else "facebook"
    return f"https://fitsek.com/?utm_source={source}&utm_medium=social&utm_campaign=day{day:02d}_{slug}"


def cta_key(raw: str) -> str:
    value = (raw or "").lower()
    if "comment" in value:
        return "comment"
    if "waitlist" in value or "12-week" in value:
        return "waitlist"
    if "download" in value or "free" in value:
        return "download"
    if "join" in value or "list" in value:
        return "join"
    if "save" in value:
        return "save"
    if "share" in value:
        return "share"
    return "download"


def cta_text(row: dict[str, str], platform: str) -> str:
    key = cta_key(row.get("cta", ""))
    line = CTA_COPY[key]
    if platform.lower().startswith("inst"):
        if key in {"download", "join", "waitlist"}:
            return f"{line}\nLink in bio: fitsek.com"
        return line
    if key in {"download", "join", "waitlist"}:
        return f"{line}\n{destination_url(row, platform)}"
    # For social actions, still leave a clean path for high-intent readers.
    return f"{line}\nfitsek.com"


def visual_hook(row: dict[str, str]) -> str:
    return VISUAL_HOOKS.get(title_key(row), (row.get("hook") or "").strip())


def visual_title(row: dict[str, str]) -> str:
    return VISUAL_TITLES.get(title_key(row), title_key(row))


def polished_caption(row: dict[str, str], platform: str) -> str:
    title = title_key(row)
    hook = visual_hook(row).rstrip(".") + "."
    body = BODY_COPY.get(title)
    if not body:
        body = (row.get("caption") or row.get("hook") or "").strip()
        body = re.sub(r"Fitsek rule:.*?(General fitness education only; results vary\.)?", "", body, flags=re.I | re.S).strip()
    parts = [hook, body.strip(), cta_text(row, platform), HASHTAGS, DISCLAIMER]
    return "\n\n".join(part for part in parts if part).strip()


def first_schedulable_date(slots: list[tuple[int, int]] | None = None, min_buffer_minutes: int = 10) -> dt.date:
    slots = slots or DEFAULT_SLOTS
    now = dt.datetime.now(AEST)
    min_time = now + dt.timedelta(minutes=min_buffer_minutes)
    for hour, minute in slots:
        candidate = dt.datetime.combine(now.date(), dt.time(hour, minute), tzinfo=AEST)
        if candidate > min_time:
            return now.date()
    return now.date() + dt.timedelta(days=1)


def schedule_datetime_for_index(index: int, posts_per_day: int = 3, slots: list[tuple[int, int]] | None = None) -> dt.datetime:
    slots = slots or DEFAULT_SLOTS
    posts_per_day = max(1, min(posts_per_day, len(slots)))
    slot_index = index % posts_per_day
    day_offset = index // posts_per_day
    local_date = first_schedulable_date(slots[:posts_per_day]) + dt.timedelta(days=day_offset)
    hour, minute = slots[slot_index]
    return dt.datetime.combine(local_date, dt.time(hour, minute), tzinfo=AEST).astimezone(dt.timezone.utc)


def schedule_timestamp_for_index(index: int, posts_per_day: int = 3) -> int:
    return int(schedule_datetime_for_index(index, posts_per_day).timestamp())


def audit_rows(rows: Iterable[dict[str, str]], days: int | None = None) -> tuple[list[dict], list[dict]]:
    subset = list(rows)[:days] if days else list(rows)
    previews = []
    issues = []
    for row in subset:
        item = {"day": row.get("day"), "title": title_key(row)}
        for platform in ("facebook", "instagram"):
            text = polished_caption(row, platform)
            item[f"{platform}_caption"] = text
            for pattern in BAD_PUBLIC_PATTERNS:
                if pattern.search(text):
                    issues.append({"day": row.get("day"), "title": title_key(row), "platform": platform, "issue": pattern.pattern})
            if platform == "instagram" and "utm_" in text:
                issues.append({"day": row.get("day"), "title": title_key(row), "platform": platform, "issue": "raw_utm_url_in_ig_caption"})
        previews.append(item)
    return previews, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("audit")
    p.add_argument("--days", type=int, default=21)
    p = sub.add_parser("preview")
    p.add_argument("--days", type=int, default=3)
    args = parser.parse_args()
    rows = read_calendar()
    previews, issues = audit_rows(rows, days=args.days)
    if args.cmd == "preview":
        print(json.dumps(previews, indent=2, ensure_ascii=False))
        return 0
    print(json.dumps({"checked": min(args.days, len(rows)), "issues": issues}, indent=2, ensure_ascii=False))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
