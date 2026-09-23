"""Have Jev play the Chrome dino-runner game.

chrome://dino itself can't be automated (Chrome blocks automation protocols and
extensions from touching its own internal pages). This uses trex-runner.com, a
faithful copy of Chrome's own extracted source for the same game, running as a
normal webpage - so we can read its exact numeric state (obstacle distance,
speed, etc.) instead of resorting to screenshots + a vision model.
"""

import os
import time

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from typesafe_sdk import Choice, TypeSafeClient

load_dotenv()

GAME_URL = "https://trex-runner.com/"
# Obstacles in this game never appear farther than ~550-600px away in the
# first place, so there's no real "trigger early" buffer to give - this just
# needs to cover first-sight distance. Kept above ACT_GAP for headroom.
TRIGGER_GAP = 900
# Measured actual round trips at 480-920ms (worse than OpenRouter's published
# 70-500ms) closing ~190-350px at this game's speed. Since obstacles are only
# ever first visible around ~550-600px, there is no room for a "still far,
# none" reply followed by a later "jump" - by the time that first reply comes
# back the obstacle is already dangerously close. So ACT_GAP is set at/above
# first-sight distance: jump on the very first call for an obstacle, don't
# wait to reconfirm.
ACT_GAP = 600
POLL_INTERVAL = 0.03
# Minimum real time to wait after commanding a jump/duck before allowing
# another one - roughly a jump's arc duration. Self-tracked rather than
# trusting the page's own jumping/ducking flag, which can get stuck at True.
ACTION_COOLDOWN = 0.5

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api",
            model="jev-1.13",
        )
    return _client


# Runner.instance_ is the same global the real chrome://dino exposes internally.
STATE_JS = """
() => {
    const r = window.Runner && window.Runner.instance_;
    if (!r) return null;
    const obstacles = (r.horizon && r.horizon.obstacles) || [];
    return {
        crashed: r.crashed,
        playing: r.playing,
        speed: Math.round(r.currentSpeed * 10) / 10,
        distance: Math.round(r.distanceRan),
        dino: { ducking: r.tRex.ducking, jumping: r.tRex.jumping },
        obstacles: obstacles.slice(0, 2).map(o => ({
            gap: Math.round(o.xPos),
            width: Math.round(o.width),
            y: Math.round(o.yPos),
            type: o.typeConfig ? o.typeConfig.type : null,
        })),
    };
}
"""

ACTION_INSTRUCTIONS = (
    "You are playing the Chrome dino runner game. The dino stands at a fixed "
    "x position near the left edge. Each obstacle's 'gap' is its horizontal "
    "pixel distance from the dino - smaller gap means it's closer. There is "
    "severe decision + input lag (a network round trip per decision) that can "
    "close 200-350 pixels or more, and obstacles are never visible farther "
    f"than about 600 pixels away to begin with. So as soon as ANY obstacle "
    f"is visible at all, if its gap is {ACT_GAP} pixels or less you MUST "
    "jump or duck immediately - do not answer 'none' to 'wait and see', "
    "there will likely not be a second chance to react before it's too late. "
    "Ground obstacles (type containing CACTUS) must be jumped. Flying "
    "obstacles (PTERODACTYL) have a 'y' position - duck under a low one, "
    "jump a high one only if it's too low to run under. Only answer 'none' "
    f"if the nearest obstacle's gap is still above {ACT_GAP}, or there are "
    "no obstacles."
)


def decide_action(state: dict) -> str:
    response = _get_client().system_one(
        state=state,
        questions={
            "action": Choice(
                instructions=ACTION_INSTRUCTIONS,
                criteria={
                    "jump": "Jump now to clear the next obstacle",
                    "duck": "Duck now to avoid the next obstacle",
                    "none": "No action needed right now",
                },
            ),
        },
    )
    return response.answers["action"].choice


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        # This site never fires the `load` event promptly (a slow/hanging ad or
        # tracker resource) - domcontentloaded is enough since we only need
        # window.Runner, not every third-party resource on the page.
        page.goto(GAME_URL, wait_until="domcontentloaded")
        page.wait_for_function("() => window.Runner && window.Runner.instance_")
        page.keyboard.press("Space")  # start the game
        # This build doesn't reliably set Runner.instance_.playing to true even
        # while running, so use distanceRan actually advancing as the "started" signal.
        page.wait_for_function(
            "() => window.Runner.instance_.distanceRan > 0", timeout=5000
        )

        ticks = 0
        last_action_time = 0.0
        while True:
            state = page.evaluate(STATE_JS)
            if state is None:
                print("Runner not found on page.")
                break
            if state["crashed"]:
                print(f"Crashed after {ticks} ticks - distance {state['distance']}")
                break

            nearest_gap = min((o["gap"] for o in state["obstacles"]), default=None)
            if nearest_gap is None or nearest_gap > TRIGGER_GAP:
                # Nothing to react to yet - poll locally instead of spending a
                # Jev round trip confirming "none" every tick.
                time.sleep(POLL_INTERVAL)
                continue

            now = time.monotonic()
            if now - last_action_time < ACTION_COOLDOWN:
                # Still resolving the last jump/duck - don't re-trigger it.
                time.sleep(POLL_INTERVAL)
                continue

            action = decide_action(state)
            if action == "jump":
                page.keyboard.press("ArrowUp")
                last_action_time = now
            elif action == "duck":
                page.keyboard.down("ArrowDown")
                time.sleep(0.15)
                page.keyboard.up("ArrowDown")
                last_action_time = now

            ticks += 1
            print(
                f"tick={ticks} speed={state['speed']} dist={state['distance']} "
                f"dino={state['dino']} obstacles={state['obstacles']} -> {action}"
            )

        browser.close()


if __name__ == "__main__":
    main()
