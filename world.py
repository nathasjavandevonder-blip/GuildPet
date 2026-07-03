WORLD_MILESTONES = [
    (0, "🪨 Empty Cave", "A quiet cave with room to grow."),
    (500, "🌾 Soft Nest", "The dragon now has a cozy place to rest."),
    (1500, "💰 Tiny Treasure Pile", "A small pile of coins appears near the nest."),
    (5000, "🏳️ Guild Banner", "A banner shows this dragon belongs to the guild."),
    (10000, "💎 Crystal Glow", "Crystals begin glowing inside the lair."),
    (25000, "🧸 Toy Corner", "The dragon has toys scattered around the cave."),
    (50000, "🔥 Warm Hearth", "A warm hearth lights the lair."),
    (100000, "🌊 Underground Waterfall", "A waterfall flows through the dragon's home."),
    (250000, "🗿 Dragon Statue", "A statue honors the guild's progress."),
    (500000, "🏰 Dragon Hall", "The lair has become a true dragon hall."),
    (1000000, "☁️ Floating Islands", "The dragon's world reaches the skies."),
    (5000000, "🌌 Legendary Sky Kingdom", "The guild has built a legendary dragon realm."),
]

def current_world(lifetime_tokens: int):
    current = WORLD_MILESTONES[0]
    next_item = None

    for i, milestone in enumerate(WORLD_MILESTONES):
        if lifetime_tokens >= milestone[0]:
            current = milestone
            if i + 1 < len(WORLD_MILESTONES):
                next_item = WORLD_MILESTONES[i + 1]
        else:
            break

    return current, next_item

def world_progress_bar(lifetime_tokens: int):
    current, next_item = current_world(lifetime_tokens)
    if not next_item:
        return "🟪" * 10 + " MAX"

    start = current[0]
    end = next_item[0]
    progress = int(((lifetime_tokens - start) / (end - start)) * 100)
    progress = max(0, min(100, progress))
    filled = round((progress / 100) * 10)
    return "🟦" * filled + "⬜" * (10 - filled) + f" {progress}%"

def unlocked_world_lines(lifetime_tokens: int, limit: int = 8):
    unlocked = [m for m in WORLD_MILESTONES if lifetime_tokens >= m[0]]
    latest = unlocked[-limit:]
    return [f"{icon} **{name}**" for _, icon_name, desc in []]  # not used

def unlocked_world_text(lifetime_tokens: int):
    unlocked = [m for m in WORLD_MILESTONES if lifetime_tokens >= m[0]]
    lines = []
    for required, name, desc in unlocked[-8:]:
        lines.append(f"{name} — {desc}")
    return "\n".join(lines) if lines else "No world upgrades yet."
