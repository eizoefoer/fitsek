#!/usr/bin/env python3
"""Regression coverage for Fitsek first-party event capture."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
import lead_api


class EventCaptureTests(unittest.TestCase):
    def test_event_endpoint_persists_section_and_scroll_depth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            previous_data_dir = lead_api.DATA_DIR
            lead_api.DATA_DIR = Path(temp_dir)
            server = lead_api.ThreadingHTTPServer(("127.0.0.1", 0), lead_api.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                payload = json.dumps(
                    {
                        "type": "section_view",
                        "path": "/",
                        "section": "faq",
                        "depth": 75,
                        "utm": {"utm_source": "instagram"},
                    }
                ).encode("utf-8")
                request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/event",
                    data=payload,
                    headers={"Content-Type": "application/json", "Origin": "https://fitsek.com"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=5) as response:
                    self.assertEqual(202, response.status)

                record = json.loads((Path(temp_dir) / "events.jsonl").read_text(encoding="utf-8"))
                self.assertEqual(
                    {"section": "faq", "depth": 75},
                    {"section": record.get("section"), "depth": record.get("depth")},
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                lead_api.DATA_DIR = previous_data_dir


if __name__ == "__main__":
    unittest.main()
