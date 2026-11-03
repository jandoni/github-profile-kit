#!/usr/bin/env python3
"""Rounded pill buttons for the profile README, drawn as SVG.

Shields.io badges are square, and Simple Icons no longer has a LinkedIn logo,
so these are drawn here. An icon is one of the built-in glyphs (linkedin, globe,
scholar, grid) or any Simple Icons slug fetched into scripts/icons.json.

    python scripts/buttons.py [--config profile.json] [--assets assets]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from kit import ROOT, attr, colour, esc, icon, load_config, load_icons, write

H, PAD, ICON, GAP = 38, 16, 16, 9
CHAR_W = 7.7              # average width of a 13.5px semibold sans character
FONT = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
# Google Scholar glyph from Simple Icons (CC0), kept here so builds need no network.
SCHOLAR_PATH = "M5.242 13.769L0 9.5 12 0l12 9.5-5.242 4.269C17.548 11.249 14.978 9.5 12 9.5c-2.977 0-5.548 1.748-6.758 4.269zM12 10a7 7 0 1 0 0 14 7 7 0 0 0 0-14z"


def linkedin_icon(x: float, y: float, fg: str, bg: str) -> str:
    """Drawn by hand: a rounded square with "in" cut out in the button colour."""
    return (f'<rect x="{x}" y="{y}" width="{ICON}" height="{ICON}" rx="3" fill="{fg}"/>'
            f'<text x="{x + ICON / 2}" y="{y + 12.3}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
            f'font-weight="700" font-size="11" fill="{bg}">in</text>')


def grid_icon(x: float, y: float, fg: str, bg: str) -> str:
    """Four rounded squares: a simple 'projects' glyph."""
    g, gap = (ICON - 3) / 2, 3
    return "".join(f'<rect x="{x + cx * (g + gap):.1f}" y="{y + cy * (g + gap):.1f}" width="{g:.1f}" height="{g:.1f}" rx="1.8" '
                   f'fill="none" stroke="{fg}" stroke-width="1.5"/>' for cx in (0, 1) for cy in (0, 1))


def globe_icon(x: float, y: float, fg: str, bg: str) -> str:
    c, r = (x + ICON / 2, y + ICON / 2), ICON / 2 - 0.8
    s = f'stroke="{fg}" stroke-width="1.4" fill="none"'
    return (f'<circle cx="{c[0]}" cy="{c[1]}" r="{r}" {s}/>'
            f'<ellipse cx="{c[0]}" cy="{c[1]}" rx="{r * 0.45:.2f}" ry="{r}" {s}/>'
            f'<line x1="{x + 0.8}" y1="{c[1]}" x2="{x + ICON - 0.8}" y2="{c[1]}" {s}/>')


def path_icon(d: str):
    """A 24x24 Simple Icons path scaled to the icon size."""
    def draw(x: float, y: float, fg: str, bg: str) -> str:
        return f'<path transform="translate({x},{y}) scale({ICON / 24})" d="{d}" fill="{fg}"/>'
    return draw


BUILT_IN = {"linkedin": linkedin_icon, "globe": globe_icon, "grid": grid_icon, "scholar": path_icon(SCHOLAR_PATH)}


def render(label: str, draw_icon, bg: str, fg: str) -> str:
    text_w = len(label) * CHAR_W
    w = round(PAD + ICON + GAP + text_w + PAD)
    iy = (H - ICON) / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}" role="img" aria-label="{attr(label)}">
<rect width="{w}" height="{H}" rx="{H / 2}" fill="{bg}"/>
{draw_icon(PAD, iy, fg, bg)}
<text x="{PAD + ICON + GAP}" y="{H / 2 + 4.6}" font-family="{FONT}" font-size="13.5" font-weight="600" fill="{fg}">{esc(label)}</text>
</svg>
"""


def build(cfg: dict, assets: Path) -> list[Path]:
    bg, fg = colour(cfg, "accent"), colour(cfg, "on_accent")
    icons = load_icons()
    out = []
    for b in cfg.get("buttons", []):
        slug = b["icon"]
        draw = BUILT_IN.get(slug) or path_icon(icon(icons, slug)["path"])
        path = assets / "buttons" / f'{b["file"]}.svg'
        write(path, render(b["label"], draw, bg, fg))
        out.append(path)
    print(f"wrote {len(out)} buttons to {assets / 'buttons'}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="config file (default: profile.json, else profile.example.json)")
    ap.add_argument("--assets", type=Path, default=ROOT / "assets", help="output folder (default: assets/)")
    a = ap.parse_args()
    build(load_config(a.config), a.assets)
