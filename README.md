# Guild Dragon Bot v1.2

Button-based Discord guild dragon game.

## New in v1.2
- Cleaner RPG-style embed
- Dragon speech bubble
- Visual asset engine
- Dragon image support
- Lair image support folders
- Pose text removed from main UI
- Full project release

## Run

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

## Discord setup

```text
/dragon_setup
```

## Image assets

Put dragon images in:

```text
assets/dragons/egg/idle.png
assets/dragons/egg/eating.png
assets/dragons/egg/sleeping.png
assets/dragons/egg/bonding.png
assets/dragons/hatchling/idle.png
```

Supported:
- png
- jpg
- jpeg
- webp

The bot will fall back to `idle.png` if a pose image is missing.
