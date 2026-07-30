#!/usr/bin/env python3
"""Regression tests for the rolling Instagram publish verifier."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from automation import verify_posts


class CheckInstagramPostsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.schedule_path = Path(self.tempdir.name) / "schedule.json"
        self.original_schedule_path = verify_posts.IG_SCHEDULE_PATH
        self.original_graph_get = verify_posts.graph_get
        verify_posts.IG_SCHEDULE_PATH = self.schedule_path

    def tearDown(self) -> None:
        verify_posts.IG_SCHEDULE_PATH = self.original_schedule_path
        verify_posts.graph_get = self.original_graph_get
        self.tempdir.cleanup()

    def test_historical_posts_do_not_require_recent_media_membership(self) -> None:
        now = 10_000
        self.schedule_path.write_text(json.dumps({"posts": [{
            "day": 1,
            "title": "Previously published",
            "scheduled_publish_time_utc": now - 86_400,
            "status": "published",
            "published_media_id": "old-media",
        }]}))
        verify_posts.graph_get = lambda *_args, **_kwargs: {"data": []}

        result = verify_posts.check_ig("token", "ig-user", now, now - 21_600, 1_800)

        self.assertEqual(0, result["checked_due_count"])
        self.assertEqual([], result["missing_due"])

    def test_flags_recent_due_published_id_absent_from_media_window(self) -> None:
        now = 10_000
        self.schedule_path.write_text(json.dumps({"posts": [{
            "day": 2,
            "title": "Recently due but absent",
            "scheduled_publish_time_utc": now - 3_600,
            "status": "published",
            "published_media_id": "missing-media",
        }]}))
        verify_posts.graph_get = lambda *_args, **_kwargs: {"data": []}

        result = verify_posts.check_ig("token", "ig-user", now, now - 21_600, 1_800)

        self.assertEqual(1, result["checked_due_count"])
        self.assertEqual(["Recently due but absent"], [item["title"] for item in result["missing_due"]])
        self.assertEqual("published_media_id_not_in_recent_media", result["missing_due"][0]["reason"])

    def test_due_post_requires_published_status_and_media_id(self) -> None:
        now = 10_000
        self.schedule_path.write_text(json.dumps({"posts": [
            {
                "day": 3,
                "title": "Still scheduled",
                "scheduled_publish_time_utc": now - 3_600,
                "status": "scheduled",
            },
            {
                "day": 4,
                "title": "Published without id",
                "scheduled_publish_time_utc": now - 3_600,
                "status": "published",
            },
        ]}))
        verify_posts.graph_get = lambda *_args, **_kwargs: {"data": []}

        result = verify_posts.check_ig("token", "ig-user", now, now - 21_600, 1_800)

        self.assertEqual(2, result["checked_due_count"])
        self.assertEqual(
            ["not_marked_published", "missing_published_media_id"],
            [item["reason"] for item in result["missing_due"]],
        )


if __name__ == "__main__":
    unittest.main()
