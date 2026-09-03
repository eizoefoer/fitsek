#!/usr/bin/env python3
"""Regression tests for the public Stripe checkout bridge."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class FirstSaleFunnelTests(unittest.TestCase):
    def test_product_page_has_a_tracked_stripe_checkout_cta(self) -> None:
        product = (SITE / "product.html").read_text(encoding="utf-8")
        self.assertIn('data-track="checkout_start"', product)
        self.assertIn('data-checkout-link', product)
        self.assertIn('/checkout.js', product)
        self.assertNotIn('Checkout is not open yet', product)

    def test_checkout_config_is_safe_by_default_and_runtime_script_rejects_non_stripe_urls(self) -> None:
        config = json.loads((SITE / "checkout.json").read_text(encoding="utf-8"))
        self.assertEqual({"url": ""}, config)
        script = (SITE / "checkout.js").read_text(encoding="utf-8")
        self.assertIn('https://buy.stripe.com/', script)
        self.assertIn('checkout_start', script)
        self.assertIn('checkout_unavailable', script)

    def test_weekly_review_reports_checkout_intent_and_sales(self) -> None:
        review = (ROOT / "automation/business_review.py").read_text(encoding="utf-8")
        self.assertIn('Checkout-start events', review)
        self.assertIn('Completed-sale events', review)
        self.assertIn('No checkout starts', review)


if __name__ == "__main__":
    unittest.main()
