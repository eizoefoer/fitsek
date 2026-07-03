# Business Review System

Run reports manually:

```bash
python3 automation/business_review.py --period daily --write
python3 automation/business_review.py --period weekly --write
python3 automation/business_review.py --period monthly --write
```

The script checks live URLs, lead API health, local event/lead logs, social draft queue, manual social metrics, and decision-rule recommendations. Reports are written to `analytics/reports/`.

Manual social metrics live in `analytics/manual_social_metrics.csv` until Instagram/Facebook API access is stable, approved, and compliant.
