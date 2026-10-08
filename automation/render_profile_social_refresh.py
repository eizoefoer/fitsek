#!/usr/bin/env python3
"""Render Fitsek profile, photoreal post, story, and reel assets.

The renderer is deterministic and uses existing faceless photoreal source photos in
this repo. It produces public social assets with Fitsek's dark mint/cyan/lime
brand direction, safe wellness copy, and no generated real-person claims.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site/assets/social/profile-refresh"
MANIFEST_PATH = ROOT / "content/social/profile-refresh-manifest.json"

DARK = "#05070c"
PANEL = "#0b1220"
MINT = "#42f5a7"
CYAN = "#42d9ff"
LIME = "#b9ff4a"
WHITE = "#f5f8ff"
MUTED = "#a9b7ca"

HASHTAGS = "#deskworkerfitness #bodyrecomposition #fatlossbasics #walkingpad #highprotein #fitsek"
DISCLAIMER = "General fitness education only. Results vary."


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    choices = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for choice in choices:
        if Path(choice).exists():
            return ImageFont.truetype(choice, size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: Any, max_width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = ""
        for word in words:
            test = (cur + " " + word).strip()
            if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


def cover_crop(img: Image.Image, size: tuple[int, int], x_bias: float = 0.5, y_bias: float = 0.5) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = img.resize((round(src_w * scale), round(src_h * scale)), Image.Resampling.LANCZOS)
    rw, rh = resized.size
    left = int((rw - target_w) * x_bias)
    top = int((rh - target_h) * y_bias)
    left = max(0, min(left, rw - target_w))
    top = max(0, min(top, rh - target_h))
    return resized.crop((left, top, left + target_w, top + target_h))


def gradient(size: tuple[int, int], top=(5, 7, 12, 80), bottom=(5, 7, 12, 230)) -> Image.Image:
    w, h = size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    if px is None:
        return overlay
    for y in range(h):
        t = y / max(1, h - 1)
        rgba = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(4))
        for x in range(w):
            px[x, y] = rgba
    return overlay


def glow_background(size: tuple[int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGBA", size, DARK)
    g = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(g, "RGBA")
    d.ellipse((-w * 0.25, -h * 0.15, w * 0.55, h * 0.45), fill=(66, 245, 167, 58))
    d.ellipse((w * 0.55, -h * 0.10, w * 1.20, h * 0.42), fill=(66, 217, 255, 52))
    d.ellipse((w * 0.18, h * 0.60, w * 1.15, h * 1.25), fill=(185, 255, 74, 34))
    g = g.filter(ImageFilter.GaussianBlur(max(52, int(w * 0.055))))
    return Image.alpha_composite(base, g)


def draw_brand_bar(draw: ImageDraw.ImageDraw, xy: tuple[int, int], scale: float = 1.0, invert: bool = False) -> None:
    x, y = xy
    mark = int(58 * scale)
    radius = int(16 * scale)
    draw.rounded_rectangle((x, y, x + mark, y + mark), radius=radius, fill=LIME if not invert else DARK)
    draw.text((x + int(19 * scale), y + int(5 * scale)), "F", font=font(int(38 * scale), True), fill=DARK if not invert else LIME)
    draw.text((x + mark + int(16 * scale), y + int(3 * scale)), "FITSEK", font=font(int(28 * scale), True), fill=WHITE if not invert else DARK)
    draw.text((x + mark + int(18 * scale), y + int(36 * scale)), "DESK-WORKER RECOMP", font=font(int(10 * scale), True), fill=MUTED if not invert else "#243021")


def draw_footer_note(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    draw.text((64, h - 78), DISCLAIMER, font=font(25), fill=(245, 248, 255, 205))


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: str = MINT) -> None:
    draw.text(xy, text.upper(), font=font(24, True), fill=color, spacing=4)


def caption(title: str, body: str, cta: str, instagram: bool = True) -> str:
    return "\n\n".join([
        title.rstrip(".") + ".",
        body.strip(),
        cta.strip(),
        HASHTAGS,
        DISCLAIMER,
    ])


@dataclass(frozen=True)
class SocialItem:
    item_id: str
    kind: str  # photo | reel | story_image
    title: str
    label: str
    hook: str
    body: str
    cta: str
    source: str
    filename: str
    cover_filename: str | None = None
    alt_text: str = "Faceless Fitsek lifestyle asset for general desk-worker fitness education."


PHOTO_ITEMS = [
    SocialItem(
        "photo-walking-pad",
        "photo",
        "Make steps boring enough to repeat",
        "01 / STEPS",
        "A walking pad works when it stops feeling special.",
        "Try one 10-minute walk after a meal, one easy meeting walk, and one shut-laptop lap. Small, repeatable steps beat a perfect plan you avoid.",
        "Save this and start with the easiest slot. Link in bio: fitsek.com",
        "site/assets/social/photoreal-desk-walking-pad.jpg",
        "photo-01-walking-pad.jpg",
    ),
    SocialItem(
        "photo-protein-anchors",
        "photo",
        "Two protein anchors beat perfect meal prep",
        "02 / PROTEIN",
        "Low appetite? Start with two reliable anchors.",
        "Pick one earlier meal and one later meal. Add easy carbs, colour, and a sauce you actually like. The default meal should be obvious on a work day.",
        "Save the template for your next shop. Link in bio: fitsek.com",
        "site/assets/social/photoreal-meal-prep-protein.jpg",
        "photo-02-protein-anchors.jpg",
    ),
    SocialItem(
        "photo-gym-progression",
        "photo",
        "Use one progression rule for 4 weeks",
        "03 / STRENGTH",
        "Random hard sets make progress hard to see.",
        "Keep the main lifts stable, stay 1-2 reps before form breaks, and add reps before load. Evidence beats novelty.",
        "Save this before changing the workout again. Link in bio: fitsek.com",
        "site/assets/social/photoreal-gym-progression.jpg",
        "photo-03-gym-progression.jpg",
    ),
    SocialItem(
        "photo-weekly-checkin",
        "photo",
        "Change one lever, not your whole life",
        "04 / REVIEW",
        "A useful Sunday check-in should feel boring.",
        "Look at steps, protein anchors, training, and sleep. Choose one lever for the next week. Measuring one change is easier than guessing at five.",
        "Save this for Sunday. Link in bio: fitsek.com",
        "site/assets/brand/photo-social-reset.jpg",
        "photo-04-weekly-checkin.jpg",
    ),
    SocialItem(
        "photo-build-base",
        "photo",
        "Build the base before cutting harder",
        "05 / BASE",
        "The harshest plan is rarely the most repeatable one.",
        "Before you cut harder, check the base: lift 2-3 times, walk most days, hit two protein anchors, and review the week honestly.",
        "Get the free 7-Day Desk Worker Recomp Reset. Link in bio: fitsek.com",
        "site/assets/social/photoreal-product-context.jpg",
        "photo-05-build-base.jpg",
    ),
    SocialItem(
        "photo-work-week-plan",
        "photo",
        "Your work week is the plan",
        "06 / FIT",
        "Fitsek is built for busy desk weeks, not fantasy weeks.",
        "Meetings, commutes, late meals, and low-energy days are constraints. Build around them with simple strength, steps, protein anchors, and review.",
        "Join the Fitsek list. Link in bio: fitsek.com",
        "site/assets/brand/photo-hero-workspace.jpg",
        "photo-06-work-week-plan.jpg",
    ),
]

REEL_ITEMS = [
    SocialItem(
        "reel-walking-pad",
        "reel",
        "Walking pad protocol",
        "REEL 01 / STEPS",
        "Make steps boring enough to repeat.",
        "10 minutes after one meal. One easy meeting walk. One shut-laptop lap. That is enough to start.",
        "Save this simple walking-pad protocol. Link in bio: fitsek.com",
        "site/assets/social/photoreal-desk-walking-pad.jpg",
        "reel-01-walking-pad.mp4",
        "reel-01-walking-pad-cover.jpg",
    ),
    SocialItem(
        "reel-protein-template",
        "reel",
        "Two protein anchors",
        "REEL 02 / PROTEIN",
        "Two anchors beat six theoretical meals.",
        "Pick one earlier protein anchor, one later protein anchor, and repeat them before chasing a perfect diet.",
        "Save the two-anchor template. Link in bio: fitsek.com",
        "site/assets/social/photoreal-meal-prep-protein.jpg",
        "reel-02-protein-template.mp4",
        "reel-02-protein-template-cover.jpg",
    ),
    SocialItem(
        "reel-weekly-checkin",
        "reel",
        "Sunday check-in",
        "REEL 03 / REVIEW",
        "Change one lever, not your whole life.",
        "Review steps, protein, training, and sleep. Choose one lever. Run the week. Review again.",
        "Save this for Sunday. Link in bio: fitsek.com",
        "site/assets/brand/photo-social-reset.jpg",
        "reel-03-weekly-checkin.mp4",
        "reel-03-weekly-checkin-cover.jpg",
    ),
]

STORY_ITEMS = [
    SocialItem(
        "story-steps",
        "story_image",
        "3-step walking pad reset",
        "STORY 01 / STEPS",
        "10 after one meal\nEasy meeting walk\nShut-laptop lap",
        "A small steps plan for real desk days.",
        "Link in bio: fitsek.com",
        "site/assets/social/photoreal-desk-walking-pad.jpg",
        "story-01-steps.jpg",
    ),
    SocialItem(
        "story-protein",
        "story_image",
        "2-anchor protein day",
        "STORY 02 / PROTEIN",
        "Earlier anchor\nLater anchor\nEasy carbs + colour",
        "Repeatable meals beat impressive meals.",
        "Link in bio: fitsek.com",
        "site/assets/social/photoreal-meal-prep-protein.jpg",
        "story-02-protein.jpg",
    ),
    SocialItem(
        "story-review",
        "story_image",
        "Sunday one-lever review",
        "STORY 03 / REVIEW",
        "Steps\nProtein\nTraining\nSleep",
        "Pick one lever. Do not reset your whole life.",
        "Link in bio: fitsek.com",
        "site/assets/brand/photo-social-reset.jpg",
        "story-03-review.jpg",
    ),
]


def render_photo_item(item: SocialItem, size=(1080, 1350)) -> Path:
    source = Image.open(ROOT / item.source).convert("RGB")
    img = cover_crop(source, size, y_bias=0.46).convert("RGBA")
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(0.94)
    img = Image.alpha_composite(img, gradient(size, top=(5, 7, 12, 28), bottom=(5, 7, 12, 238)))
    d = ImageDraw.Draw(img, "RGBA")
    w, h = size
    draw_brand_bar(d, (62, 58), scale=0.95)
    draw_label(d, (64, 185), item.label, color=MINT)
    title_font = font(70, True)
    y = 810
    for line in wrap(d, item.title, title_font, w - 128)[:4]:
        d.text((64, y), line, font=title_font, fill=WHITE)
        y += 80
    body_font = font(31)
    y += 18
    for line in wrap(d, item.body, body_font, w - 128)[:4]:
        d.text((66, y), line, font=body_font, fill=(245, 248, 255, 218))
        y += 43
    d.rounded_rectangle((64, h - 180, w - 64, h - 106), radius=37, fill=(185, 255, 74, 238))
    d.text((98, h - 161), "FITSEK.COM  ·  FREE 7-DAY RESET", font=font(31, True), fill=DARK)
    draw_footer_note(d, w, h)
    out = OUT / item.filename
    img.convert("RGB").save(out, quality=92, optimize=True)
    return out


def render_story_item(item: SocialItem) -> Path:
    size = (1080, 1920)
    source = Image.open(ROOT / item.source).convert("RGB")
    img = cover_crop(source, size, y_bias=0.46).convert("RGBA")
    img = Image.alpha_composite(img, gradient(size, top=(5, 7, 12, 42), bottom=(5, 7, 12, 248)))
    d = ImageDraw.Draw(img, "RGBA")
    w, h = size
    draw_brand_bar(d, (68, 70), scale=1.02)
    draw_label(d, (72, 250), item.label, color=CYAN)
    title_font = font(78, True)
    y = 450
    for line in wrap(d, item.title, title_font, w - 144)[:4]:
        d.text((72, y), line, font=title_font, fill=WHITE)
        y += 88
    d.rounded_rectangle((72, 930, w - 72, 1332), radius=44, fill=(5, 7, 12, 192), outline=(66, 245, 167, 94), width=2)
    bullet_font = font(42, True)
    by = 1002
    for idx, raw_line in enumerate(item.hook.split("\n"), 1):
        wrapped = wrap(d, raw_line, bullet_font, w - 330)[:2]
        d.text((118, by), f"0{idx}", font=font(30, True), fill=LIME)
        for line in wrapped:
            d.text((196, by - 8), line, font=bullet_font, fill=WHITE)
            by += 54
        by += 34
    d.rounded_rectangle((72, h - 318, w - 72, h - 222), radius=48, fill=(185, 255, 74, 238))
    d.text((126, h - 292), "LINK IN BIO: FITSEK.COM", font=font(38, True), fill=DARK)
    draw_footer_note(d, w, h)
    out = OUT / item.filename
    img.convert("RGB").save(out, quality=92, optimize=True)
    return out


def render_avatar_and_cover() -> list[dict]:
    assets: list[dict] = []
    # Avatar: high-contrast, small-size safe, and circular-crop safe.
    size = (1080, 1080)
    img = glow_background(size)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse((134, 134, 946, 946), fill=(185, 255, 74, 255))
    d.ellipse((170, 170, 910, 910), outline=(5, 7, 12, 78), width=8)
    d.text((371, 235), "F", font=font(500, True), fill=DARK)
    d.text((343, 759), "FITSEK", font=font(78, True), fill=DARK)
    d.text((358, 850), "RECOMP · RESET", font=font(28, True), fill="#26310d")
    avatar = OUT / "fitsek-avatar-square.png"
    img.convert("RGB").save(avatar, optimize=True)
    assets.append({"id": "profile-avatar", "kind": "profile_asset", "surface": "instagram_profile_picture", "path": str(avatar.relative_to(ROOT)), "note": "Manual/profile-update asset; Instagram Graph API does not expose profile-picture mutation."})

    # Facebook Page cover / generic social banner.
    cover_size = (1640, 924)
    source = Image.open(ROOT / "site/assets/brand/photo-hero-workspace.jpg").convert("RGB")
    cover = cover_crop(source, cover_size, x_bias=0.55, y_bias=0.5).convert("RGBA")
    cover = Image.alpha_composite(cover, gradient(cover_size, top=(5, 7, 12, 140), bottom=(5, 7, 12, 228)))
    d = ImageDraw.Draw(cover, "RGBA")
    draw_brand_bar(d, (86, 78), scale=1.18)
    d.text((90, 340), "Recomp that fits\nreal work weeks.", font=font(102, True), fill=WHITE, spacing=10)
    d.text((94, 620), "Strength · steps · protein anchors · weekly review", font=font(40), fill=(66, 245, 167, 238))
    d.rounded_rectangle((92, 750, 650, 830), radius=40, fill=(185, 255, 74, 238))
    d.text((134, 770), "FITSEK.COM", font=font(38, True), fill=DARK)
    banner = OUT / "fitsek-facebook-cover.jpg"
    cover.convert("RGB").save(banner, quality=92, optimize=True)
    assets.append({"id": "facebook-cover", "kind": "profile_asset", "surface": "facebook_page_cover", "path": str(banner.relative_to(ROOT)), "note": "Manual/profile-update asset; Graph cover-photo endpoint is read-only."})
    return assets


def render_reel_item(item: SocialItem) -> tuple[Path, Path]:
    # Cover/story frame with burnt-in captions. The mp4 applies subtle motion.
    cover_item = SocialItem(
        item_id=item.item_id + "-cover",
        kind="story_image",
        title=item.title,
        label=item.label,
        hook=item.hook,
        body=item.body,
        cta=item.cta,
        source=item.source,
        filename=item.cover_filename or item.filename.replace(".mp4", "-cover.jpg"),
    )
    cover = render_story_item(cover_item)
    out = OUT / item.filename
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-i",
        str(cover),
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t",
        "6",
        "-vf",
        "zoompan=z='min(zoom+0.00055,1.035)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=180:s=1080x1920:fps=30,format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)
    return out, cover


def render_all() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    entries.extend(render_avatar_and_cover())

    for item in PHOTO_ITEMS:
        out = render_photo_item(item)
        entries.append({
            "id": item.item_id,
            "kind": item.kind,
            "surface": "instagram_feed_photo",
            "path": str(out.relative_to(ROOT)),
            "caption": caption(item.title, item.body, item.cta),
            "alt_text": item.alt_text,
            "source_photo": item.source,
            "status": "ready_for_publish_or_schedule",
        })
    for item in STORY_ITEMS:
        out = render_story_item(item)
        entries.append({
            "id": item.item_id,
            "kind": item.kind,
            "surface": "instagram_story",
            "path": str(out.relative_to(ROOT)),
            "caption": caption(item.title, item.body, item.cta),
            "alt_text": item.alt_text,
            "source_photo": item.source,
            "status": "ready_for_publish_or_schedule",
        })
    for item in REEL_ITEMS:
        out, cover = render_reel_item(item)
        entries.append({
            "id": item.item_id,
            "kind": item.kind,
            "surface": "instagram_reel",
            "path": str(out.relative_to(ROOT)),
            "cover_path": str(cover.relative_to(ROOT)),
            "caption": caption(item.title, item.body, item.cta),
            "alt_text": item.alt_text,
            "source_photo": item.source,
            "duration_seconds": 6,
            "status": "ready_for_publish_or_schedule",
        })

    manifest = {
        "version": 1,
        "created_by": "automation/render_profile_social_refresh.py",
        "brand_direction": "dark Fitsek palette with mint/cyan/lime accents, editorial hierarchy, cinematic spacing, faceless photoreal source photos",
        "policy": {
            "faceless": True,
            "no_fake_testimonials": True,
            "no_before_after": True,
            "no_medical_or_guaranteed_outcomes": True,
            "profile_updates_need_manual_or_explicit_approval": True,
        },
        "publishing_note": "Use a public HTTPS base URL when publishing via Meta. Stories are generated as assets; keep approval-first behavior before any mutating Meta call.",
        "entries": entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST_PATH), "entries": len(entries), "asset_dir": str(OUT)}, indent=2))
    return manifest


def main() -> int:
    if "--help" in sys.argv or "-h" in sys.argv:
        print("usage: python3 automation/render_profile_social_refresh.py")
        return 0
    render_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
