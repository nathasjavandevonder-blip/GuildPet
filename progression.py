from database import connect, get_dragon
from memories import add_memory

RESEARCH = {
    "better_food": {
        "name": "Better Food",
        "cost": 1,
        "description": "Feed gives +2 hunger and +1 dragon XP.",
    },
    "play_area": {
        "name": "Play Area",
        "cost": 1,
        "description": "Play gives +2 happiness and +1 dragon XP.",
    },
    "training_ground": {
        "name": "Training Ground",
        "cost": 2,
        "description": "Train gives +2 bond and +2 dragon XP.",
    },
    "warm_nest": {
        "name": "Warm Nest",
        "cost": 2,
        "description": "Rest gives +5 energy.",
    },
    "clean_spring": {
        "name": "Clean Spring",
        "cost": 2,
        "description": "Clean gives +5 cleanliness.",
    },
    "dragon_library": {
        "name": "Dragon Library",
        "cost": 3,
        "description": "All care actions give +1 Guild XP.",
    },
}

def level_needed(level: int):
    return 250 + ((level - 1) * 150)

def add_guild_level_xp(guild_id: int, amount: int):
    if amount <= 0:
        return []

    d = get_dragon(guild_id)
    level = d["guild_level"]
    xp = d["guild_level_xp"] + amount
    research_points = d["research_points"]
    leveled = []

    while xp >= level_needed(level):
        xp -= level_needed(level)
        level += 1
        research_points += 1
        leveled.append(level)

    con = connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE dragon SET guild_level=?, guild_level_xp=?, research_points=? WHERE guild_id=?",
        (level, xp, research_points, guild_id)
    )
    con.commit()
    con.close()

    for new_level in leveled:
        add_memory(guild_id, f"The guild dragon reached Guild Level {new_level} and earned a research point.")

    return leveled

def has_research(guild_id: int, key: str):
    con = connect()
    cur = con.cursor()
    cur.execute(
        "SELECT bought FROM shop_items WHERE guild_id=? AND item_key=?",
        (guild_id, f"research_{key}")
    )
    row = cur.fetchone()
    con.close()
    return bool(row and row[0])

def buy_research(guild_id: int, key: str):
    if key not in RESEARCH:
        return False, "Unknown research."

    if has_research(guild_id, key):
        return False, "This research has already been unlocked."

    d = get_dragon(guild_id)
    item = RESEARCH[key]

    if d["research_points"] < item["cost"]:
        return False, f"The guild needs **{item['cost']} Research Points**. Current: **{d['research_points']}**."

    con = connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE dragon SET research_points=research_points-?, dragon_message=?, last_action_text=? WHERE guild_id=?",
        (
            item["cost"],
            f"The guild learned {item['name']}!",
            f"📚 Research unlocked: **{item['name']}**.",
            guild_id,
        )
    )
    cur.execute(
        "INSERT OR REPLACE INTO shop_items (guild_id, item_key, bought) VALUES (?, ?, 1)",
        (guild_id, f"research_{key}")
    )
    con.commit()
    con.close()

    add_memory(guild_id, f"The guild researched {item['name']}.")
    return True, f"✅ Research unlocked: **{item['name']}**."

def research_bonus(guild_id: int, action: str):
    bonus = {
        "hunger": 0,
        "happiness": 0,
        "energy": 0,
        "cleanliness": 0,
        "bond": 0,
        "xp": 0,
        "guild_level_xp": 0,
    }

    if action == "feed" and has_research(guild_id, "better_food"):
        bonus["hunger"] += 2
        bonus["xp"] += 1

    if action == "play" and has_research(guild_id, "play_area"):
        bonus["happiness"] += 2
        bonus["xp"] += 1

    if action == "train" and has_research(guild_id, "training_ground"):
        bonus["bond"] += 2
        bonus["xp"] += 2

    if action == "rest" and has_research(guild_id, "warm_nest"):
        bonus["energy"] += 5

    if action == "clean" and has_research(guild_id, "clean_spring"):
        bonus["cleanliness"] += 5

    if has_research(guild_id, "dragon_library"):
        bonus["guild_level_xp"] += 1

    return bonus

def prestige_guild(guild_id: int):
    d = get_dragon(guild_id)

    if d["guild_level"] < 25:
        return False, "Prestige requires Guild Level **25**."

    con = connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET prestige=prestige+1,
            guild_level=1,
            guild_level_xp=0,
            research_points=research_points+3,
            dragon_message=?,
            last_action_text=?
        WHERE guild_id=?
    """, (
        "The guild's legacy has grown stronger.",
        "🌟 The guild prestiged and gained legacy power.",
        guild_id,
    ))
    con.commit()
    con.close()

    add_memory(guild_id, "The guild performed a Dragon Prestige and began a new legacy.")
    return True, "🌟 Guild Prestige complete! Guild Level reset to 1 and the guild gained **3 Research Points**."
