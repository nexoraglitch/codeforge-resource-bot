# CodeForge Daily Resource Bot

Posts one new resource link per day to `#python-resources`,
`#js-resources`, and `#html-css-resources` — fully automatic, no
interaction needed once it's running.

## How it works
- `resources.json` holds a curated list of links per language (feel free to edit/add your own)
- Each day at a set time, the bot posts the next resource in a shuffled, non-repeating order
- Once it cycles through the full list, it reshuffles and starts a new cycle — runs forever
- `state.json` (created automatically) remembers its position, so a restart never causes a skipped day or a repeat

## 1. Install dependencies
```bash
pip install -U discord.py
```

## 2. Reuse your existing bot (or make a new one)
This bot only needs **Send Messages** permission in the 3 resource
channels — it never reads messages, so it doesn't need Message Content
or Members intents. You can reuse the same bot application from the
server setup script if you want, just make sure it's invited with
Send Messages permission.

## 3. Get the 3 channel IDs
Enable Developer Mode (User Settings → Advanced), then right-click
each channel → **Copy Channel ID**:
- `#python-resources`
- `#js-resources` (or whatever you named the JS one)
- `#html-css-resources`

## 4. Set environment variables
```bash
export DISCORD_BOT_TOKEN="your-token-here"
export PYTHON_RESOURCES_CHANNEL_ID="..."
export JS_RESOURCES_CHANNEL_ID="..."
export HTML_CSS_RESOURCES_CHANNEL_ID="..."
```

## 5. (Optional) Change the posting time
Open `resource_bot.py` and edit this line near the top:
```python
POST_TIME_UTC = datetime.time(hour=14, minute=0, tzinfo=datetime.timezone.utc)
```
14:00 UTC ≈ 9am US Eastern / 6am US Pacific / 7:30pm India. Adjust to
whatever time works for your community.

## 6. Run it
```bash
python resource_bot.py
```

---

## 🚂 Deploying to Railway (step by step)

### 1. Push this folder to a GitHub repo
Railway deploys from GitHub. Create a new repo (can be private) and push
just the `resource-bot` folder's contents to it — `resource_bot.py`,
`resources.json`, `requirements.txt`, `Procfile`.

### 2. Create the Railway project
1. Go to https://railway.app → **New Project → Deploy from GitHub repo**
2. Select your repo
3. Railway auto-detects Python via `requirements.txt` and will use the
   `Procfile` to know how to start it (`worker: python resource_bot.py`)

### 3. Set it to run as a Worker, not a Web Service
In the service settings, make sure Railway is running the `worker`
process from your Procfile (not trying to expose a web port — this bot
doesn't serve HTTP, it just runs continuously in the background).

### 4. Add environment variables
In your Railway service → **Variables** tab, add:
```
DISCORD_BOT_TOKEN=your-token-here
PYTHON_RESOURCES_CHANNEL_ID=...
JS_RESOURCES_CHANNEL_ID=...
HTML_CSS_RESOURCES_CHANNEL_ID=...
DATA_DIR=/data
```
`DATA_DIR=/data` tells the bot where to read/write `state.json` — this
matters because of the next step.

### 5. Add a Volume so state.json survives redeploys
Railway's default filesystem resets every time you redeploy. Without a
Volume, a redeploy could reset the bot's rotation position and cause a
repeated resource. To prevent that:
1. In your service → **Settings → Volumes → New Volume**
2. Set the **mount path** to `/data`
3. Redeploy

Now `state.json` lives on persistent storage instead of the
ephemeral container filesystem. (Note: volumes are only mounted while
the actual start command is running, not during any pre-deploy/build
step — this bot only touches the volume from inside `resource_bot.py`
itself, so this is already handled correctly.)

### 6. Deploy and verify
Railway deploys automatically on push. Check the **Deployments → View
Logs** tab — on startup you should see:
```
Logged in as YourBotName#1234
Daily resource posts scheduled for 14:00:00+00:00 UTC.
```
The bot will now post to all 3 channels automatically every day,
indefinitely, with no further interaction needed.

> 💡 **Billing note:** Railway charges usage-based pricing by CPU and memory, with no spending cap by default unless you set one manually in the dashboard. This bot is extremely lightweight (idle almost all day, one burst of activity to send 3 messages), so cost should be minimal — but it's worth setting a usage limit/alert in Railway's dashboard just in case.

### Updating resources later
Since `resources.json` is deployed with your code (not on the Volume),
add new links by editing the file locally and pushing to GitHub —
Railway auto-redeploys, and `state.json` on the Volume keeps your
rotation position intact across that redeploy.

---

## Alternative hosting options
If you'd rather not use Railway:

| Option | Notes |
|---|---|
| **A cheap VPS** (e.g. a $4–6/mo droplet/instance) | Run with `pm2` or `systemd` so it auto-restarts on crash/reboot. |
| **Your own always-on machine** (Raspberry Pi, home server) | Free if you already have one. Use a process manager so it survives disconnects. |

## Adding/editing resources
Just edit `resources.json` — add new entries to any language's list at
any time, even while the bot is running (it re-reads the file every
time it posts, so no restart needed). Format:
```json
{"title": "Resource Name", "url": "https://...", "emoji": "📘"}
```

## Adding a 4th language later
If you add a new language category (via `add_language.py`), add a
matching key to `resources.json`, a new entry in the `CHANNEL_IDS` dict
and `HEADER` dict near the top of `resource_bot.py`, and set the
matching environment variable for its channel ID.
