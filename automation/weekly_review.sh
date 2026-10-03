#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/fitsek
python3 automation/business_review.py --period weekly --write
python3 automation/social_format_readout.py --write
