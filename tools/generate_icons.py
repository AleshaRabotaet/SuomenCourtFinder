#!/usr/bin/env python3
"""Regenerate docs/icons/*.png (home-screen / PWA icons).

Draws a flat tennis-ball icon in the app's accent green, at each size
iOS/Android expect. Run with `pip install pillow` then `python tools/generate_icons.py`.
Icons are full-bleed squares (no pre-baked rounded corners) since iOS and
Android each apply their own mask on top.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ACCENT = "#1d6f42"
BALL = "#d4f24c"
SEAM = "#ffffff"

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "icons"
SIZES = {
    "icon-192.png": 192,
    "icon-512.png": 512,
    "apple-touch-icon.png": 180,
}


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size), ACCENT)
    draw = ImageDraw.Draw(img)

    margin = round(size * 0.14)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=BALL)

    seam_width = max(1, round(size * 0.02))
    r = (size - 2 * margin) / 2
    cx = cy = size / 2
    # Two seam arcs, each bowing away from the ball's vertical center line.
    bbox_left = [cx - r * 1.35, cy - r, cx + r * 0.35, cy + r]
    bbox_right = [cx - r * 0.35, cy - r, cx + r * 1.35, cy + r]
    draw.arc(bbox_left, start=300, end=60, fill=SEAM, width=seam_width)
    draw.arc(bbox_right, start=120, end=240, fill=SEAM, width=seam_width)

    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, size in SIZES.items():
        icon = draw_icon(size)
        icon.save(OUT_DIR / filename)
        print(f"wrote {OUT_DIR / filename} ({size}x{size})")


if __name__ == "__main__":
    main()
