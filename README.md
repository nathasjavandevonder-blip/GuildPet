# Guild Dragon Bot v3.2 — Dragon Adventures

## New

- Dragon Adventures system
- `/dragon_adventures`
- `/dragon_adventure_status`
- Adventure button on the main dragon message
- Active adventure tracking
- Claim adventure rewards after the dragon returns
- Rewards:
  - Dragon XP
  - Guild Tokens
  - Guild XP
  - Memories
- Failed adventure outcomes
- Unlocks harder adventure areas based on dragon XP

## Adventure areas

- 🌲 Ancient Forest
- 🌊 Crystal Lake
- 🏛️ Ancient Ruins
- ⛰️ Storm Mountains
- 🌋 Fire Volcano
- ☁️ Sky Islands

## Update

Upload all files to GitHub, commit, push.

On VPS:

```bash
cd ~/bot/dragonbot
git pull
python -m py_compile bot.py
sudo systemctl restart dragonbot
journalctl -u dragonbot -n 80 --no-pager
```

Then test:

```text
/dragon_adventures
/dragon_adventure_status
```

No database reset required.


## GuildPet v4 Stable RPG Update

Adds Adventure routes, Inventory, Quests, Lair/RPG stats, loot rarity, monsters, boss chance, and keeps XP x55 + energy rebalance.

Install:
```bash
cd /root/bot/dragonbot
unzip -o GuildPet_v4_stable_full_update.zip
./venv/bin/python migrate_v4.py
./venv/bin/python -m py_compile bot.py config.py database.py dragon.py utils.py adventures.py rpg.py embeds.py views/dragon_view.py views/adventure_view.py cogs/adventures.py
sudo systemctl restart dragonbot
journalctl -u dragonbot -n 80 --no-pager
```
