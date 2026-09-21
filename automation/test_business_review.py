#!/usr/bin/env python3
"""Regression coverage for time-bounded Fitsek business reviews."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))
import business_review


FIXED_NOW = datetime(2026, 9, 21, 9, 0, tzinfo=timezone.utc)


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW if tz else FIXED_NOW.replace(tzinfo=None)


class BusinessReviewWindowTests(unittest.TestCase):
    def test_daily_review_excludes_events_older_than_24_hours(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            events = [
                {"received_at": "2026-09-20T08:00:00Z", "type": "page_view", "utm": {}},
                {"received_at": "2026-09-21T08:00:00Z", "type": "page_view", "utm": {}},
            ]
            (data_dir / "events.jsonl").write_text(
                "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
            )
            (data_dir / "leads.jsonl").write_text("", encoding="utf-8")
            with patch.object(business_review, "DATA_DIR", data_dir), patch.object(
                business_review, "datetime", FixedDateTime
            ), patch.object(business_review, "check_url", return_value=(True, "200")):
                report = business_review.build_report("daily")

        self.assertIn("- Website/page events: 1", report)
        self.assertIn("## Reporting window", report)


if __name__ == "__main__":
    unittest.main()
