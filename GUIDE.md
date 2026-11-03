# How I built this

This is the story behind my GitHub profile: where it started, what GitHub lets a README do, how each piece works, what I threw away, and the rules I kept to. The kit in this repository is the result, cleaned up so it runs from a config file instead of from constants in my scripts.

## Starting point

My profile was empty: no bio, no README, just a list of repositories. Before drawing anything I read a lot of other people's profile READMEs. Most of them are built from the same parts: a stats card, a "top languages" card, a streak counter, a row of badges and a typing line.

I tried the stats cards first, because they promise something useful: a summary of your work. The public github-readme-stats instance answered with a 503 and `DEPLOYMENT_PAUSED`. Another service, GitHub Stats Extended, did load, and it told visitors I was "Rank C" with 31 commits. That number is true for my public repositories and wrong about my year, because most of my work is in private repositories that the card can't see. The contribution calendar on the same page said about 480, because GitHub counts private contributions there, anonymously. A card that undercounts me by an order of magnitude, just above a calendar that contradicts it, is worse than no card. I dropped the stats cards and decided to draw my own pieces.

## What GitHub lets a README do

A profile README goes through GitHub's HTML sanitizer, and most of what you'd use to design a page doesn't survive it:

- `<style>` blocks, `style` attributes and `class` attributes are stripped, so there is no CSS at all.
- `target="_blank"` is stripped, so every link opens in the same tab.
- The README itself can't have a background colour or image.

What does survive is images, and an SVG is an image. Inside an `<img>`, an SVG can carry its own `<style>` block and animate, both with SMIL (`<set>`, `<animate>`) and with CSS keyframes. What it can't do is load anything from outside: no web fonts by URL, no linked photos. So every photo and every custom font is embedded as base64, and anything not embedded uses a system font stack (Georgia for the headline, Menlo for the terminal, the platform's sans for the rest). In practice everything visual on my profile is an SVG, and the README is a thin layer of links around them.

A few more rules I learned the slow way:

- `align="left"` on an image, followed by `<br clear="left">`, is the only two-column layout. I used it for a while for a card on the left and tool icons on the right.
- `<picture>` with `prefers-color-scheme` sources is how you serve a different image in dark mode.
- GitHub proxies and caches images hard. For a file in the repository, the raw redirect drops the query string, so adding `?v=2` changes nothing. When I changed an image, I gave it a new file name. My cards went from `pub-*.svg` to `publication-*.svg` for exactly that reason.
- Wrap every image in a link. An image without one opens the raw file when someone clicks it.

## The header

The header is the skyline from my LinkedIn banner: the banner is 3168 by 792 pixels, and the crop box takes the right third, which has no text on it. The photo is resized to three times its slot so it stays sharp on high-density screens, and a gradient at its left edge blends it into the paper.

The first version showed the headline word by word and typed only the line under it, using a clip rectangle that widens by one average character width per step. That trick is fine for a 15-pixel line. For the 46-pixel Georgia headline I wanted real letter-by-letter typing, and a fixed-step clip doesn't work with a proportional font: an "m" is about three times as wide as an "i", so the clip lands in the middle of letters and the rhythm looks uneven. So each headline character is its own `<tspan>`, hidden, with a `<set>` that shows it at its moment. The small line under it still uses the clip, and if you step through `docs/header.gif` you can catch half an "m" for one frame.

That line is just `header.title` in the config. When my title changed, I edited one string and renamed the output file so GitHub's cache couldn't keep serving the old header.

## The buttons

I started with Shields.io badges. They are square, which fought the rounded header and cards, and Simple Icons, the icon set Shields uses, removed the LinkedIn logo, so the LinkedIn badge had no icon. I tried text-only badges for consistency and still didn't like them. Now the buttons are drawn here: a copper pill, a white icon, a label. The LinkedIn glyph is drawn by hand (a rounded square with "in" cut out in the button colour); the Google Scholar and GitHub glyphs are Simple Icons paths.

## The terminal

The first terminal typed a short session: `whoami`, `cat career.txt`, `ls building/`. It sat on the left with the tool icons to its right. It looked good, and it repeated what my bio and the profile sidebar already say, so I cut it. The terminal now frames the two things the sidebar can't show: the contribution snake and the tools I use, as two typed commands with a blinking cursor at the end.

The snake is nested inside the terminal as an inner `<svg>`. Its CSS sets custom properties on `:root` and uses the classes `.c`, `.s` and `.u` with keyframes named `c0`, `s0` and so on, which would collide with any short name of mine. Every class and id I add starts with `tm-`, and the snake's CSS stays untouched.

## The snake

[Platane/snk](https://github.com/Platane/snk) draws a snake that eats your contribution calendar. I gave it the copper palette: five dot shades from paper to dark copper, and the snake in the accent colour.

It is generated every day in GitHub Actions rather than on my laptop. The calendar changes daily, and in Actions the job runs on GitHub's servers with only the temporary `GITHUB_TOKEN` that each run receives. There is no personal token to create, store or leak, and the profile updates whether or not my laptop is open. The same workflow then runs `terminal.py` and publishes both files to an `output` branch, which the README loads by absolute URL.

## The cards

The publication and award cards match the project cards on my portfolio: a dark rounded card, an inset photo with rounded corners, a title in Geist, a short paragraph, a small copper label in Geist Mono and a cream pill. GitHub can't load the portfolio's fonts, so each card embeds both as base64 woff2, about 52 KB of font, plus its photo as a JPEG at twice its size. A card ends up around 125 KB. There is no grid either, so two cards sit in a centred paragraph at 48% width each, with three non-breaking spaces between them.

## What I tried and dropped

- **An animated contribution heatmap.** I drew my own calendar in copper: cells filled in week by week, a paper plane flew across the year, and the eight busiest days lit up as it passed. It played once. It was also a paper plane, which is decoration, and I kept the idea of a living calendar through the snake instead.
- **A neofetch-style card** with an ASCII portrait next to a list of facts about me.
- **An ASCII contribution skyline**, the calendar drawn as buildings.
- **An ASCII Chicago skyline** as the header.
- **A typing line** from readme-typing-svg, cycling through my career in a serif.

The reasons were mostly taste. The brief I gave myself was black and copper on warm paper, real photography, and nothing that reads as generated decoration: no particles, glowing nodes or ASCII art used as ornament. The ASCII ideas were clever, and they were exactly that kind of ornament. The other reason was dependence. The typing line came from someone else's server, and so did the stats card that was already down. Today the profile is static files in my repository plus one scheduled Action.

## Accessibility and restraint

Every image has alt text that says what it shows, including the full list of tools in the terminal, since none of that text is readable inside an image. The header and the typed commands play once and stay; the only loops are the terminal's cursor and the snake.

Reduced motion took two tries. My first rule was `*{animation:none}` inside a `prefers-reduced-motion` media query. It stops CSS animations, but the typing is SMIL, and SMIL ignores it: with reduced motion forced in Chromium, my header still typed itself out. The kit's rule shows everything in its final state instead. Hidden elements are made visible, the typing clips are removed, and CSS animations stop, which parks the snake. In the same test the header and terminal now appear complete and still. Whether a browser passes the setting into an image is up to the browser; Chromium does.

## Privacy

The calendar counts my private contributions, but only as numbers on days. The snake eats the same squares and never names a repository, and nothing in the kit asks for private data. There are no secrets in the repository: the workflow uses only `GITHUB_TOKEN`, which GitHub creates for each run and revokes when it ends. `profile.json` holds the same things my profile already shows, and in this repository it is ignored by git, so nobody's personal config ends up in a pull request. My photos aren't in the repository either; the example config only points at where they live on my machine.
