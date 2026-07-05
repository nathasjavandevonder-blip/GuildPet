def percent(value, maximum=100):
    try:
        return max(0, min(100, int((int(value) / int(maximum)) * 100)))
    except Exception:
        return 0

def emoji_bar(value, maximum=100, size=10, good="🟩", mid="🟨", bad="🟥", empty="⬛"):
    p = percent(value, maximum)
    filled = round(size * p / 100)
    block = bad if p <= 25 else mid if p <= 55 else good
    return block * filled + empty * (size - filled)

def xp_bar(value, maximum=100, size=12):
    p = percent(value, maximum)
    filled = round(size * p / 100)
    return "🟪" * filled + "⬛" * (size - filled)

def compact_care_line(emoji, label, value):
    return f"{emoji} **{label}** {emoji_bar(value)} `{percent(value)}%`"

def hearts(value):
    p = percent(value)
    filled = round(10 * p / 100)
    return "💜" * filled + "🖤" * (10 - filled) + f" `{p}%`"

def mood_color(d):
    if d["sleeping"]:
        return 0x5865F2
    if d["energy"] <= 20:
        return 0xED4245
    if d["happiness"] >= 85:
        return 0x57F287
    if d["bond"] >= 80:
        return 0xEB459E
    return 0x9B59FF

def lair_emoji(lair):
    return {
        "Empty Cave": "🕳️",
        "Moss Nest": "🌿",
        "Crystal Nest": "💎",
        "Lava Nest": "🌋",
        "Royal Dragon Hall": "🏰",
        "Sky Fortress": "☁️",
    }.get(lair, "🏡")

def event_emoji(event):
    return {
        "None": "🌎",
        "Rainbow": "🌈",
        "Butterflies": "🦋",
        "Mushrooms": "🍄",
        "Full Moon": "🌕",
        "Meteor Shower": "☄️",
        "Heavy Rain": "🌧️",
        "Warm Breeze": "🍃",
        "Fresh Footprints": "🐾",
        "Mysterious Feather": "🪶",
        "Fruit Gift": "🍎",
    }.get(event, "🌎")

def stage_icon(stage_title):
    s = (stage_title or "").lower()
    if "egg" in s:
        return "🥚"
    if "hatchling" in s:
        return "🐣"
    if "young" in s:
        return "🐲"
    if "adult" in s:
        return "🐉"
    if "elder" in s or "ancient" in s:
        return "👑"
    return "🐉"

def dragon_status_badge(d):
    if d["sleeping"]:
        return "💤 Sleeping"
    if d["energy"] <= 20:
        return "😴 Exhausted"
    if d["hunger"] <= 25:
        return "🍖 Hungry"
    if d["cleanliness"] <= 25:
        return "🛁 Messy"
    if d["happiness"] >= 85:
        return "😊 Happy"
    if d["bond"] >= 85:
        return "💞 Bonded"
    return f"✨ {d['mood']}"

def separator():
    return "━━━━━━━━━━━━━━━━━━━━"

def mini_separator():
    return "────────────"

def rarity_from_tokens(lifetime):
    if lifetime >= 25000:
        return "🌟 Mythic"
    if lifetime >= 10000:
        return "🟪 Legendary"
    if lifetime >= 5000:
        return "🟦 Epic"
    if lifetime >= 1500:
        return "🟩 Rare"
    return "⬜ Common"

def dragon_element(color):
    c = (color or "").lower()
    if "red" in c:
        return "🔥 Fire"
    if "blue" in c:
        return "🌊 Water"
    if "green" in c:
        return "🌿 Nature"
    if "gold" in c or "yellow" in c:
        return "⚡ Storm"
    if "purple" in c:
        return "🌙 Arcane"
    if "black" in c:
        return "🖤 Shadow"
    if "white" in c:
        return "✨ Light"
    return "🐉 Dragon"
