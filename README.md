# Guild Dragon Bot v2.3 — Living Events

## New in v2.3

- Deeper sleeping behavior
- Mood-based living quotes
- Dragon traits
- World events
- Daily guild gift
- Affection events after bonding
- More detailed egg growth: Tiny Egg, Large Egg, Cracked Egg, Almost Hatching
- `/dragon_trait`

## Existing systems included

- v2.1 Living Dragon
- v2.2 Guild Progression
- Research
- Prestige
- World progression
- Art engine

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

No database reset required.
