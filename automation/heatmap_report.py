#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get('FITSEK_DATA_DIR', '/var/lib/fitsek'))
REPORT_DIR = ROOT / 'analytics' / 'reports'


def read_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    except PermissionError:
        return []
    for line in lines:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def build_report() -> str:
    events = read_jsonl(DATA_DIR / 'events.jsonl')
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    by_type = Counter(str(e.get('type', 'unknown')) for e in events)
    by_path = Counter(str(e.get('path', 'unknown')) for e in events)
    clicks = Counter()
    sections = Counter()
    scrolls = Counter()
    sources = Counter()
    for e in events:
        etype = e.get('type')
        if etype == 'click':
            clicks[str(e.get('label') or e.get('href') or 'unknown')] += 1
        elif etype == 'section_view':
            sections[str(e.get('section') or 'unknown')] += 1
        elif etype == 'scroll_depth':
            scrolls[str(e.get('depth') or 'unknown')] += 1
        utm = e.get('utm') or {}
        sources[str(utm.get('utm_source') or 'direct/unknown')] += 1
    lines = [
        f'# Fitsek First-Party UX Heatmap Report — {now}',
        '',
        'This is a privacy-light, first-party event summary. It is not a session-recording heatmap and does not identify visitors. Use it to decide whether the page needs clearer CTAs, stronger section order, or more social bridge content.',
        '',
        '## Event mix',
        *[f'- {k}: {v}' for k, v in by_type.most_common()],
        '',
        '## Traffic by path',
        *[f'- {k}: {v}' for k, v in by_path.most_common(12)],
        '',
        '## CTA/click labels',
        *([f'- {k}: {v}' for k, v in clicks.most_common(12)] or ['- No click events captured yet.']),
        '',
        '## Section views',
        *([f'- {k}: {v}' for k, v in sections.most_common(12)] or ['- Section-view instrumentation is now installed; wait for fresh traffic.']),
        '',
        '## Scroll depth',
        *([f'- {k}%: {v}' for k, v in sorted(scrolls.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 999)] or ['- Scroll-depth instrumentation is now installed; wait for fresh traffic.']),
        '',
        '## Source tags',
        *[f'- {k}: {v}' for k, v in sources.most_common(12)],
        '',
        '## Interpretation rules',
        '- Page views without 50%+ scroll: tighten hero promise and above-fold CTA.',
        '- Scrolls without clicks: improve CTA contrast, wording, and bridge sections.',
        '- Clicks without signups: improve lead magnet specificity and form trust cues.',
        '- Product clicks without signups/sales: add stronger product bridge emails and waitlist proof.',
    ]
    return '\n'.join(lines) + '\n'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    report = build_report()
    if args.write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORT_DIR / f'{datetime.now(timezone.utc).strftime("%Y-%m-%d")}-ux-heatmap.md'
        out.write_text(report, encoding='utf-8')
        print(f'Wrote {out}')
    print(report)


if __name__ == '__main__':
    main()
