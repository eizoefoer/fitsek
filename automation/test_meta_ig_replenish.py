#!/usr/bin/env python3
"""Regression coverage for the mixed social plan replenisher."""
from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation import meta_ig_publisher as publisher


class ReplenishMixedPlanTests(unittest.TestCase):
    def test_extends_low_horizon_without_losing_published_rows(self):
        today = dt.datetime.now(publisher.AEST).date()
        plan = {"mode": "mixed_format_funnel_v1", "posts": [
            {"plan_id": "published", "status": "published", "publication_mode": "instagram_graph_api", "scheduled_publish_time_aest": dt.datetime.combine(today - dt.timedelta(days=1), dt.time(9), tzinfo=publisher.AEST).isoformat(), "published_media_id": "123"},
            {"plan_id": "due-soon", "status": "scheduled", "publication_mode": "instagram_graph_api", "scheduled_publish_time_aest": dt.datetime.combine(today + dt.timedelta(days=1), dt.time(9), tzinfo=publisher.AEST).isoformat()},
        ]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "schedule.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            with patch.object(publisher, "SCHEDULE_PATH", path):
                result, changed = publisher.replenish_mixed_plan(days=3, minimum_future_days=7)
        self.assertTrue(changed)
        self.assertEqual(result["posts"][0]["published_media_id"], "123")
        self.assertEqual(len(result["posts"]), 8)
        self.assertEqual(sum(p["format"] == "story" for p in result["posts"][2:]), 3)

    def test_keeps_a_healthy_horizon_unchanged(self):
        today = dt.datetime.now(publisher.AEST).date()
        plan = {"mode": "mixed_format_funnel_v1", "posts": [{"plan_id": "future", "status": "scheduled", "publication_mode": "instagram_graph_api", "scheduled_publish_time_aest": dt.datetime.combine(today + dt.timedelta(days=10), dt.time(9), tzinfo=publisher.AEST).isoformat()}]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "schedule.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            with patch.object(publisher, "SCHEDULE_PATH", path):
                result, changed = publisher.replenish_mixed_plan(days=3, minimum_future_days=7)
        self.assertFalse(changed)
        self.assertEqual(len(result["posts"]), 1)


if __name__ == "__main__":
    unittest.main()
