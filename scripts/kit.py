"""Shared helpers for the generators: config, colours, paths, photos, fonts, icons.

Every script reads profile.json from the repository root, or profile.example.json
when profile.json doesn't exist. Pass --config to any script to use another file.
"""

from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS_FILE = ROOT / "scripts" / "icons.json"


def reduced_motion_css(typing_clips: str) -> str:
    """The header and the terminal animate with SMIL (<set>, <animate>), which a CSS
    "animation: none" rule doesn't stop. Under reduced motion this shows every element
    in its final state instead: hidden elements visible, typing clips removed, CSS
    animations (the snake) stopped. typing_clips is a selector for the typing clips."""
    return ('@media (prefers-reduced-motion: reduce){*{animation:none!important}'
            f'[opacity="0"]{{opacity:1!important}}{typing_clips}{{clip-path:none!important}}}}')


def config_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    own = ROOT / "profile.json"
    return own if own.exists() else ROOT / "profile.example.json"


def load_config(explicit: str | None = None) -> dict:
    path = config_path(explicit)
    if not path.exists():
        sys.exit(f"config not found: {path}")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["_base"] = str(path.parent)
    return cfg


def resolve(cfg: dict, value: str | None) -> Path | None:
    """A path from the config: ~ is expanded, relative paths start at the config file."""
    if not value:
        return None
    p = Path(value).expanduser()
    return p if p.is_absolute() else Path(cfg["_base"]) / p


def colour(cfg: dict, value: str | None, default: str = "ink") -> str:
    """A palette name (ink, accent, muted, ...) or a #hex value."""
    value = value or default
    if value.startswith("#"):
        return value
    found = cfg["palette"].get(value)
    if not isinstance(found, str):
        sys.exit(f'unknown colour "{value}": use a top-level palette name or a #hex value')
    return found


def esc(s: str) -> str:
    """Escape text content."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def attr(s: str) -> str:
    """Escape a double-quoted attribute value."""
    return esc(s).replace('"', "&quot;")


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def fit_aspect(im, ratio: float, anchor: str = "center"):
    """Crop to the slot's aspect ratio when the photo is more than 1% off it,
    so a photo of another shape isn't stretched. anchor: center or bottom."""
    r = im.width / im.height
    if abs(r - ratio) / ratio <= 0.01:
        return im
    if r > ratio:
        w = round(im.height * ratio)
        x = (im.width - w) // 2
        return im.crop((x, 0, x + w, im.height))
    h = round(im.width / ratio)
    y = im.height - h if anchor == "bottom" else (im.height - h) // 2
    return im.crop((0, y, im.width, y + h))


def jpeg_b64(path: Path, size: tuple[int, int], quality: int, crop=None, anchor: str = "center") -> str:
    """A photo as base64 JPEG: cropped (crop box [left, top, right, bottom], null for
    the image edge), fitted to the slot and resized to `size` pixels."""
    from PIL import Image

    im = Image.open(path).convert("RGB")
    if crop:
        left, top, right, bottom = crop
        im = im.crop((left or 0, top or 0, im.width if right is None else right, im.height if bottom is None else bottom))
    im = fit_aspect(im, size[0] / size[1], anchor)
    im = im.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode()


def css_family(name: str) -> str:
    return f'"{name}"' if " " in name else name


def font_face(cfg: dict, key: str) -> tuple[str, str]:
    """(@font-face rule or "", CSS family name) for fonts.<key> in the config.
    Without the font file the family name is still listed, and the system fonts
    after it in each stack take over."""
    font = cfg.get("fonts", {}).get(key) or {}
    family = font.get("family", "")
    path = resolve(cfg, font.get("file"))
    if not family:
        return "", ""
    if not path or not path.exists():
        warn(f"font file for {family} not found ({path}); the cards fall back to system fonts")
        return "", css_family(family)
    data = base64.b64encode(path.read_bytes()).decode()
    return (f'@font-face{{font-family:{css_family(family)};src:url(data:font/woff2;base64,{data}) format("woff2");'
            f'font-weight:100 900}}', css_family(family))


def load_icons() -> dict:
    if not ICONS_FILE.exists():
        return {}
    return json.loads(ICONS_FILE.read_text(encoding="utf-8")).get("icons", {})


def icon(icons: dict, slug: str) -> dict:
    if slug not in icons:
        sys.exit(f'no icon "{slug}" in scripts/icons.json: run python scripts/fetch_icons.py')
    return icons[slug]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
