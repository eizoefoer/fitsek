#!/usr/bin/env python3
"""Small weekly readout for Fitsek's organic format mix and funnel routing."""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "var" / "meta_ig_schedule.json"
REPORTS = ROOT / "analytics" / "reports"


def readout(plan_path: Path = PLAN) -> dict:
    if not plan_path.exists():
        return {"available": False, "reason": "No Instagram schedule ledger yet."}
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    posts = plan.get("posts", [])
    return {
        "available": True,
        "mode": plan.get("mode"),
        "total": len(posts),
        "format": dict(collections.Counter(str(p.get("format", p.get("media_type", "unknown")).lower()) for p in posts)),
        "status": dict(collections.Counter(str(p.get("status", "unknown")) for p in posts)),
        "funnel_stage": dict(collections.Counter(str(p.get("funnel_stage", "unspecified")) for p in posts)),
        "publication_mode": dict(collections.Counter(str(p.get("publication_mode", "instagram_graph_api")) for p in posts)),
        "bio_route": "https://fitsek.com/go",
        "manual_story_note": plan.get("story_api_limit"),
    }


def markdown(data: dict) -> str:
    if not data["available"]:
        return "# Fitsek social format + funnel readout\n\nNo schedule ledger is available yet.\n"
    lines = ["# Fitsek social format + funnel readout", "", f"- Plan mode: `{data['mode']}`", f"- Planned items: {data['total']}", f"- Bio route: {data['bio_route']}", ""]
    for label in ("format", "status", "funnel_stage", "publication_mode"):
        lines += [f"## {label.replace('_', ' ').title()}", ""]
        lines += [f"- {key}: {value}" for key, value in sorted(data[label].items())]
        lines.append("")
    if data.get("manual_story_note"):
        lines += ["## Story control", "", data["manual_story_note"], ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = readout()
    text = markdown(data)
    if args.write:
        REPORTS.mkdir(parents=True, exist_ok=True)
        week = dt.date.today().isocalendar()
        (REPORTS / f"social-format-{week.year}-W{week.week:02d}.md").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
