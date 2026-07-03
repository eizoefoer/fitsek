#!/usr/bin/env python3
"""Watch and maintain Fitsek Meta API tokens.

Meta does not issue OAuth refresh tokens for this flow. This script keeps the
stored long-lived user token/page token usable as far as Meta allows, and alerts
before manual re-auth is required.

Cron mode should use --quiet-ok: no output while healthy; stdout only when a
refresh happened or user action is needed.
"""
from __future__ import annotations
import argparse, contextlib, datetime as dt, io, json, os, sys, urllib.parse, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
import meta_autopilot as meta  # noqa: E402

STATE = ROOT / 'var/meta_token_watch.json'
GRAPH = 'https://graph.facebook.com/v19.0'


def app_access_token() -> str:
    app_id, app_secret = meta.env('META_FITSEK_APP_ID'), meta.env('META_FITSEK_APP_SECRET')
    if not app_id or not app_secret:
        raise RuntimeError('Missing META_FITSEK_APP_ID / META_FITSEK_APP_SECRET')
    return f'{app_id}|{app_secret}'


def debug_token(token: str) -> dict:
    params = urllib.parse.urlencode({'input_token': token, 'access_token': app_access_token()})
    req = urllib.request.Request(f'{GRAPH}/debug_token?{params}')
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode() or '{}').get('data', {})
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        raise RuntimeError(f'Meta debug_token HTTP {e.code}: {body[:600]}')


def expiry_summary(data: dict) -> dict:
    exp = data.get('expires_at') or 0
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    if exp:
        expires_at = dt.datetime.fromtimestamp(exp, tz=dt.timezone.utc).isoformat()
        days_left = round((exp - now) / 86400, 1)
    else:
        expires_at = 'never_or_not_reported'
        days_left = None
    return {'is_valid': bool(data.get('is_valid')), 'expires_at': expires_at, 'days_left': days_left, 'scopes': sorted(data.get('scopes') or [])}


def get_summaries() -> dict:
    user_tok = meta.long_user_token() or meta.short_token()
    page_tok = meta.page_token()
    out = {}
    if user_tok:
        out['user_token'] = expiry_summary(debug_token(user_tok))
    else:
        out['user_token'] = {'is_valid': False, 'error': 'missing'}
    if page_tok:
        out['page_token'] = expiry_summary(debug_token(page_tok))
    else:
        out['page_token'] = {'is_valid': False, 'error': 'missing'}
    return out


def refresh_safely() -> tuple[bool, str]:
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            meta.refresh_tokens(write_env=True)
        return True, buf.getvalue().strip()
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--warn-days', type=float, default=14.0)
    ap.add_argument('--refresh-days', type=float, default=30.0)
    ap.add_argument('--quiet-ok', action='store_true')
    args = ap.parse_args()

    meta.load_env()
    messages = []

    try:
        before = get_summaries()
    except Exception as exc:
        print(f'Fitsek Meta token watch: unable to inspect tokens: {exc}')
        return 0

    need_refresh = False
    user = before.get('user_token', {})
    page = before.get('page_token', {})
    if not user.get('is_valid') or not page.get('is_valid'):
        need_refresh = True
    elif user.get('days_left') is not None and user['days_left'] <= args.refresh_days:
        need_refresh = True

    refreshed = False
    refresh_note = ''
    after = before
    if need_refresh:
        ok, note = refresh_safely()
        refreshed = ok
        refresh_note = note
        try:
            meta.load_env()
            after = get_summaries()
        except Exception as exc:
            messages.append(f'Fitsek Meta token watch: refresh attempted, but re-check failed: {exc}')

    user_after = after.get('user_token', {})
    page_after = after.get('page_token', {})
    if not user_after.get('is_valid'):
        messages.append('Fitsek Meta token action needed: user token is invalid. Generate a fresh user token and rerun `python3 automation/meta_autopilot.py refresh --write-env`.')
    elif user_after.get('days_left') is not None and user_after['days_left'] <= args.warn_days:
        messages.append(f"Fitsek Meta token action needed: user token expires in {user_after['days_left']} days ({user_after['expires_at']}). Re-auth through Meta before it expires.")
    if not page_after.get('is_valid'):
        messages.append('Fitsek Meta token action needed: page token is invalid or missing. Refresh/write env with a valid user token.')

    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'refreshed': refreshed, 'before': before, 'after': after}, indent=2), encoding='utf-8')

    if refreshed and not messages:
        messages.append(f"Fitsek Meta token refreshed/validated. User token days left: {user_after.get('days_left')}; page token valid: {page_after.get('is_valid')}")
    if refresh_note and messages:
        messages.append('Refresh details are stored safely in env/state; no token values printed.')

    if messages or not args.quiet_ok:
        print('\n'.join(messages) if messages else f"Fitsek Meta tokens OK. User token days left: {user_after.get('days_left')}; page token valid: {page_after.get('is_valid')}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
