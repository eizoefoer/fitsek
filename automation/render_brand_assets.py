#!/usr/bin/env python3
"""Render Fitsek brand icons and optimize approved faceless photo assets.

Inputs are locally generated/approved source images. The script keeps the public
site assets deterministic after those inputs are selected; it does not call any
paid or remote image APIs.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "assets" / "brand"
SITE = ROOT / "site"

VOLT = "#b9ff4a"
MINT = "#42f5a7"
CYAN = "#42d9ff"
BLUE = "#5b8cff"
BG = "#05070c"
PANEL = "#0d1422"
TEXT = "#f5f8ff"
MUTED = "#a9b7ca"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def write_svgs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mark = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="Fitsek mark">
  <defs>
    <linearGradient id="fitsek-g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{VOLT}"/>
      <stop offset="0.42" stop-color="{MINT}"/>
      <stop offset="0.74" stop-color="{CYAN}"/>
      <stop offset="1" stop-color="{BLUE}"/>
    </linearGradient>
  </defs>
  <rect x="8" y="8" width="112" height="112" rx="31" fill="url(#fitsek-g)"/>
  <path d="M39 34h56v17H59v17h31v16H59v30H39V34Z" fill="{BG}"/>
</svg>
'''
    logo = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 128" role="img" aria-label="Fitsek logo">
  <defs>
    <linearGradient id="fitsek-g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{VOLT}"/>
      <stop offset="0.42" stop-color="{MINT}"/>
      <stop offset="0.74" stop-color="{CYAN}"/>
      <stop offset="1" stop-color="{BLUE}"/>
    </linearGradient>
  </defs>
  <rect x="8" y="8" width="112" height="112" rx="31" fill="url(#fitsek-g)"/>
  <path d="M39 34h56v17H59v17h31v16H59v30H39V34Z" fill="{BG}"/>
  <text x="146" y="83" fill="{TEXT}" font-family="Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="62" font-weight="900" letter-spacing="-3">Fitsek</text>
</svg>
'''
    (OUT / "fitsek-mark.svg").write_text(mark, encoding="utf-8")
    (OUT / "fitsek-logo.svg").write_text(logo, encoding="utf-8")
    (SITE / "favicon.svg").write_text(mark, encoding="utf-8")


def gradient(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size), BG)
    px = img.load()
    assert px is not None
    stops = [(185, 255, 74), (66, 245, 167), (66, 217, 255), (91, 140, 255)]
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            scaled = t * (len(stops) - 1)
            i = min(int(scaled), len(stops) - 2)
            f = scaled - i
            c = tuple(int(stops[i][j] * (1 - f) + stops[i + 1][j] * f) for j in range(3))
            px[x, y] = c
    return img


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def draw_mark(size: int) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mark_size = int(size * 0.86)
    offset = (size - mark_size) // 2
    grad = gradient(mark_size).convert("RGBA")
    mask = rounded_mask(mark_size, int(mark_size * 0.25))
    canvas.alpha_composite(Image.composite(grad, Image.new("RGBA", (mark_size, mark_size), (0, 0, 0, 0)), mask), (offset, offset))
    d = ImageDraw.Draw(canvas)
    fnt = font(int(size * 0.55), True)
    bbox = d.textbbox((0, 0), "F", font=fnt)
    d.text(((size - (bbox[2] - bbox[0])) / 2 - size * 0.01, (size - (bbox[3] - bbox[1])) / 2 - size * 0.08), "F", font=fnt, fill=BG)
    return canvas


def write_icons() -> None:
    for name, size in [("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)]:
        draw_mark(size).save(SITE / name)
    draw_mark(256).save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)])


def cover(im: Image.Image, size: tuple[int, int], center_y: float = 0.5) -> Image.Image:
    im = im.convert("RGB")
    target_w, target_h = size
    ratio = max(target_w / im.width, target_h / im.height)
    resized = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, min(resized.height - target_h, round((resized.height - target_h) * center_y)))
    return resized.crop((left, top, left + target_w, top + target_h))


def save_photo(src: Path, stem: str, size: tuple[int, int], center_y: float = 0.5) -> None:
    if not src:
        return
    im = cover(Image.open(src), size, center_y=center_y)
    im.save(OUT / f"{stem}.jpg", quality=88, optimize=True, progressive=True)
    im.save(OUT / f"{stem}.webp", quality=82, method=6)


def make_og(hero_src: Path) -> None:
    hero = cover(Image.open(hero_src), (1200, 630), center_y=0.48).convert("RGBA")
    overlay = Image.new("RGBA", hero.size, (5, 7, 12, 0))
    d = ImageDraw.Draw(overlay, "RGBA")
    d.rectangle((0, 0, 1200, 630), fill=(5, 7, 12, 105))
    d.rectangle((0, 0, 680, 630), fill=(5, 7, 12, 165))
    d.rounded_rectangle((64, 64, 154, 154), radius=24, fill=(185, 255, 74, 255))
    d.text((96, 73), "F", font=font(58, True), fill=(5, 7, 12, 255))
    d.text((178, 83), "FITSEK", font=font(42, True), fill=(245, 248, 255, 255))
    d.text((64, 224), "Recomp that fits\nreal work weeks.", font=font(68, True), fill=(245, 248, 255, 255), spacing=4)
    d.text((66, 456), "Strength • steps • protein • weekly review", font=font(30), fill=(66, 245, 167, 255))
    out = Image.alpha_composite(hero, overlay).convert("RGB")
    out.save(OUT / "og-fitsek-site.png", quality=90, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hero-source", type=Path, required=True)
    parser.add_argument("--social-source", type=Path, required=True)
    parser.add_argument("--product-source", type=Path, required=True)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    write_svgs()
    write_icons()
    save_photo(args.hero_source, "photo-hero-workspace", (1440, 960), center_y=0.48)
    save_photo(args.social_source, "photo-social-reset", (1080, 1080), center_y=0.5)
    save_photo(args.product_source, "photo-product-system", (1440, 960), center_y=0.5)
    make_og(args.hero_source)
    print(f"rendered Fitsek brand assets to {OUT}")


if __name__ == "__main__":
    main()
