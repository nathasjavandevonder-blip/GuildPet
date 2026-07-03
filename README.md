# Guild Dragon Bot v2.0

A cooperative Discord guild dragon game.

## v2.0 focus
- Art-first embed layout
- Dragon artwork support
- Event artwork support
- World mural artwork support
- Community world progression
- Lifetime Guild Tokens
- Cleaner game-style UI
- Same single-message button gameplay

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## .env

```env
DISCORD_TOKEN=your_token_here
```

## Discord

```text
/dragon_setup
```

## Important image folders

```text
assets/dragons/egg/idle.png
assets/dragons/egg/eating.png
assets/dragons/egg/sleeping.png

assets/world/empty_cave.png
assets/world/soft_nest.png

assets/events/treasure.png
assets/events/merchant.png
assets/events/storm.png
```

Use `/dragon_needed_images` and `/dragon_art_status` in Discord to see exactly what the bot is looking for.

## Admin test commands

```text
/dragon_force_pose
/dragon_force_stats
/dragon_add_tokens
/dragon_weather
/dragon_accessory
```

No database reset is required when updating from v1.x. The bot auto-adds missing columns.
