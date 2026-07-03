# Guild Dragon Bot v2.2 Fixed

This is a clean full release rebuilt from v2.1. It fixes the broken `bot.py` syntax issue and adds v2.2 Guild Progression safely.

## Includes

- v2.1 Living Dragon
- v2.2 Guild Progression
- Guild Level
- Guild XP
- Research Points
- Research menu
- Research button
- Prestige command
- Clean fixed `bot.py`

## Update

Upload all files to GitHub, commit, push.

On VPS:

```bash
cd ~/bot/dragonbot
git pull
python -m py_compile bot.py
sudo systemctl restart dragonbot
sudo systemctl status dragonbot --no-pager -l
```

No database reset required. Missing columns are added automatically.
