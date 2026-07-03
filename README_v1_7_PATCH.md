# Guild Dragon Bot v1.7 Patch

## Adds
- World progression / community mural system
- Total lifetime guild tokens
- Visual unlock milestones
- `/dragon_world`
- Cleaner game-style embed layout
- Guild Tokens now has:
  - Spendable tokens
  - Lifetime tokens

## Replace these files in GitHub
- database.py
- dragon.py
- events.py
- shop.py
- embeds.py
- bot.py

Then commit + push.

## VPS

```bash
cd ~/bot/dragonbot
git pull
sudo systemctl restart dragonbot
```

No database reset needed. The bot auto-adds the new column.
