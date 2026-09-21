#!/usr/bin/env python3
"""Regression coverage for Fitsek Meta token-watch API versioning."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))
import meta_token_watch


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b'{"data":{"is_valid":true,"scopes":["pages_manage_posts"]}}'


class MetaTokenWatchVersionTests(unittest.TestCase):
    def test_debug_token_uses_configured_graph_api_version(self) -> None:
        with patch.object(meta_token_watch.meta, "graph_version", return_value="v25.0"), patch.object(
            meta_token_watch, "app_access_token", return_value="app-id|app-secret"
        ), patch.object(meta_token_watch.urllib.request, "urlopen", return_value=FakeResponse()) as urlopen:
            result = meta_token_watch.debug_token("safe-test-token")

        requested_url = urlopen.call_args.args[0].full_url
        self.assertIn("/v25.0/debug_token?", requested_url)
        self.assertTrue(result["is_valid"])


if __name__ == "__main__":
    unittest.main()
