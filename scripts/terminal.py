#!/usr/bin/env python3
"""Terminal window for the profile README: the contribution snake and the tools
I use, framed as a short typed session. SVG + SMIL so it animates inside
GitHub's <img>. The daily workflow runs it after Platane/snk draws the snake:

    python scripts/terminal.py --snake dist/snake-light.svg --out dist/terminal.svg

The snake is nested as an inner <svg>. Its CSS (custom properties on :root,
classes .c/.s/.u and keyframes c*/s*/u*) is left untouched, so every class and
id of ours carries a "tm-" prefix.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from kit import ROOT, attr, colour, esc, icon, load_config, load_icons, reduced_motion_css, write

MONO = "Menlo, 'SF Mono', Consolas, 'DejaVu Sans Mono', monospace"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
CW = 8.1                       # monospace character width at 13.5px
W, PAD = 940, 30
COLS, ROW_H, ICON_SIZE = 7, 74, 30
TYPING_CLIPS = '[clip-path^="url(#tm-"]'


class Session:
    """Colours and prompt shared by the parts of the session."""

    def __init__(self, cfg: dict):
        t = cfg["terminal"]
        tp = cfg["palette"].get("terminal", {})
        self.prompt_text = t.get("prompt", "~ $ ")
        self.bg = colour(cfg, "paper")
        self.border = tp.get("border", "#d8d2c8")
        self.bar = tp.get("title_bar", "#ebe6de")
        self.out = tp.get("output", "#4a453f")
        self.title = tp.get("title", "#6b655e")
        self.prompt = colour(cfg, tp.get("prompt"), "accent")
        self.cmd = colour(cfg, tp.get("command"), "ink")
        self.icon = colour(cfg, tp.get("icons"), "accent")

    def typed(self, x: float, y: float, text: str, begin: float, cid: str) -> tuple[str, float]:
        """A prompt that appears, then a command that types out. Returns (svg, end time)."""
        cx = x + len(self.prompt_text) * CW
        steps = ";".join(f"{i * CW:.1f}" for i in range(len(text) + 1))
        dur = len(text) * 0.05
        svg = (f'<text class="tm-m" x="{x}" y="{y}" fill="{self.prompt}" opacity="0">{esc(self.prompt_text)}<set attributeName="opacity" to="1" begin="{begin:.2f}s"/></text>'
               f'<clipPath id="tm-{cid}"><rect x="{cx:.1f}" y="{y - 15}" height="20" width="0">'
               f'<animate attributeName="width" values="{steps}" calcMode="discrete" begin="{begin + .2:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
               f'<text class="tm-m" x="{cx:.1f}" y="{y}" fill="{self.cmd}" clip-path="url(#tm-{cid})">{esc(text)}</text>')
        return svg, begin + 0.2 + dur


def snake_block(s: Session, path: Path | None, x: float, y: float, width: float, begin: float) -> tuple[str, float]:
    if not path or not path.exists():
        return (f'<text class="tm-m" x="{x}" y="{y + 40}" fill="{s.out}">(the snake is drawn by the daily workflow)</text>', 40.0)
    src = path.read_text(encoding="utf-8")
    m = re.match(r'\s*<svg([^>]*)>(.*)</svg>\s*$', src, re.S)
    attrs, inner = m.group(1), m.group(2)
    vb = re.search(r'viewBox="([^"]+)"', attrs).group(1)
    vw, vh = (float(v) for v in vb.split()[2:4])
    height = width * vh / vw
    return (f'<g opacity="0"><set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<svg x="{x}" y="{y}" width="{width:.1f}" height="{height:.1f}" viewBox="{vb}">{inner}</svg></g>', height)


def tools_block(s: Session, tools: list[dict], x: float, y: float, width: float, begin: float) -> tuple[str, float, float]:
    cell = width / COLS
    parts = []
    for i, tool in enumerate(tools):
        r, c = divmod(i, COLS)
        cx, cy = x + c * cell + cell / 2, y + r * ROW_H
        t = begin + i * 0.07
        parts.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s"/>'
                     f'<path transform="translate({cx - ICON_SIZE / 2:.1f},{cy:.1f}) scale({ICON_SIZE / 24})" d="{tool["path"]}" fill="{s.icon}"/>'
                     f'<text class="tm-n" x="{cx:.1f}" y="{cy + ICON_SIZE + 17:.1f}" text-anchor="middle" fill="{s.out}">{esc(tool["name"])}</text></g>')
    rows = (len(tools) + COLS - 1) // COLS
    return "".join(parts), rows * ROW_H, begin + len(tools) * 0.07


def tools(cfg: dict) -> list[dict]:
    """The configured tools with their icon paths. A tool without a name uses Simple Icons' title."""
    icons = load_icons()
    out = []
    for t in cfg["terminal"].get("tools", []):
        found = icon(icons, t["slug"])
        out.append({"name": t.get("name") or found["title"], "path": found["path"]})
    return out


