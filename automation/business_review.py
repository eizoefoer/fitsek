#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, os, urllib.parse, urllib.request, urllib.error
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get('FITSEK_DATA_DIR', '/var/lib/fitsek'))
REPORT_DIR = ROOT / 'analytics' / 'reports'

URLS = ['https://fitsek.com/', 'https://fitsek.com/product.html', 'https://fitsek.com/lead-magnet.html', 'https://leads.fitsek.com/healthz']

def read_jsonl(path: Path):
    if not path.exists(): return []
    out=[]
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    except PermissionError:
        return []
    for line in lines:
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def expected_body_ok(url: str, body: str) -> bool:
    if url.endswith('/'): return '7-Day Desk Worker Recomp Reset' in body
    if 'lead-magnet' in url: return '7-Day Desk Worker Recomp Reset' in body
    if 'product' in url: return '12-Week Recomp System' in body
    if 'healthz' in url: return 'true' in body
    return True

def fetch(url: str, headers: dict[str, str] | None = None) -> tuple[int, str]:
    req=urllib.request.Request(url, headers={'User-Agent':'fitsek-review/1.0', **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.read(120000).decode('utf-8', errors='replace')

def github_pages_http_fallback(url: str) -> tuple[bool, str] | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.hostname not in {'fitsek.com', 'www.fitsek.com'}:
        return None
    fallback_url = urllib.parse.urlunparse(('http', '185.199.108.153', parsed.path or '/', '', parsed.query, ''))
    try:
        status, body = fetch(fallback_url, {'Host': 'fitsek.com'})
        ok = 200 <= status < 400 and expected_body_ok(url, body)
        return ok, f'{status} via GitHub Pages public-DNS fallback; HTTPS cert/local resolver may still be settling'
    except Exception as e:
        return False, f'fallback {type(e).__name__}: {e}'

def check_url(url: str) -> tuple[bool, str]:
    try:
        status, body = fetch(url)
        ok=200 <= status < 400 and expected_body_ok(url, body)
        return ok, f'{status}'
    except Exception as e:
        fallback = github_pages_http_fallback(url)
        if fallback is not None and fallback[0]:
            return fallback
        detail = f'{type(e).__name__}: {e}'
        if fallback is not None:
            detail += f'; {fallback[1]}'
        return False, detail

def social_queue():
    posts=list((ROOT/'content/social/posts').glob('day-*.md'))
    approved=sum('status: approved' in p.read_text(encoding='utf-8', errors='ignore').lower() for p in posts)
    return len(posts), approved

def manual_social():
    path=ROOT/'analytics/manual_social_metrics.csv'
    if not path.exists(): return []
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def num(v):
    try: return float(v or 0)
    except Exception: return 0.0

def build_report(period: str) -> str:
    now=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    events=read_jsonl(DATA_DIR/'events.jsonl')
    leads=read_jsonl(DATA_DIR/'leads.jsonl')
    event_counts=Counter(e.get('type','unknown') for e in events)
    source_counts=Counter((e.get('utm') or {}).get('utm_source','direct/unknown') for e in events)
    post_count, approved=social_queue()
    metrics=manual_social()
    by_post=[]
    for m in metrics:
        score = num(m.get('link_clicks'))*3 + num(m.get('email_signups'))*8 + num(m.get('saves'))*2 + num(m.get('shares'))*2 + num(m.get('sales'))*20
        by_post.append((score,m))
    by_post.sort(key=lambda x:x[0], reverse=True)
    url_checks=[(u,*check_url(u)) for u in URLS]
    product_clicks=sum(1 for e in events if 'product' in str(e.get('href','')) or e.get('label','').startswith('cta_product'))
    checkout_starts=event_counts.get('checkout_start', 0)
    completed_sales=event_counts.get('checkout_complete', 0)
    section_views=Counter(str(e.get('section','unknown')) for e in events if e.get('type') == 'section_view')
    scroll_depths=Counter(str(e.get('depth','unknown')) for e in events if e.get('type') == 'scroll_depth')
    signup_rate=(len(leads)/max(1,event_counts.get('page_view',0)))*100
    recommendations=[]
    if post_count - approved < 7: recommendations.append('Queue/approve at least 7 upcoming social posts.')
    if event_counts.get('click',0) == 0 and event_counts.get('page_view',0) > 20: recommendations.append('Posts/landing may need stronger CTA bridge; clicks are low vs visits.')
    if event_counts.get('click',0) > 0 and len(leads) == 0: recommendations.append('Improve lead magnet promise/form placement; clicks exist but signups are absent.')
    if len(leads) > 0 and product_clicks == 0: recommendations.append('Strengthen paid product bridge in email/page copy.')
    if product_clicks > 0 and checkout_starts == 0: recommendations.append('No checkout starts: make the purchase CTA, price, and Stripe link more prominent.')
    if checkout_starts > 0 and completed_sales == 0: recommendations.append('Checkout starts without sales: review price, offer clarity, and Stripe checkout friction.')
    if completed_sales > 0: recommendations.append('Completed sales recorded: ask buyers for compliant feedback and expand the winning acquisition channel.')
    if not recommendations: recommendations.append('Keep publishing; next improvement: A/B test hook style on the next 3 posts.')
    lines=[
        f'# Fitsek {period.title()} Business Review — {now}', '',
        '## Health checks',
        *[f'- {u}: {"OK" if ok else "FAIL"} ({detail})' for u,ok,detail in url_checks], '',
        '## Funnel metrics',
        f'- Website/page events: {event_counts.get("page_view",0)}',
        f'- CTA/click events: {event_counts.get("click",0)}',
        f'- Email leads: {len(leads)}',
        f'- Signup conversion estimate: {signup_rate:.1f}%',
        f'- Product intent clicks/events: {product_clicks}',
        f'- Checkout-start events: {checkout_starts}',
        f'- Completed-sale events: {completed_sales}',
        f'- Section-view events: {sum(section_views.values())} ({dict(section_views.most_common(5))})',
        f'- Scroll-depth events: {sum(scroll_depths.values())} ({dict(scroll_depths.most_common(5))})',
        f'- Traffic sources seen: {dict(source_counts.most_common(8))}', '',
        '## Social queue',
        f'- Draft posts: {post_count}',
        f'- Approved posts: {approved}',
        '- Publishing mode: manual approval / Meta Business Suite first 30 days', '',
        '## Best / worst content from manual metrics',
    ]
    if by_post:
        best=by_post[0][1]; worst=by_post[-1][1]
        lines += [f'- Best: {best.get("platform")} {best.get("post_id")} — clicks {best.get("link_clicks")}, saves {best.get("saves")}, sales {best.get("sales")}', f'- Worst: {worst.get("platform")} {worst.get("post_id")} — clicks {worst.get("link_clicks")}, saves {worst.get("saves")}, sales {worst.get("sales")}']
    else:
        lines += ['- No manual social metrics entered yet. Add published post metrics to `analytics/manual_social_metrics.csv`.']
    lines += ['', '## Recommended next action', *[f'- {r}' for r in recommendations], '', '## Decision rules reminder', '- Reach no clicks → improve CTA and bio link.', '- Clicks no signups → improve landing page/lead magnet promise.', '- Signups no sales → improve offer, pricing, proof, email bridge.', '- Saves high clicks low → create stronger bridge content.', '- Walking pad / meal template / tracker winners should become product extensions.']
    return '\n'.join(lines) + '\n'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--period', choices=['daily','weekly','monthly'], default='daily')
    ap.add_argument('--write', action='store_true')
    args=ap.parse_args()
    report=build_report(args.period)
    if args.write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        path=REPORT_DIR/f'{datetime.now(timezone.utc).strftime("%Y-%m-%d")}-{args.period}.md'
        path.write_text(report, encoding='utf-8')
        print(f'Wrote {path}')
    print(report)
if __name__ == '__main__': main()
