from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "automation" / "verify_posts.py"
SPEC = importlib.util.spec_from_file_location("fitsek_verify_posts", MODULE_PATH)
verify_posts = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verify_posts)


class VerifyPostsTests(unittest.TestCase):
    def test_instagram_ignores_published_posts_outside_recent_verification_window(self) -> None:
        plan = {
            "posts": [
                {
                    "title": "historic published post",
                    "scheduled_publish_time_utc": 100,
                    "status": "published",
                    "published_media_id": "old-media",
                },
                {
                    "title": "recent published post",
                    "scheduled_publish_time_utc": 900,
                    "status": "published",
                    "published_media_id": "recent-media",
                },
            ]
        }
        with patch.object(verify_posts, "graph_get", return_value={"data": [{"id": "recent-media"}]}), patch.object(verify_posts, "load_json", return_value=plan):
            result = verify_posts.check_ig("token", "ig", now=1_200, since=800, grace_seconds=60)
        self.assertEqual(result["checked_due_count"], 1)
        self.assertEqual(result["missing_due"], [])

    def test_instagram_still_reports_a_recent_due_post_that_is_not_visible(self) -> None:
        plan = {
            "posts": [
                {
                    "day": 3,
                    "title": "recent missing post",
                    "scheduled_publish_time_utc": 900,
                    "status": "published",
                    "published_media_id": "missing-media",
                },
            ]
        }
        with patch.object(verify_posts, "graph_get", return_value={"data": []}), patch.object(verify_posts, "load_json", return_value=plan):
            result = verify_posts.check_ig("token", "ig", now=1_200, since=800, grace_seconds=60)
        self.assertEqual(result["checked_due_count"], 1)
        self.assertEqual(result["missing_due"], [
            {
                "day": 3,
                "title": "recent missing post",
                "scheduled_aest": verify_posts.ts_to_aest(900),
                "status": "published",
                "published_media_id": "missing-media",
            }
        ])