def render(cfg: dict, snake: Path | None) -> str:
    t_cfg = cfg["terminal"]
    s = Session(cfg)
    contrib = t_cfg.get("contributions", {})
    tool_list = tools(cfg)
    x = PAD
    parts = []
    y = 64
    svg, t = s.typed(x, y, contrib.get("command", "contributions --last-year"), 0.5, "a")
    parts.append(svg)
    snake_svg, snake_h = snake_block(s, snake, x - 8, y + 10, W - 2 * PAD + 16, t + 0.25)
    parts.append(snake_svg)
    y = y + 10 + snake_h + 14
    caption = contrib.get("caption", "Each square is a day of GitHub contributions.")
    parts.append(f'<text class="tm-m" x="{x}" y="{y}" fill="{s.out}" opacity="0">{esc(caption)}'
                 f'<set attributeName="opacity" to="1" begin="{t + 0.6:.2f}s"/></text>')
    y += 40
    svg, t2 = s.typed(x, y, t_cfg.get("tools_command", "tools"), t + 1.2, "b")
    parts.append(svg)
    tools_svg, tools_h, t3 = tools_block(s, tool_list, x, y + 18, W - 2 * PAD, t2 + 0.3)
    parts.append(tools_svg)
    y = y + 18 + tools_h + 18
    parts.append(f'<text class="tm-m" x="{x}" y="{y}" fill="{s.prompt}" opacity="0">{esc(s.prompt_text)}<set attributeName="opacity" to="1" begin="{t3 + 0.2:.2f}s"/></text>'
                 f'<rect x="{x + len(s.prompt_text) * CW:.1f}" y="{y - 13}" width="{CW:.1f}" height="16" fill="{s.prompt}" opacity="0">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" begin="{t3 + 0.2:.2f}s" repeatCount="indefinite"/></rect>')
    H = round(y + 26)
    frame = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8" fill="{s.bg}" stroke="{s.border}"/>'
             f'<rect x=".5" y=".5" width="{W - 1}" height="30" rx="8" fill="{s.bar}"/>'
             f'<rect x=".5" y="22" width="{W - 1}" height="9" fill="{s.bar}"/>'
             f'<line x1="0" y1="31" x2="{W}" y2="31" stroke="{s.border}"/>'
             f'<text x="{W / 2:.0f}" y="20" text-anchor="middle" fill="{s.title}" style="font:12px {SANS}">{esc(t_cfg.get("window_title", ""))}</text>')
    label = ("Terminal showing this year's GitHub contributions as a snake animation, and the tools I use: "
             f'{", ".join(t["name"] for t in tool_list)}.')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{attr(label)}">'
            f'<style>.tm-m{{font:13.5px {MONO};white-space:pre}}.tm-n{{font:11px {MONO}}}{reduced_motion_css(TYPING_CLIPS)}</style>'
            f'{frame}{"".join(parts)}</svg>\n')


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="config file (default: profile.json, else profile.example.json)")
    ap.add_argument("--snake", type=Path, help="snake SVG from Platane/snk (without it, a placeholder line)")
    ap.add_argument("--out", type=Path, default=ROOT / "dist" / "terminal.svg", help="output file (default: dist/terminal.svg)")
    a = ap.parse_args()
    write(a.out, render(load_config(a.config), a.snake))
    print(f"wrote {a.out}")
