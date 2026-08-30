"""
CodeForge Daily Resource Bot
-----------------------------
Runs continuously and posts one new resource link per day to each of the
three resource channels (#python-resources, #js-resources, #html-css-resources)
with zero manual interaction.

HOW IT AVOIDS REPEATS:
Each language has a curated list in resources.json. The bot shuffles each
list once, tracks its position in state.json, and works through the list
in order without repeating. Once it reaches the end, it reshuffles and
starts a new cycle automatically — so it can run indefinitely.

HOW IT SURVIVES RESTARTS:
Position is saved to state.json after every post, so if the bot process
restarts (crash, redeploy, reboot) it picks up exactly where it left off
instead of skipping a day or repeating a resource.

SETUP:
1. pip install -U discord.py
2. Create a bot (or reuse your setup bot) at
   https://discord.com/developers/applications
   - Needs the "Send Messages" permission in the 3 resource channels
   - Does NOT need Message Content or Members intents — this bot only sends,
     never reads, messages, so it stays minimal-permission by design.
3. Get the 3 channel IDs (enable Developer Mode in Discord, then
   right-click each channel -> Copy Channel ID):
     - #python-resources
     - #js-resources / #javascript-resources (matches your channel name)
     - #html-css-resources
4. Set environment variables:
     export DISCORD_BOT_TOKEN="your-token-here"
     export PYTHON_RESOURCES_CHANNEL_ID="..."
     export JS_RESOURCES_CHANNEL_ID="..."
     export HTML_CSS_RESOURCES_CHANNEL_ID="..."
5. (Optional) Change POST_TIME_UTC below to control what time it posts daily.
6. Run: python resource_bot.py

This process needs to stay running 24/7 to post daily — see README.md
for free/cheap always-on hosting options (a bot script like this is NOT
something you can run only when your own computer is on).
"""

import os
import json
import random
import datetime
import discord
from discord.ext import tasks

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

CHANNEL_IDS = {
    "python": os.environ.get("PYTHON_RESOURCES_CHANNEL_ID"),
    "javascript": os.environ.get("JS_RESOURCES_CHANNEL_ID"),
    "html_css": os.environ.get("HTML_CSS_RESOURCES_CHANNEL_ID"),
}

missing = [k for k, v in CHANNEL_IDS.items() if not v]
if not TOKEN or missing:
    raise SystemExit(
        "Missing required environment variables. Need DISCORD_BOT_TOKEN plus "
        "a channel ID for each of: " + ", ".join(CHANNEL_IDS.keys()) + ". "
        "See the setup instructions at the top of this file."
    )

CHANNEL_IDS = {k: int(v) for k, v in CHANNEL_IDS.items()}

# What time (UTC, 24hr) the bot posts each day. 14:00 UTC ≈ 9am EST / 6am PST.
POST_TIME_UTC = datetime.time(hour=14, minute=0, tzinfo=datetime.timezone.utc)

# Directory for data files. On Railway, set DATA_DIR to your mounted
# Volume path (e.g. "/data") so state.json survives redeploys. Locally,
# it defaults to the script's own folder.
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(__file__))

RESOURCES_FILE = os.path.join(os.path.dirname(__file__), "resources.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")

HEADER = {
    "python": "🐍 **Daily Python Resource**",
    "javascript": "⚡ **Daily JavaScript Resource**",
    "html_css": "🌐 **Daily HTML/CSS Resource**",
}

# ---------------------------------------------------------------------
# STATE MANAGEMENT (persisted to disk so restarts don't lose position)
# ---------------------------------------------------------------------


def load_resources():
    with open(RESOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_next_resource(lang: str, resources: dict, state: dict):
    """
    Returns the next resource for a language, advancing and persisting
    the position. Reshuffles and starts a new cycle when the list is
    exhausted, so the bot can run forever without manual restocking.
    """
    pool = resources[lang]
    lang_state = state.setdefault(lang, {"order": [], "index": 0})

    # Build a fresh shuffled order if we don't have one yet, or we've
    # reached the end of the current cycle.
    if not lang_state["order"] or lang_state["index"] >= len(lang_state["order"]):
        order = list(range(len(pool)))
        random.shuffle(order)
        lang_state["order"] = order
        lang_state["index"] = 0

    idx = lang_state["order"][lang_state["index"]]
    lang_state["index"] += 1
    return pool[idx]


# ---------------------------------------------------------------------
# BOT
# ---------------------------------------------------------------------

# Minimal intents: this bot only sends messages, never reads them.
intents = discord.Intents.default()
client = discord.Client(intents=intents)


@tasks.loop(time=POST_TIME_UTC)
async def post_daily_resources():
    resources = load_resources()
    state = load_state()

    for lang, channel_id in CHANNEL_IDS.items():
        channel = client.get_channel(channel_id)
        if channel is None:
            print(f"WARNING: could not find channel for '{lang}' (ID {channel_id}). Skipping.")
            continue

        resource = get_next_resource(lang, resources, state)
        message = f"{HEADER[lang]}\n{resource['emoji']} **{resource['title']}**\n{resource['url']}"

        try:
            await channel.send(message)
            print(f"Posted {lang} resource: {resource['title']}")
        except discord.Forbidden:
            print(f"ERROR: missing permission to send in channel for '{lang}'.")

    save_state(state)


@post_daily_resources.before_loop
async def before_post_daily_resources():
    await client.wait_until_ready()


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    print(f"Daily resource posts scheduled for {POST_TIME_UTC} UTC.")
    if not post_daily_resources.is_running():
        post_daily_resources.start()


if __name__ == "__main__":
    client.run(TOKEN)
