# Guild Dragon Bot v2.1 — Living Dragon

A cooperative Discord guild dragon game.

## New in v2.1

- Dragon moves by itself every 15 minutes
- Sleep / wake cycle
- Seasonal dialogue
- Mood-based living behavior
- Care requests when hunger, cleanliness, happiness or energy gets low
- Living status command
- Main embed shows season and sleeping state
- Same single-message button gameplay

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Discord

```text
/dragon_setup
```

## New command

```text
/dragon_living_status
```

## Existing useful commands

```text
/dragon_world
/dragon_profile
/dragon_art_status
/dragon_needed_images
/dragon_force_pose
/dragon_add_tokens
```

No database reset is required when updating from v2.0. The bot auto-adds missing columns.
