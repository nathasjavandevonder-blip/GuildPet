def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, value))

def emoji_bar(value: int, blocks: int = 10):
    value = clamp(value)
    filled = round((value / 100) * blocks)

    if value >= 75:
        fill = "🟩"
    elif value >= 40:
        fill = "🟨"
    else:
        fill = "🟥"

    return fill * filled + "⬜" * (blocks - filled) + f" {value}%"

def growth_bar(value: int, blocks: int = 10):
    value = clamp(value)
    filled = round((value / 100) * blocks)
    return "🟪" * filled + "⬜" * (blocks - filled) + f" {value}%"

def get_stage(xp: int):
    if xp >= 100000:
        return "Elder Dragon", "🌌"
    if xp >= 40000:
        return "Ancient Dragon", "👑"
    if xp >= 15000:
        return "Adult Dragon", "🔥"
    if xp >= 5000:
        return "Young Dragon", "🐉"
    if xp >= 1000:
        return "Hatchling", "🐲"
    return "Egg", "🥚"

def next_stage_info(xp: int):
    stages = [
        ("Egg", 0),
        ("Hatchling", 1000),
        ("Young Dragon", 5000),
        ("Adult Dragon", 15000),
        ("Ancient Dragon", 40000),
        ("Elder Dragon", 100000),
    ]

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
