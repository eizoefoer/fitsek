#!/usr/bin/env python3
"""Fitsek Meta API automation.

Modes are deliberately approval-first:
- check: validate token, permissions, discover FB Page + linked IG account.
- prepare: build local outbox from content/social/30-day-calendar.csv.
- fb-draft: create unpublished Facebook Page photo posts (Graph API). User reviews/publishes in Meta.
- fb-schedule: create scheduled Facebook Page photo posts (requires --confirm; this schedules, so use only after approval).
- ig-plan: build IG-ready media plan. Instagram Graph API cannot create persistent scheduled drafts; media containers expire.

Secrets are loaded from ~/.hermes/.env and never printed.
"""
from __future__ import annotations
import argparse, csv, datetime as dt, json, os, sys, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = Path.home()/'.hermes/.env'
STATE_PATH = ROOT/'var/meta_state.json'
OUTBOX_PATH = ROOT/'automation/meta_outbox.json'
GRAPH='https://graph.facebook.com/v19.0'
REQUIRED_PERMS={'pages_show_list','pages_manage_posts','pages_read_engagement'}
IG_PERMS={'instagram_basic','instagram_content_publish'}

def load_env():
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(errors='ignore').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            k,v=line.split('=',1); os.environ[k.strip()] = v.strip().strip('"').strip("'")

def env(name): return os.environ.get(name,'').strip()

def urlencode(d): return urllib.parse.urlencode({k:v for k,v in d.items() if v is not None})

