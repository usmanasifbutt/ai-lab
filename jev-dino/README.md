# jev-dino

Exploratory script (not a real project): have [TypeSafe AI's Jev](https://typesafe.ai) play
the Chrome dino-runner game, deciding jump/duck/none every tick based on exact numeric game
state (obstacle distance, speed) rather than pixels.

`chrome://dino` itself can't be automated - Chrome blocks automation protocols (Playwright,
Puppeteer, Selenium all use this under the hood) and extensions from touching its own internal
pages. This plays [trex-runner.com](https://trex-runner.com/), a faithful copy of Chrome's own
extracted source for the same game, running as a normal webpage instead.

Runs via [OpenRouter](https://openrouter.ai/typesafe/jev-1.13) rather than a direct TypeSafe
API key.

## Setup

```bash
uv sync
uv run playwright install chromium
```

Add your OpenRouter key to `.env` (already created, just fill in the value):

```
OPENROUTER_API_KEY=sk-or-...
```

## Running

```bash
uv run python play.py
```

Runs with a visible browser window by default (`headless=False` in `play.py`) so you can watch
it play; set `headless=True` if you don't want the window. Plays until it crashes, printing
each tick's state and Jev's decision to the console.

## What to expect (and the actual conclusion of this experiment)

Obstacles in this game are never visible farther than ~570-600px away - there's no "spot it
early" option. Measured real round-trip latency to `jev-1.13` via OpenRouter in testing was
480-920ms, at or above the *worst end* of OpenRouter's published 70-500ms range, closing
200-350+ px per call at this game's speed. That leaves a total reaction window, from an
obstacle first appearing to needing to have already acted, of well under one second - and a
single slow network call can consume the entire thing.

The prompt was tuned to act on the very first sighting of an obstacle (`ACT_GAP=600`, matching
first-sight distance) rather than waiting to "confirm" and jump on a second call, which
measurably helped - it now regularly clears several obstacles per run instead of dying on the
very first one. But it still crashes, sometimes immediately, whenever a single round trip lands
on the slow end of that range. That's the honest ceiling for this approach: no further prompt
tuning fixes a physics problem - the reaction window here is sometimes literally shorter than
one network round trip to a hosted model. A same-speed local decision-maker (see git history:
this project briefly had a `heuristic` mode with zero latency, later removed) doesn't have this
problem, which is itself the finding worth taking away - some decisions in a real-time loop are
latency-bound in a way no amount of model quality or prompting changes.

## Known quirks

- `trex-runner.com` never fires the `load` event promptly (a slow/hanging ad or tracker
  resource), which made `page.goto()` unreliable with Playwright's default wait condition -
  fixed by waiting for `domcontentloaded` instead, since that's all we need for `window.Runner`
  to be ready.
- This site's `Runner.instance_.playing` flag doesn't reliably reflect that the game is
  running, so `play.py` uses `distanceRan > 0` as the "game started" signal instead.
- This site's `dino.jumping`/`dino.ducking` flags can get **permanently stuck at `True`**
  after enough jumps (found by logging them), which would block every future decision if used
  to guard against re-triggering a jump/duck mid-action. `play.py` tracks its own action
  timestamp instead (`ACTION_COOLDOWN`, ~0.5s) rather than trusting the page's internal state.
