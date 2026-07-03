#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, re, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get('FITSEK_API_PORT', '8765'))
DATA_DIR = Path(os.environ.get('FITSEK_DATA_DIR', '/var/lib/fitsek'))
ALLOWED = {x.strip() for x in os.environ.get('FITSEK_ALLOWED_ORIGINS', 'https://fitsek.com,https://www.fitsek.com,http://127.0.0.1:8080').split(',') if x.strip()}
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
MAX_BODY = 32_768

DATA_DIR.mkdir(parents=True, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    server_version = 'fitsek-leads/1.0'

    def _origin(self):
        origin = self.headers.get('Origin', '')
        return origin if origin in ALLOWED else ''

    def _headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        origin = self._origin()
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        origin = self._origin()
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Vary', 'Origin')
        self.end_headers()

    def _json_body(self):
        length = int(self.headers.get('Content-Length', '0') or 0)
        if length > MAX_BODY:
            raise ValueError('body too large')
        raw = self.rfile.read(length)
        return json.loads(raw.decode('utf-8') or '{}')

    def _client_ip(self):
        fwd = self.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        return fwd or self.client_address[0]

    def _append(self, name, item):
        path = DATA_DIR / name
        with path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(item, sort_keys=True, separators=(',', ':')) + '\n')
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def do_GET(self):
        if self.path == '/healthz':
            self._headers(200)
            self.wfile.write(b'{"ok":true}')
            return
        self._headers(404); self.wfile.write(b'{"error":"not_found"}')

    def do_POST(self):
        if self.path not in {'/signup', '/event'}:
            self._headers(404); self.wfile.write(b'{"error":"not_found"}'); return
        try:
            data = self._json_body()
        except Exception:
            self._headers(400); self.wfile.write(b'{"error":"bad_json"}'); return
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        ip = self._client_ip()
        base = {
            'received_at': now,
            'ip_hash': hashlib.sha256(ip.encode('utf-8')).hexdigest()[:16],
            'user_agent_hash': hashlib.sha256((self.headers.get('User-Agent') or '').encode('utf-8')).hexdigest()[:16],
            'origin': self.headers.get('Origin', ''),
            'path': str(data.get('path', ''))[:200],
            'utm': data.get('utm') if isinstance(data.get('utm'), dict) else {},
            'referrer': str(data.get('referrer', ''))[:500],
        }
        if self.path == '/event':
            event_type = str(data.get('type', 'event'))[:80]
            label = str(data.get('label', ''))[:160]
            self._append('events.jsonl', {**base, 'type': event_type, 'label': label, 'href': str(data.get('href',''))[:500]})
            self._headers(202); self.wfile.write(b'{"ok":true}'); return
        email = str(data.get('email', '')).strip().lower()
        if data.get('company'):
            self._headers(202); self.wfile.write(b'{"ok":true}'); return
        if not data.get('consent') or not EMAIL_RE.match(email):
            self._headers(400); self.wfile.write(b'{"error":"invalid_signup"}'); return
        self._append('leads.jsonl', {**base, 'email': email, 'lead_magnet': str(data.get('lead_magnet', ''))[:120], 'consent': True})
        self._append('events.jsonl', {**base, 'type': 'signup', 'label': '7-day-reset'})
        self._headers(201); self.wfile.write(b'{"ok":true}')

    def log_message(self, fmt, *args):
        return

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
