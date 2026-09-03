#!/usr/bin/env python3
"""Regression tests for Facebook scheduled-post Graph payloads."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import meta_autopilot


class FacebookSchedulePayloadTests(unittest.TestCase):
    def test_scheduled_photo_declares_scheduled_unpublished_content_type(self) -> None:
        post = {
            "day": 1,
            "title": "Test post",
            "asset_url": "https://fitsek.com/assets/social/post-01.png",
            "facebook_caption": "Test caption",
            "suggested_scheduled_publish_time_utc": 1_800_000_000,
            "suggested_scheduled_publish_time_aest": "2027-01-15T00:00:00+10:00",
        }
        recorded: list[dict] = []

        def fake_graph(_method, _path, _token, data=None, **_kwargs):
            recorded.append(data)
            return {"id": "123"}

        state = {"selected_page": {"id": "page-id", "tasks": ["CREATE_CONTENT"]}}
        with patch.object(meta_autopilot, "build_outbox", return_value=[post]), \
             patch.object(meta_autopilot, "discover", return_value=(state, [], [], "page-token")), \
             patch.object(meta_autopilot, "graph", side_effect=fake_graph), \
             patch.object(meta_autopilot.time, "sleep"):
            meta_autopilot.fb_create("scheduled", 1, confirm=True)

        self.assertEqual("false", recorded[0]["published"])
        self.assertEqual("SCHEDULED", recorded[0]["unpublished_content_type"])
        self.assertEqual("1800000000", recorded[0]["scheduled_publish_time"])


if __name__ == "__main__":
    unittest.main()
