#!/usr/bin/env python3
"""Preview the profile locally before pushing: renders templates/README.md with
your config into dist/preview.html, laid out roughly the way GitHub shows a
profile README, using the local assets and dist/terminal.svg.

    python scripts/build.py && python scripts/terminal.py --snake snake.svg
    python scripts/preview.py                          # open dist/preview.html
    python scripts/preview.py --png docs/preview.png --gif docs/header.gif

--png and --gif need Playwright (pip install playwright && playwright install chromium).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from build import TEMPLATE, render_readme
from kit import ROOT, load_config, write

PAGE = """<!doctype html><meta charset="utf-8"><title>Profile preview</title>
<style>
body{{margin:0;background:#fff;font:16px/1.5 -apple-system,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif;color:#1f2328}}
.box{{width:{width}px;margin:24px auto;border:1px solid #d0d7de;border-radius:6px}}
.bar{{padding:8px 16px;border-bottom:1px solid #d0d7de;font:12px ui-monospace,Menlo,monospace;color:#59636e}}
.md{{padding:32px}} .md p{{margin:0 0 16px}} .md img{{max-width:100%;vertical-align:middle;border:0}}
.md h3{{font-size:1.25em;font-weight:600;line-height:1.25;margin:24px 0 16px}}
</style>
<div class="box"><div class="bar">{user} / README.md</div><div class="md">
{body}
</div></div>
"""


def to_html(markdown: str, assets: Path, terminal: Path) -> str:
    """Just enough Markdown for the template: ### headings, raw HTML, paragraphs."""
    blocks = []
    for block in re.split(r"\n\s*\n", markdown.strip()):
        if block.startswith("### "):
            blocks.append(f"<h3>{block[4:]}</h3>")
        elif block.startswith("<p"):
            blocks.append(block)
        else:
            blocks.append(f"<p>{block}</p>")
    html = "\n".join(blocks)
    html = re.sub(r'src="https://raw\.githubusercontent\.com/[^"]*/output/terminal\.svg[^"]*"', f'src="{terminal.as_uri()}"', html)
    return html.replace('src="assets/', f'src="{assets.as_uri()}/')


def png(page_file: Path, out: Path, wait: float, scale: float) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1012, "height": 900}, device_scale_factor=scale)
        pg.goto(page_file.as_uri())
        pg.wait_for_timeout(wait * 1000)
        pg.locator(".box").screenshot(path=str(out))
        b.close()
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


def gif(header: Path, out: Path, frames: int = 20, width: int = 880) -> None:
    """The header typing out, frame by frame: pauses the SMIL timeline at evenly
    spaced times so every frame is exact, then holds the last one."""
    from PIL import Image
    from playwright.sync_api import sync_playwright
    end = 5.6
    times = [end * i / (frames - 1) for i in range(frames)]
    shots = out.with_suffix(".frames")
    shots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1100, "height": 260})
        pg.goto(header.as_uri())
        pg.wait_for_timeout(500)
        for i, t in enumerate(times):
            pg.evaluate(f"document.documentElement.pauseAnimations(); document.documentElement.setCurrentTime({t})")
            pg.wait_for_timeout(60)
            pg.screenshot(path=str(shots / f"{i:02d}.png"))
        b.close()
    ims = []
    for i in range(frames):
        im = Image.open(shots / f"{i:02d}.png").convert("RGB")
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        ims.append(im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    step = round(end / (frames - 1) * 1000)
    ims[0].save(out, save_all=True, append_images=ims[1:], duration=[step] * (frames - 1) + [3000], loop=0, optimize=True)
    for f in shots.iterdir():
        f.unlink()
    shots.rmdir()
    kept = Image.open(out).n_frames      # identical neighbours are merged into one longer frame
    print(f"wrote {out} ({out.stat().st_size // 1024} KB, {kept} frames)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="config file (default: profile.json, else profile.example.json)")
    ap.add_argument("--assets", type=Path, default=ROOT / "assets", help="built assets (default: assets/)")
    ap.add_argument("--terminal", type=Path, default=ROOT / "dist" / "terminal.svg", help="built terminal (default: dist/terminal.svg)")
    ap.add_argument("--out", type=Path, default=ROOT / "dist" / "preview.html")
    ap.add_argument("--png", type=Path, help="also save a screenshot (needs Playwright)")
    ap.add_argument("--gif", type=Path, help="also save the header typing as a GIF (needs Playwright)")
    ap.add_argument("--wait", type=float, default=8, help="seconds to let the animations play before the screenshot")
    ap.add_argument("--scale", type=float, default=2, help="device pixel ratio of the screenshot")
    a = ap.parse_args()
    cfg = load_config(a.config)
    body = to_html(render_readme(cfg, TEMPLATE.read_text(encoding="utf-8")), a.assets.resolve(), a.terminal.resolve())
    write(a.out, PAGE.format(width=880, user=cfg["github_username"], body=body))
    print(f"wrote {a.out}")
    if a.png:
        png(a.out.resolve(), a.png, a.wait, a.scale)
    if a.gif:
        gif(a.assets.resolve() / f'{cfg["header"].get("file", "header")}.svg', a.gif)


if __name__ == "__main__":
    main()
