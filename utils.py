from datetime import datetime, timezone

def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, value))

def emoji_bar(value: int, blocks: int = 10):
    value = clamp(value)
    filled = round((value / 100) * blocks)
    fill = "🟩" if value >= 75 else "🟨" if value >= 40 else "🟥"
    return fill * filled + "⬜" * (blocks - filled) + f" {value}%"

def growth_bar(value: int, blocks: int = 10):
    value = clamp(value)
    filled = round((value / 100) * blocks)
    return "🟪" * filled + "⬜" * (blocks - filled) + f" {value}%"

def heart_bar(value: int, blocks: int = 10):
    value = clamp(value)
    filled = round((value / 100) * blocks)
    return "💜" * filled + "🤍" * (blocks - filled) + f" {value}%"

def get_stage(xp: int):
    if xp >= 100000: return "Elder Dragon", "🌌"
    if xp >= 40000: return "Ancient Dragon", "👑"
    if xp >= 15000: return "Adult Dragon", "🔥"
    if xp >= 5000: return "Young Dragon", "🐉"
    if xp >= 1000: return "Hatchling", "🐲"
    return "Egg", "🥚"

def get_stage_title(xp: int):
    stage, emoji = get_stage(xp)
    titles = {
        "Egg": "Tiny Egg",
        "Hatchling": "Curious Hatchling",
        "Young Dragon": "Young Guardian",
        "Adult Dragon": "Sky Protector",
        "Ancient Dragon": "Ancient Elder",
        "Elder Dragon": "Celestial Dragon",
    }
    return titles.get(stage, stage), emoji

def next_stage_info(xp: int):
    stages = [("Egg", 0), ("Hatchling", 1000), ("Young Dragon", 5000), ("Adult Dragon", 15000), ("Ancient Dragon", 40000), ("Elder Dragon", 100000)]
    current_xp = 0
    next_name = "Hatchling"
    next_xp = 1000
    for i, (name, needed) in enumerate(stages):
        if xp >= needed:
            current_xp = needed
            if i + 1 < len(stages):
                next_name, next_xp = stages[i + 1]
            else:
                next_name, next_xp = "MAX", needed
    if next_name == "MAX":
        return 100, current_xp, next_xp, next_name
    progress = int(((xp - current_xp) / (next_xp - current_xp)) * 100)
    return clamp(progress), current_xp, next_xp, next_name

def utc_today():
    return datetime.now(timezone.utc).date().isoformat()

def time_of_day():
    hour = datetime.now(timezone.utc).hour
    if 5 <= hour < 11: return "Morning"
    if 11 <= hour < 18: return "Day"
    if 18 <= hour < 22: return "Evening"
    return "Night"


def current_season():
    month = datetime.now(timezone.utc).month
    day = datetime.now(timezone.utc).day

    if month == 10:
        return "Halloween"
    if month == 12 and day >= 15:
        return "Christmas"
    if month in [12, 1, 2]:
        return "Winter"
    if month in [3, 4, 5]:
        return "Spring"
    if month in [6, 7, 8]:
        return "Summer"
    return "Autumn"

def is_night_utc():
    hour = datetime.now(timezone.utc).hour
    return hour >= 22 or hour < 6


def detailed_stage_title(xp: int):
    # Extra visible growth before the first hatch.
    if xp < 250:
        return "Tiny Egg", "🥚"
    if xp < 500:
        return "Large Egg", "🥚"
    if xp < 750:
        return "Cracked Egg", "🥚"
    if xp < 1000:
        return "Almost Hatching", "🥚"
    return get_stage_title(xp)
