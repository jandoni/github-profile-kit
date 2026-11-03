<!--
  Profile README template. `python scripts/build.py --readme README.md` fills in
  the {{...}} values from profile.json and drops this comment. You can also copy
  the file by hand and replace the values yourself.
  - The line with {{button.*}} repeats once per button.
  - The <p> block with {{card.*}} repeats once per pair of cards.
  - Every image sits inside a link: an image without one opens the raw file when clicked.
  - The terminal comes from the output branch that the daily workflow publishes.
    If GitHub keeps showing an old copy after you change its layout, bump ?v=1.
-->
<a href="{{header.link}}"><img src="assets/{{header.file}}.svg" width="100%" alt="{{header.alt}}"></a>

<p align="center">
  <a href="{{button.url}}"><img src="assets/buttons/{{button.file}}.svg" height="38" alt="{{button.alt}}"></a>
</p>

<a href="{{terminal.link}}"><img src="https://raw.githubusercontent.com/{{username}}/{{username}}/output/terminal.svg?v=1" width="100%" alt="{{terminal.alt}}"></a>

### {{cards.heading}}

<p align="center">
<a href="{{card.url}}"><img src="assets/cards/{{card.file}}.svg" width="48%" alt="{{card.alt}}"></a>
</p>
