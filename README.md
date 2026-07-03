# Guild Dragon Bot v3.0 Foundation

This is a cleaned, more stable project structure.

## What changed

- `bot.py` is now a clean launcher with startup tasks.
- Slash commands are split into cogs:
  - `cogs/setup.py`
  - `cogs/admin.py`
  - `cogs/progression.py`
  - `cogs/profile.py`
- Startup now prints:
  - loaded extensions
  - `Synced X commands`
  - bot version
- `.gitignore` now blocks:
  - `.env`
  - `guild_dragon.db`
  - `__pycache__`
  - `.pyc` files

## Features preserved

- Living dragon
- Dragon buttons
- Shop
- Research
- Guild progression
- World progression
- Daily gifts
- Traits
- Profiles
- Leaderboard
- Memories
- Random events
- Art engine

## Update

Upload all files to GitHub, commit, push.

On VPS:

```bash
cd ~/bot/dragonbot
git pull
python -m py_compile bot.py
sudo systemctl restart dragonbot
journalctl -u dragonbot -n 60 --no-pager
```

You should see:

```text
Loaded extension: cogs.setup
Loaded extension: cogs.admin
Loaded extension: cogs.progression
Loaded extension: cogs.profile
Synced X commands
Logged in as Sky Dragon#1048
Guild Dragon Bot v3.0 Foundation
```

No database reset required.
