#!/usr/bin/env python3
"""Build the static assets in one go: the header, the buttons and the cards.
The terminal is built by the daily workflow, because it holds the snake.

    python scripts/build.py                      # assets/header.svg, assets/buttons/, assets/cards/
    python scripts/build.py --readme README.md   # also fill in templates/README.md from the config

The README template is plain HTML with {{...}} values:
  - a line with {{button.*}} repeats once per button, joined by &nbsp; ("hidden": true skips one)
  - a <p> block with {{card.*}} repeats once per pair of cards, with &nbsp;&nbsp;&nbsp; between the two
  - the leading <!-- ... --> comment (the instructions) is dropped
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import buttons
import cards
import header
import terminal
from kit import ROOT, attr, load_config, write

TEMPLATE = ROOT / "templates" / "README.md"


def readme_values(cfg: dict) -> dict:
    user = cfg["github_username"]
    t = cfg.get("terminal", {})
    names = [tool["name"] for tool in terminal.tools(cfg)]
    tool_text = "".join(names) if len(names) < 2 else f'{", ".join(names[:-1])} and {names[-1]}'
    alt = t.get("alt", "Terminal: this year's GitHub contributions as a snake animation, each square a day of "
                       "contributions; then the tools I use: {tools}.")
    return {
        "username": user,
        "header.link": cfg["header"].get("link", f"https://github.com/{user}"),
        "header.file": cfg["header"].get("file", "header"),
        "header.alt": attr(header.alt_text(cfg)),
        "terminal.link": t.get("link", f"https://github.com/{user}?tab=repositories"),
        "terminal.alt": attr(alt.replace("{tools}", tool_text)),
        "cards.heading": (cfg.get("cards") or {}).get("heading", "Publications"),
    }


def fill(text: str, values: dict, prefix: str = "") -> str:
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in values:
            raise SystemExit(f"templates/README.md: no value for {{{{{prefix}{key}}}}}")
        return str(values[key])
    return re.sub(r"\{\{" + re.escape(prefix) + r"([\w.]+)\}\}", sub, text)


def render_readme(cfg: dict, template: str) -> str:
    text = re.sub(r"\A<!--.*?-->\n", "", template, flags=re.S)
    # One line per button.
    def button_lines(m: re.Match) -> str:
        line = m.group(0)
        return "&nbsp;\n".join(fill(line, {"url": b["url"], "file": b["file"], "alt": attr(b.get("alt", b["label"]))}, "button.")
                               for b in cfg.get("buttons", []) if not b.get("hidden"))
    text = re.sub(r"^.*\{\{button\..*$", button_lines, text, flags=re.M)
    # One <p> block per pair of cards.
    items = (cfg.get("cards") or {}).get("items", [])
    def card_rows(m: re.Match) -> str:
        open_tag, line, close_tag = m.group(1), m.group(2), m.group(3)
        rows = []
        for i in range(0, len(items), 2):
            pair = [fill(line, {"url": c["url"], "file": c["file"], "alt": attr(c.get("alt", c["title"]))}, "card.")
                    for c in items[i:i + 2]]
            rows.append(f"{open_tag}\n" + "&nbsp;&nbsp;&nbsp;\n".join(pair) + f"\n{close_tag}")
        return "\n\n".join(rows)
    text = re.sub(r"^(<p[^>]*>)\n(.*\{\{card\..*)\n(</p>)$", card_rows, text, flags=re.M)
    return fill(text, readme_values(cfg))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="config file (default: profile.json, else profile.example.json)")
    ap.add_argument("--assets", type=Path, default=ROOT / "assets", help="output folder (default: assets/)")
    ap.add_argument("--readme", type=Path, help="also render templates/README.md to this file")
    a = ap.parse_args()
    cfg = load_config(a.config)
    header.build(cfg, a.assets)
    buttons.build(cfg, a.assets)
    cards.build(cfg, a.assets)
    if a.readme:
        write(a.readme, render_readme(cfg, TEMPLATE.read_text(encoding="utf-8")))
        print(f"wrote {a.readme}")
    user = cfg["github_username"]
    print(f"terminal (built daily by the workflow): https://raw.githubusercontent.com/{user}/{user}/output/terminal.svg")


if __name__ == "__main__":
    main()
