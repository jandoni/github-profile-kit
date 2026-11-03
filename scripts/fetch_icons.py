#!/usr/bin/env python3
"""Fetch Simple Icons path data for every slug in the config (the terminal's
tools and any button icon that isn't built in) into scripts/icons.json.

    python scripts/fetch_icons.py [--config profile.json] [--version 16.36.0]

Slugs are the file names on https://simpleicons.org (lower case, no spaces:
"googlecloud", "apacheairflow"). Icons are CC0. The version is pinned so a
rebuild draws the same paths; pass --version latest to take the newest set.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

from buttons import BUILT_IN
from kit import ICONS_FILE, load_config

VERSION = "16.36.0"
URL = "https://cdn.jsdelivr.net/npm/simple-icons@{version}/icons/{slug}.svg"
# Some icon CDNs answer 403 to Python's default User-Agent.
HEADERS = {"User-Agent": "github-profile-kit/1.0"}


def slugs(cfg: dict) -> list[str]:
    wanted = [t["slug"] for t in cfg.get("terminal", {}).get("tools", [])]
    wanted += [b["icon"] for b in cfg.get("buttons", []) if b["icon"] not in BUILT_IN]
    return list(dict.fromkeys(wanted))


def fetch(slug: str, version: str) -> dict:
    req = urllib.request.Request(URL.format(version=version, slug=slug), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        svg = r.read().decode("utf-8")
    title = re.search(r"<title>(.*?)</title>", svg, re.S)
    path = re.search(r'<path d="([^"]+)"', svg)
    if not path:
        raise ValueError("no <path> in the SVG")
    return {"title": title.group(1) if title else slug, "path": path.group(1)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="config file (default: profile.json, else profile.example.json)")
    ap.add_argument("--version", default=VERSION, help=f"simple-icons version (default: {VERSION})")
    a = ap.parse_args()
    cfg = load_config(a.config)
    old = json.loads(ICONS_FILE.read_text(encoding="utf-8")).get("icons", {}) if ICONS_FILE.exists() else {}
    icons, failed = {}, []
    for slug in slugs(cfg):
        try:
            icons[slug] = fetch(slug, a.version)
            print(f"  {slug}: {icons[slug]['title']}")
        except (urllib.error.URLError, ValueError) as e:
            failed.append(slug)
            if slug in old:
                icons[slug] = old[slug]
            print(f"  {slug}: failed ({e}){', kept the old path' if slug in old else ''}", file=sys.stderr)
    data = {"source": URL.format(version=a.version, slug="<slug>"), "license": "CC0-1.0", "icons": icons}
    ICONS_FILE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(icons)} icons to {ICONS_FILE}")
    if failed:
        sys.exit(f"not found: {', '.join(failed)}. Check the slugs on https://simpleicons.org "
                 "(LinkedIn was removed from Simple Icons; use the built-in linkedin icon).")


if __name__ == "__main__":
    main()