def graph(method, path, token, params=None, data=None):
    params=params or {}; data=data or {}
    if method=='GET':
        params['access_token']=token
        url=f'{GRAPH}/{path.lstrip("/")}?{urlencode(params)}'
        req=urllib.request.Request(url)
    else:
        data['access_token']=token
        url=f'{GRAPH}/{path.lstrip("/")}'
        req=urllib.request.Request(url, data=urlencode(data).encode(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        body=e.read().decode(errors='replace')
        raise RuntimeError(f'Meta API HTTP {e.code}: {body[:1200]}')

def short_token(): return env('META_FITSEK_ACCESS_TOKEN_SHORT_TERM') or env('META_FITSEK_USER_ACCESS_TOKEN')
def long_user_token(): return env('META_FITSEK_LONG_USER_ACCESS_TOKEN')
def page_token(): return env('META_FITSEK_PAGE_ACCESS_TOKEN')
def user_token(): return long_user_token() or short_token()

def exchange_user_token(token):
    app_id, app_secret = env('META_FITSEK_APP_ID'), env('META_FITSEK_APP_SECRET')
    if not (app_id and app_secret): raise SystemExit('Missing META_FITSEK_APP_ID / META_FITSEK_APP_SECRET')
    return graph('GET','oauth/access_token', token='', params={'grant_type':'fb_exchange_token','client_id':app_id,'client_secret':app_secret,'fb_exchange_token':token})

def get_user_token(): return user_token()

def upsert_env(updates: dict[str, str]):
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ENV_PATH.read_text(errors='ignore').splitlines() if ENV_PATH.exists() else []
    seen=set(); out=[]
    for line in lines:
        if '=' in line and not line.lstrip().startswith('#'):
            k=line.split('=',1)[0].strip()
            if k in updates:
                out.append(f'{k}={updates[k]}'); seen.add(k); continue
        out.append(line)
    for k,v in updates.items():
        if k not in seen: out.append(f'{k}={v}')
    ENV_PATH.write_text('\n'.join(out)+'\n')

def refresh_tokens(write_env=False):
    candidates=[]
    for label, tok in [('short', short_token()), ('long_user', long_user_token())]:
        if tok and tok not in [t for _, t in candidates]: candidates.append((label, tok))
    if not candidates: raise SystemExit('Missing META_FITSEK_ACCESS_TOKEN_SHORT_TERM or META_FITSEK_LONG_USER_ACCESS_TOKEN')
    errors=[]
    last=None
    for label, token in candidates:
        for mode in ['exchange', 'direct']:
            try:
                user_tok=token
                if mode == 'exchange':
                    exchanged=exchange_user_token(token)
                    user_tok=exchanged.get('access_token') or token
                accounts=graph('GET','me/accounts',user_tok,{'fields':'id,name,category,tasks,access_token,instagram_business_account{id,username,name}'})
                pages=accounts.get('data',[])
                fit_pages=[p for p in pages if 'fitsek' in (p.get('name','').lower())] or pages
                if not fit_pages: raise RuntimeError('No manageable pages returned for this token')
                page=fit_pages[0]
                updates={'META_FITSEK_LONG_USER_ACCESS_TOKEN':user_tok,'META_FITSEK_PAGE_ACCESS_TOKEN':page.get('access_token',''),'META_FITSEK_PAGE_ID':page.get('id','')}
                ig=page.get('instagram_business_account') or {}
                if ig.get('id'): updates['META_FITSEK_IG_USER_ID']=ig['id']
                if write_env: upsert_env({k:v for k,v in updates.items() if v})
                safe={'source_token':label,'refresh_mode':mode,'long_user_token_present':bool(user_tok),'page_access_token_present':bool(page.get('access_token')),'page':{k:v for k,v in page.items() if k!='access_token'},'ig_user':ig or None,'wrote_env':write_env}
                print(json.dumps(safe, indent=2))
                return safe
            except Exception as exc:
                errors.append(f'{label}/{mode}: {str(exc)[:220]}')
                last=exc
    raise RuntimeError('Unable to refresh/discover Meta tokens. Attempts: ' + ' | '.join(errors))

def discover(write_state=True):
    token=get_user_token()
    if not token: raise SystemExit('Missing META_FITSEK_ACCESS_TOKEN_SHORT_TERM or META_FITSEK_PAGE_ACCESS_TOKEN')
    me=graph('GET','me',token,{'fields':'id,name'})
    perms=graph('GET','me/permissions',token).get('data',[])
    granted={p.get('permission') for p in perms if p.get('status')=='granted'}
    accounts=graph('GET','me/accounts',token,{'fields':'id,name,category,tasks,access_token,instagram_business_account{id,username,name}'})
    pages=accounts.get('data',[])
    fit_pages=[p for p in pages if 'fitsek' in (p.get('name','').lower())] or pages
    state={'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'user':me,'granted_permissions':sorted(granted),'pages':[],'selected_page':None,'ig_user':None}
    for p in pages:
        pp={k:v for k,v in p.items() if k!='access_token'}
        pp['page_token_present']=bool(p.get('access_token'))
        state['pages'].append(pp)
    if fit_pages:
        p=fit_pages[0]
        state['selected_page']={k:v for k,v in p.items() if k!='access_token'}
        if p.get('instagram_business_account'):
            state['ig_user']=p['instagram_business_account']
        if write_state:
            STATE_PATH.parent.mkdir(exist_ok=True)
            STATE_PATH.write_text(json.dumps({**state,'selected_page_access_token_present':bool(p.get('access_token'))},indent=2), encoding='utf-8')
    missing=sorted(REQUIRED_PERMS-granted)
    ig_missing=sorted(IG_PERMS-granted)
    return state, missing, ig_missing, fit_pages[0].get('access_token') if fit_pages else None

def load_posts(days):
    cal=ROOT/'content/social/30-day-calendar.csv'
    with cal.open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    return rows[:days]

def schedule_time(day, hour=19, minute=30):
    # 19:30 AEST -> 09:30 UTC, start tomorrow; Meta requires at least 10 min future.
    today=dt.datetime.now(dt.timezone.utc).date()
    local_date=today + dt.timedelta(days=day)
    # AEST UTC+10 fixed for Brisbane.
    utc=dt.datetime.combine(local_date, dt.time(hour,minute), tzinfo=dt.timezone(dt.timedelta(hours=10))).astimezone(dt.timezone.utc)
    return int(utc.timestamp())

def caption(row, platform):
    dest=row.get(f'destination_url_{platform.lower()}') or row.get('destination_url_facebook') or 'https://fitsek.com/'
    hook=(row.get('hook','') or '').strip()
    body=(row.get('caption','') or '').strip()
    lead = body if body.lower().startswith(hook.lower()[:40]) else '\n\n'.join([hook, body]).strip()
    parts=[lead, '', f"CTA: {row.get('cta','Get the free reset').strip()}", dest, '', row.get('hashtags','').strip()]
    return '\n'.join([p for p in parts if p is not None]).strip()

def asset_url_for(day, row):
    base=env('META_FITSEK_ASSET_BASE_URL').rstrip('/')
    if base:
        return f'{base}/post-{day:02d}.png'
    return row.get('asset_url') or f'https://fitsek.com/assets/social/post-{day:02d}.png'

def build_outbox(days=7):
    posts=[]
    for r in load_posts(days):
        day=int(r['day'])
        item={
            'day':day,'date':r.get('date'),'title':r.get('post_title'),'format':r.get('format'),'pillar':r.get('pillar'),
            'asset_url':asset_url_for(day, r),
            'asset_path':r.get('asset_path') or f'site/assets/social/post-{day:02d}.png',
            'facebook_caption':caption(r,'facebook'),'instagram_caption':caption(r,'instagram'),
            'suggested_scheduled_publish_time_utc':schedule_time(day),
            'suggested_scheduled_publish_time_aest':dt.datetime.fromtimestamp(schedule_time(day), tz=dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=10))).isoformat(),
            'status':'ready_for_meta_review'
        }
        posts.append(item)
    OUTBOX_PATH.write_text(json.dumps({'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'mode':'approval_first','posts':posts},indent=2), encoding='utf-8')
    return posts

def print_safe_state(state, missing, ig_missing):
    print(json.dumps({
        'user': state.get('user'),
        'permissions_missing_for_fb': missing,
        'permissions_missing_for_ig': ig_missing,
        'pages_found': [{k:v for k,v in p.items() if k!='access_token'} for p in state.get('pages',[])],
        'selected_page': state.get('selected_page'),
        'ig_user': state.get('ig_user'),
        'state_file': str(STATE_PATH),
    }, indent=2))

def fb_create(mode, days, confirm=False):
    posts=build_outbox(days)
    if not confirm:
        print(f'DRY RUN: would create {len(posts)} Facebook {mode} photo posts. Use --confirm with a valid page token to call Meta API.')
        print(f'Outbox: {OUTBOX_PATH}')
        return
    state, missing, _, page_access = discover(write_state=True)
    page=state.get('selected_page')
    page_tasks=set((page or {}).get('tasks') or [])
    if missing and 'CREATE_CONTENT' not in page_tasks:
        raise SystemExit('Missing required Facebook permissions: '+', '.join(missing))
    if missing and 'CREATE_CONTENT' in page_tasks:
        print('Warning: user token is missing '+', '.join(missing)+' but the selected Page grants CREATE_CONTENT; attempting the API call and letting Meta enforce permissions.', file=sys.stderr)
    if not page or not page_access: raise SystemExit('No manageable Fitsek Facebook Page with page access token found')
    created=[]
    for item in posts:
        data={'url':item['asset_url'],'caption':item['facebook_caption'],'published':'false'}
        if mode=='scheduled':
            data['scheduled_publish_time']=str(item['suggested_scheduled_publish_time_utc'])
        res=graph('POST',f'{page["id"]}/photos',page_access,data=data)
        created.append({'day':item['day'],'id':res.get('id') or res.get('post_id'),'mode':mode,'asset_url':item['asset_url']})
        time.sleep(1)
    print(json.dumps({'created':created,'note':'Review in Meta Business Suite / Page publishing tools before the posts go live. For unpublished mode, publish/schedule manually.'}, indent=2))

def ig_plan(days):
    posts=build_outbox(days)
    state={}; ig_missing=[]; token_status='not_checked'
    try:
        state, _, ig_missing, _ = discover(write_state=True)
        token_status='ok'
    except Exception as exc:
        token_status='unavailable_or_expired'
    print(json.dumps({'ig_user':state.get('ig_user'),'token_status':token_status,'permissions_missing_for_ig':ig_missing,'note':'Instagram Graph API supports immediate publish via media container + publish, but not persistent future drafts in Meta Business Suite. Use this outbox for manual schedule approval, or run a future cron publisher after explicit approval.','outbox':str(OUTBOX_PATH),'posts':posts}, indent=2))

def main():
    load_env()
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('check')
    p=sub.add_parser('refresh'); p.add_argument('--write-env', action='store_true', help='Store long-lived user token, page token, page ID, and IG ID in ~/.hermes/.env')
    p=sub.add_parser('prepare'); p.add_argument('--days',type=int,default=7)
    p=sub.add_parser('fb-draft'); p.add_argument('--days',type=int,default=7); p.add_argument('--confirm',action='store_true')
    p=sub.add_parser('fb-schedule'); p.add_argument('--days',type=int,default=7); p.add_argument('--confirm',action='store_true')
    p=sub.add_parser('ig-plan'); p.add_argument('--days',type=int,default=7)
    args=ap.parse_args()
    if args.cmd=='check':
        state, missing, ig_missing, _ = discover(write_state=True); print_safe_state(state, missing, ig_missing)
    elif args.cmd=='refresh':
        refresh_tokens(write_env=args.write_env)
    elif args.cmd=='prepare':
        posts=build_outbox(args.days); print(json.dumps({'outbox':str(OUTBOX_PATH),'posts_prepared':len(posts),'first_asset':posts[0]['asset_url'] if posts else None}, indent=2))
    elif args.cmd=='fb-draft': fb_create('draft', args.days, args.confirm)
    elif args.cmd=='fb-schedule': fb_create('scheduled', args.days, args.confirm)
    elif args.cmd=='ig-plan': ig_plan(args.days)
if __name__=='__main__':
    try:
        main()
    except RuntimeError as exc:
        msg=str(exc)
        if 'Error validating access token' in msg or 'Session has expired' in msg:
            print('Meta API token error: the configured token is invalid or expired. Generate a fresh token with pages_show_list, pages_manage_posts, pages_read_engagement, instagram_basic, and instagram_content_publish, then rerun `python3 automation/meta_autopilot.py check`.', file=sys.stderr)
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)
