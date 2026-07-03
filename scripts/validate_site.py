#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
from html.parser import HTMLParser
ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.forms=0; self.inputs=[]; self.title=''; self._in_title=False
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=='a' and d.get('href'): self.links.append(d['href'])
        if tag=='form': self.forms += 1
        if tag=='input': self.inputs.append(d)
        if tag=='title': self._in_title=True
    def handle_endtag(self, tag):
        if tag=='title': self._in_title=False
    def handle_data(self, data):
        if self._in_title: self.title += data

def read_site(name): return (SITE/name).read_text(encoding='utf-8')
def read_root(name): return (ROOT/name).read_text(encoding='utf-8')
def assert_contains(text, needles, file):
    missing=[n for n in needles if n not in text]
    assert not missing, f'{file} missing {missing}'

index = read_site('index.html')
assert_contains(index, ['Hero', '7-Day Desk Worker Recomp Reset', 'Fitsek 12-Week Recomp System', 'Privacy', 'Terms', 'Fitness disclaimer', 'leads.fitsek.com/signup', 'static.cloudflareinsights.com/beacon.min.js'], 'site/index.html')
for section in ['problem','how','preview','faq','signup']:
    assert f'id="{section}"' in index, f'missing section #{section}'
for claim in ['diagnose users','hormone fix','cortisol cure','guaranteed fat loss','guaranteed transformation','real customer transformation']:
    assert claim.lower() not in index.lower(), f'unsafe claim phrase present: {claim}'
parser=LinkParser(); parser.feed(index)
assert parser.forms == 1, 'expected one signup form'
assert any(i.get('type')=='email' and 'required' in i for i in parser.inputs), 'required email input missing'
assert any(i.get('name')=='consent' and i.get('type')=='checkbox' and 'required' in i for i in parser.inputs), 'consent checkbox missing'
for page in ['lead-magnet.html','product.html','privacy.html','terms.html','disclaimer.html']:
    text=read_site(page)
    assert '<title>' in text, f'{page} missing title'
    assert 'medical advice' in text.lower() or page in {'privacy.html','terms.html'}, f'{page} needs disclaimer wording'
for required in ['site/CNAME','site/robots.txt','site/sitemap.xml','AGENTS.md','AI_STATE.md','.gitignore','docs/strategy/brand-basics.md','content/social/30-day-calendar.csv','products/paid-recomp-system/README.md','automation/business_review.py']:
    assert (ROOT/required).exists(), f'missing {required}'
all_text='\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and 'analytics/reports' not in str(p))
secret_patterns=[r'sk_live_[A-Za-z0-9]{12,}', r'ghp_[A-Za-z0-9]{20,}', r'github_pat_[A-Za-z0-9_]{20,}', r'EA[A-Za-z0-9]{20,}', r'AIza[A-Za-z0-9_-]{20,}']
for pat in secret_patterns:
    assert not re.search(pat, all_text), f'secret-like pattern found: {pat}'
print('site validation ok')
