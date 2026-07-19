#!/usr/bin/env python3
"""Publish/verify Fitsek profile-refresh media through the Meta Graph API.

This script deliberately separates asset creation from mutating Meta calls. Use
`check` and `print-urls` freely. `publish-ig` requires --confirm and writes only
non-secret IDs to var/meta_profile_refresh_published.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "content/social/profile-refresh-manifest.json"
STATE_PATH = ROOT / "var/meta_profile_refresh_published.json"
DEFAULT_GRAPH_VERSION = "v25.0"


def load_env() -> None:
    for path in [Path("/home/ubuntu/.hermes/.env"), Path.home() / ".hermes/.env"]:
        if not path.exists():
            continue
        for raw in path.read_text(errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def graph_version() -> str:
    raw = env("META_GRAPH_VERSION") or DEFAULT_GRAPH_VERSION
    raw = raw.strip().lstrip("/")
    return raw if raw.startswith("v") else f"v{raw}"


def graph_url(path: str) -> str:
    return f"https://graph.facebook.com/{graph_version()}/{path.lstrip('/')}"


def urlencode(values: dict[str, Any]) -> str:
    return urllib.parse.urlencode({k: str(v) for k, v in values.items() if v is not None})


def graph(method: str, path: str, token: str, params: dict[str, Any] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    params = dict(params or {})
    data = dict(data or {})
    if method == "GET":
        params["access_token"] = token
        req = urllib.request.Request(f"{graph_url(path)}?{urlencode(params)}")
    else:
        data["access_token"] = token
        req = urllib.request.Request(graph_url(path), data=urlencode(data).encode(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"Meta API HTTP {exc.code}: {body[:1600]}") from exc


def manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Missing manifest: {MANIFEST_PATH}. Run automation/render_profile_social_refresh.py first.")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def publish_token() -> str:
    token = env("META_FITSEK_PAGE_ACCESS_TOKEN") or env("META_FITSEK_LONG_USER_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Missing META_FITSEK_PAGE_ACCESS_TOKEN or META_FITSEK_LONG_USER_ACCESS_TOKEN")
    return token


def ig_user_id() -> str:
    value = env("META_FITSEK_IG_USER_ID")
    if value:
        return value
    state = ROOT / "var/meta_state.json"
    if state.exists():
        data = json.loads(state.read_text())
        ig = data.get("ig_user") or (data.get("selected_page") or {}).get("instagram_business_account") or {}
        if ig.get("id"):
            return str(ig["id"])
    return "17841443568404793"


def public_url(entry: dict[str, Any], base_url: str) -> str:
    path = Path(str(entry["path"]))
    return f"{base_url.rstrip('/')}/{path.name}"


def cover_url(entry: dict[str, Any], base_url: str) -> str | None:
    cover = entry.get("cover_path")
    if not cover:
        return None
    return f"{base_url.rstrip('/')}/{Path(str(cover)).name}"


def entries_by_id(ids: list[str] | None, kinds: set[str] | None = None) -> list[dict[str, Any]]:
    entries = [e for e in manifest().get("entries", []) if e.get("status") == "ready_for_publish_or_schedule"]
    if kinds:
        entries = [e for e in entries if e.get("kind") in kinds]
    if ids:
        wanted = set(ids)
        entries = [e for e in entries if e.get("id") in wanted]
        missing = sorted(wanted - {e.get("id") for e in entries})
        if missing:
            raise SystemExit("Unknown or non-publishable entry IDs: " + ", ".join(missing))
    return entries


def probe_url(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return {"url": url, "status": response.status, "content_type": response.headers.get("content-type"), "content_length": response.headers.get("content-length")}
    except Exception as exc:
        return {"url": url, "error": str(exc)}


def wait_for_container(container_id: str, token: str, timeout_seconds: int = 300) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last: dict[str, Any] = {}
    while True:
        last = graph("GET", container_id, token, params={"fields": "id,status_code,status"})
        status = last.get("status_code")
        if status in {None, "FINISHED", "ERROR", "EXPIRED", "PUBLISHED"}:
            return last
        if time.time() >= deadline:
            return last
        time.sleep(10)


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"created_at": dt.datetime.now(dt.timezone.utc).isoformat(), "published": []}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def publish_entry(entry: dict[str, Any], base_url: str, token: str, timeout_seconds: int) -> dict[str, Any]:
    kind = entry.get("kind")
    media_url = public_url(entry, base_url)
    data: dict[str, Any]
    if kind == "photo":
        data = {"image_url": media_url, "caption": entry.get("caption"), "alt_text": entry.get("alt_text")}
    elif kind == "reel":
        data = {"media_type": "REELS", "video_url": media_url, "caption": entry.get("caption"), "share_to_feed": "true"}
    elif kind == "story_image":
        data = {"media_type": "STORIES", "image_url": media_url}
    else:
        raise RuntimeError(f"Unsupported publish kind: {kind}")
    container = graph("POST", f"{ig_user_id()}/media", token, data=data)
    container_id = container.get("id")
    if not container_id:
        raise RuntimeError(f"No container id returned for {entry.get('id')}: {container}")
    status = wait_for_container(str(container_id), token, timeout_seconds=timeout_seconds)
    if status.get("status_code") not in {None, "FINISHED", "PUBLISHED"}:
        raise RuntimeError(f"Container {container_id} not publishable for {entry.get('id')}: {status}")
    published = graph("POST", f"{ig_user_id()}/media_publish", token, data={"creation_id": container_id})
    media_id = published.get("id")
    if not media_id:
        raise RuntimeError(f"No media id returned for {entry.get('id')}: {published}")
    return {
        "entry_id": entry.get("id"),
        "kind": kind,
        "surface": entry.get("surface"),
        "asset_url": media_url,
        "cover_url": cover_url(entry, base_url),
        "container_id": container_id,
        "container_status": status,
        "published_media_id": media_id,
        "published_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def cmd_check() -> int:
    load_env()
    token = publish_token()
    ig = ig_user_id()
    limit = graph("GET", f"{ig}/content_publishing_limit", token)
    recent = graph("GET", f"{ig}/media", token, params={"fields": "id,media_type,media_product_type,timestamp,permalink,caption", "limit": 12})
    account = graph("GET", ig, token, params={"fields": "id,username,name,media_count,followers_count,follows_count"})
    print(json.dumps({"graph_version": graph_version(), "ig_account": account, "content_publishing_limit": limit, "recent_media": recent.get("data", [])}, indent=2))
    return 0


def cmd_print_urls(args: argparse.Namespace) -> int:
    selected = entries_by_id(args.ids, set(args.kinds) if args.kinds else None)
    rows = []
    for entry in selected:
        url = public_url(entry, args.base_url)
        row = {"id": entry.get("id"), "kind": entry.get("kind"), "surface": entry.get("surface"), "url": url}
        if args.probe:
            row["probe"] = probe_url(url)
        rows.append(row)
    print(json.dumps({"count": len(rows), "rows": rows}, indent=2))
    return 0


def cmd_publish_ig(args: argparse.Namespace) -> int:
    load_env()
    selected = entries_by_id(args.ids, set(args.kinds) if args.kinds else {"photo", "reel"})
    preview = [{"id": e.get("id"), "kind": e.get("kind"), "surface": e.get("surface"), "url": public_url(e, args.base_url)} for e in selected]
    if not args.confirm:
        print(json.dumps({"dry_run": True, "would_publish": preview, "note": "Add --confirm only after the profile/feed/reels publishing step is approved/authorised."}, indent=2))
        return 0
    token = publish_token()
    state = load_state()
    done_ids = {p.get("entry_id") for p in state.get("published", []) if p.get("published_media_id")}
    published = []
    for entry in selected:
        if entry.get("id") in done_ids and not args.republish:
            continue
        result = publish_entry(entry, args.base_url, token, timeout_seconds=args.timeout_seconds)
        state.setdefault("published", []).append(result)
        save_state(state)
        published.append(result)
    print(json.dumps({"published": published, "state_path": str(STATE_PATH)}, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    load_env()
    token = publish_token()
    state = load_state()
    expected = [p for p in state.get("published", []) if p.get("published_media_id")]
    expected_ids = {str(p["published_media_id"]) for p in expected}
    recent = graph("GET", f"{ig_user_id()}/media", token, params={"fields": "id,media_type,media_product_type,timestamp,permalink,caption,thumbnail_url,media_url", "limit": args.limit})
    rows = recent.get("data", [])
    seen = {str(row.get("id")) for row in rows}
    matches = [row for row in rows if str(row.get("id")) in expected_ids]
    missing = sorted(expected_ids - seen)
    print(json.dumps({"expected_count": len(expected_ids), "matched_count": len(matches), "missing_from_recent_window": missing, "matches": matches, "recent_count": len(rows)}, indent=2))
    return 1 if missing else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("print-urls")
    p.add_argument("--base-url", required=True)
    p.add_argument("--ids", nargs="*")
    p.add_argument("--kinds", nargs="*", choices=["photo", "reel", "story_image"])
    p.add_argument("--probe", action="store_true")
    p = sub.add_parser("publish-ig")
    p.add_argument("--base-url", required=True)
    p.add_argument("--ids", nargs="*")
    p.add_argument("--kinds", nargs="*", choices=["photo", "reel", "story_image"])
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--republish", action="store_true")
    p.add_argument("--timeout-seconds", type=int, default=300)
    p = sub.add_parser("verify")
    p.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    if args.cmd == "check":
        return cmd_check()
    if args.cmd == "print-urls":
        return cmd_print_urls(args)
    if args.cmd == "publish-ig":
        return cmd_publish_ig(args)
    if args.cmd == "verify":
        return cmd_verify(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
