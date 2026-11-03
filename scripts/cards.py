#!/usr/bin/env python3
"""Cards for the profile README (publications, projects, talks): a dark rounded
card with an inset photo or a typographic panel, a title, short text, a small
label and a pill button. GitHub strips CSS from READMEs, so each card is an SVG
with its photo and fonts embedded.

    python scripts/cards.py [--config profile.json] [--assets assets]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from kit import ROOT, attr, esc, font_face, jpeg_b64, load_config, resolve, warn, write

W, H, PAD = 460, 548, 16
PHOTO_H, PHOTO_SCALE, PHOTO_QUALITY = 214, 2, 76      # 2x pixels for retina screens
TITLE_CHARS, TITLE_LINES, BODY_CHARS, BODY_LINES = 31, 2, 50, 4
PILL_CHAR_W = 8.3
SANS_FALLBACK = '-apple-system,"Segoe UI",Helvetica,Arial,sans-serif'
MONO_FALLBACK = "Menlo,Consolas,monospace"
PANEL_FONT = "Georgia, serif"


def palette(cfg: dict) -> dict:
    p = {"background": "#1c1b1f", "border": "#2e2d33", "title": "#f3efe8", "body": "#c6c0b6", "label": "#c8895a",
         "pill": "#efe8dc", "pill_text": "#1c1b1f", "panel": "#2a2421", "panel_note": "#8f877c"}
    p.update(cfg["palette"].get("cards", {}))
    return p


def wrap(text: str, max_chars: int, max_lines: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if len(trial) <= max_chars or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,:;") + "…"
    return lines


def media(cfg: dict, card: dict, p: dict) -> str:
    pw, ph = W - 2 * PAD, PHOTO_H
    path = resolve(cfg, card.get("photo"))
    if path and path.exists():
        b64 = jpeg_b64(path, (int(pw * PHOTO_SCALE), int(ph * PHOTO_SCALE)), PHOTO_QUALITY)
        return (f'<image href="data:image/jpeg;base64,{b64}" x="{PAD}" y="{PAD}" width="{pw}" height="{ph}" '
                f'preserveAspectRatio="xMidYMid slice" clip-path="url(#ph)"/>')
    if path:
        warn(f'photo for card "{card["file"]}" not found ({path}); using a plain panel')
    panel = card.get("panel") or {}
    big, small = panel.get("headline", ""), panel.get("note", "")
    return (f'<rect x="{PAD}" y="{PAD}" width="{pw}" height="{ph}" rx="16" fill="{p["panel"]}"/>'
            f'<text x="{PAD + 28}" y="{PAD + ph / 2 + 6}" font-family="{PANEL_FONT}" font-style="italic" font-size="40" fill="{p["label"]}">{esc(big)}</text>'
            f'<text x="{PAD + 30}" y="{PAD + ph / 2 + 38}" class="mono" fill="{p["panel_note"]}">{esc(small.upper())}</text>')


def render(cfg: dict, card: dict, fonts_css: str, sans: str, mono: str) -> str:
    p = palette(cfg)
    sans_stack = f"{sans},{SANS_FALLBACK}" if sans else SANS_FALLBACK
    mono_stack = f"{mono},{MONO_FALLBACK}" if mono else MONO_FALLBACK
    y = PAD + PHOTO_H + 44
    parts = [media(cfg, card, p)]
    for line in wrap(card["title"], TITLE_CHARS, TITLE_LINES):
        parts.append(f'<text x="{PAD + 10}" y="{y}" class="title">{esc(line)}</text>')
        y += 30
    y += 4
    for line in wrap(card["body"], BODY_CHARS, BODY_LINES):
        parts.append(f'<text x="{PAD + 10}" y="{y}" class="body">{esc(line)}</text>')
        y += 23
    parts.append(f'<text x="{PAD + 10}" y="{y + 18}" class="mono">{esc(card["label"].upper())}</text>')
    label = f'{card["button"]}  ↗'
    bw = len(label) * PILL_CHAR_W + 44
    bx, by = W - PAD - 10 - bw, H - PAD - 10 - 46
    parts.append(f'<rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="46" rx="23" fill="{p["pill"]}"/>'
                 f'<text x="{bx + bw / 2:.1f}" y="{by + 29}" text-anchor="middle" class="pill">{esc(label)}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{attr(card["title"])}">'
            f'<defs><clipPath id="ph"><rect x="{PAD}" y="{PAD}" width="{W - 2 * PAD}" height="{PHOTO_H}" rx="16"/></clipPath></defs>'
            f'<style>{fonts_css}'
            f'.title{{font:600 23px {sans_stack};fill:{p["title"]};letter-spacing:-.2px}}'
            f'.body{{font:400 15px {sans_stack};fill:{p["body"]}}}'
            f'.mono{{font:500 11.5px {mono_stack};fill:{p["label"]};letter-spacing:.9px}}'
            f'.pill{{font:500 14.5px {sans_stack};fill:{p["pill_text"]}}}</style>'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="24" fill="{p["background"]}" stroke="{p["border"]}"/>'
            f'{"".join(parts)}</svg>\n')


def build(cfg: dict, assets: Path) -> list[Path]:
    items = (cfg.get("cards") or {}).get("items", [])
    if not items:
        return []
    sans_css, sans = font_face(cfg, "sans")
    mono_css, mono = font_face(cfg, "mono")
    out = []
    for card in items:
        path = assets / "cards" / f'{card["file"]}.svg'
        write(path, render(cfg, card, sans_css + mono_css, sans, mono))
        out.append(path)
    print(f"wrote {len(out)} cards to {assets / 'cards'}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="config file (default: profile.json, else profile.example.json)")
    ap.add_argument("--assets", type=Path, default=ROOT / "assets", help="output folder (default: assets/)")
    a = ap.parse_args()
    build(load_config(a.config), a.assets)
