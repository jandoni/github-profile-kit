#!/usr/bin/env python3
"""Animated header: a photo on the right, the headline typed one character at a
time and the title line typed out under it. SVG + SMIL, so it plays inside
GitHub's <img> and stays sharp. Everything personal comes from profile.json.

    python scripts/header.py [--config profile.json] [--assets assets]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from kit import ROOT, attr, colour, esc, jpeg_b64, load_config, reduced_motion_css, resolve, warn, write

# Layout. The defaults fit two headline lines of about 30 characters each.
W, H = 1100, 260
TEXT_X, FIRST_BASELINE, LINE_HEIGHT, TITLE_GAP = 60, 112, 54, 46
HEADLINE_FONT = '46px Georgia,"Times New Roman",serif'
TITLE_FONT = '15px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif'
TITLE_CHAR_W = 7.6        # average width of a 15px sans character: one step of the title's typing clip
PHOTO_SCALE, PHOTO_QUALITY, PHOTO_FADE_W = 3, 78, 90     # 3x pixels for retina screens
START, PER_CHAR, LINE_PAUSE = 0.6, 0.05, 0.25            # seconds
TITLE_CLIP = '[clip-path="url(#rc)"]'                    # removed under reduced motion


def words(cfg: dict) -> list[list[tuple[str, str, bool]]]:
    """The headline as lines of (word, colour, italic). A run's text can hold several words."""
    lines = []
    for line in cfg["header"]["headline"]:
        lines.append([(word, colour(cfg, run.get("color")), bool(run.get("italic")))
                      for run in line for word in run["text"].split()])
    return lines


def alt_text(cfg: dict) -> str:
    h = cfg["header"]
    headline = " ".join(word for line in words(cfg) for word, _, _ in line)
    return h.get("alt") or f'{headline} {h["title"].rstrip(".")}.'


def photo(cfg: dict) -> str:
    h = cfg["header"]
    p = h.get("photo") or {}
    path = resolve(cfg, p.get("path"))
    if not path:
        return ""
    if not path.exists():
        warn(f"header photo not found ({path}); building the header without it")
        return ""
    pw = p.get("width", 344)
    b64 = jpeg_b64(path, (pw * PHOTO_SCALE, H * PHOTO_SCALE), PHOTO_QUALITY, crop=p.get("crop"), anchor="bottom")
    return (f'<image href="data:image/jpeg;base64,{b64}" x="{W - pw}" y="0" width="{pw}" height="{H}" preserveAspectRatio="xMidYMax slice" opacity="0">'
            '<animate attributeName="opacity" from="0" to="1" begin="0s" dur="1.4s" fill="freeze"/></image>'
            f'<rect x="{W - pw}" y="0" width="{PHOTO_FADE_W}" height="{H}" fill="url(#fade)"/>')


def render(cfg: dict) -> str:
    h = cfg["header"]
    hp = cfg["palette"].get("header", {})
    left, right = hp.get("paper_gradient", ["#e8e5e1", "#dfddd7"])
    fade = hp.get("photo_fade", "#e3e0dc")
    parts = [
        '<defs>'
        f'<linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="{left}"/><stop offset="1" stop-color="{right}"/></linearGradient>'
        f'<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{fade}"/><stop offset="1" stop-color="{fade}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="r"><rect width="{W}" height="{H}" rx="10"/></clipPath>'
        '</defs>',
        f'<style>.w{{font:{HEADLINE_FONT}}}.r{{font:{TITLE_FONT}}}{reduced_motion_css(TITLE_CLIP)}</style>',
        f'<g clip-path="url(#r)"><rect width="{W}" height="{H}" fill="url(#pg)"/>{photo(cfg)}</g>',
    ]
    # Type the headline one character at a time: each character is a <tspan> that a
    # <set> reveals, so proportional fonts never show half a letter.
    t = START
    lines = words(cfg)
    y = FIRST_BASELINE
    for line in lines:
        spans = []
        for wi, (word, fill, italic) in enumerate(line):
            style = ' font-style="italic"' if italic else ""
            for ch in word + (" " if wi < len(line) - 1 else ""):
                spans.append(f'<tspan fill="{fill}"{style} opacity="0">{esc(ch)}<set attributeName="opacity" to="1" begin="{t:.2f}s"/></tspan>')
                t += PER_CHAR
        parts.append(f'<text class="w" x="{TEXT_X}" y="{y}" xml:space="preserve">{"".join(spans)}</text>')
        t += LINE_PAUSE
        y += LINE_HEIGHT
    # The title types out behind a clip that widens in steps of one average character.
    title = h["title"]
    ty = y - LINE_HEIGHT + TITLE_GAP
    steps = ";".join(f"{j * TITLE_CHAR_W:.1f}" for j in range(len(title) + 1))
    parts.append(f'<clipPath id="rc"><rect x="{TEXT_X}" y="{ty - 16}" height="22" width="0">'
                 f'<animate attributeName="width" values="{steps}" calcMode="discrete" begin="{t + .3:.2f}s" dur="1.4s" fill="freeze"/></rect></clipPath>'
                 f'<g clip-path="url(#rc)"><text class="r" x="{TEXT_X}" y="{ty}" fill="{colour(cfg, "muted")}">{esc(title)}</text></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{attr(alt_text(cfg))}">' + "".join(parts) + "</svg>\n")


def build(cfg: dict, assets: Path) -> Path:
    out = assets / f'{cfg["header"].get("file", "header")}.svg'
    write(out, render(cfg))
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="config file (default: profile.json, else profile.example.json)")
    ap.add_argument("--assets", type=Path, default=ROOT / "assets", help="output folder (default: assets/)")
    a = ap.parse_args()
    build(load_config(a.config), a.assets)
