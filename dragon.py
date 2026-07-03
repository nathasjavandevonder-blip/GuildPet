import random
from datetime import datetime, timedelta, timezone
from database import connect, get_dragon
from memories import add_memory
from shop import has_item
from utils import clamp, get_stage

DRAGON_MESSAGES = {
    "feed": [
        "That was delicious!",
        "More meat, please!",
        "I feel stronger already.",
    ],
    "play": [
        "Again! Again!",
        "That was fun!",
        "I almost caught the ball with my wings.",
    ],
    "train": [
        "My fire feels hotter today.",
        "I will protect this guild.",
        "Training makes me powerful!",
    ],
    "clean": [
        "So fresh and shiny!",
        "My scales feel amazing.",
        "I smell better now.",
    ],
    "rest": [
        "Good night, keepers...",
        "Wake me if treasure appears.",
        "Zzz... tiny dragon dreams...",
    ],
    "bond": [
        "I trust you more now.",
        "You are one of my favorite keepers.",
        "I like when you sit with me.",
    ],
    "idle": [
        "I wonder what the guild is doing...",
        "Someone scratched behind my horns today. That felt nice.",
        "I am guarding the lair.",
        "Is it snack time yet?",
    ],
}

def check_cooldown(guild_id: int, user_id: int, action: str, minutes: int = 30):
    con = connect()
    cur = con.cursor()
    cur.execute("""
        SELECT last_used FROM cooldowns
        WHERE guild_id = ? AND user_id = ? AND action = ?
    """, (guild_id, user_id, action))
    row = cur.fetchone()

    now = datetime.now(timezone.utc)

    if row:
        last = datetime.fromisoformat(row[0])
        remaining = timedelta(minutes=minutes) - (now - last)
        if remaining.total_seconds() > 0:
            con.close()
            return False, int(remaining.total_seconds() // 60) + 1

    cur.execute("""
        INSERT OR REPLACE INTO cooldowns (guild_id, user_id, action, last_used)
        VALUES (?, ?, ?, ?)
    """, (guild_id, user_id, action, now.isoformat()))

    con.commit()
    con.close()
    return True, 0

def add_player_reward(guild_id: int, user_id: int, tokens: int, points: int, action: str):
    column = {
        "feed": "feeds",
        "play": "plays",
        "train": "trains",
        "clean": "cleans",
        "rest": "rests",
        "bond": "bonds",
        "event": "events",
    }.get(action)

    con = connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO players (guild_id, user_id, tokens, points)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET
            tokens = tokens + excluded.tokens,
            points = points + excluded.points
    """, (guild_id, user_id, tokens, points))

    if column:
        cur.execute(f"UPDATE players SET {column} = {column} + 1 WHERE guild_id=? AND user_id=?", (guild_id, user_id))

    con.commit()
    con.close()

def update_personality(guild_id: int):
    d = get_dragon(guild_id)

    if d["bond"] >= 80 and d["happiness"] >= 80:
        personality = "Affectionate"
    elif d["energy"] >= 80 and d["bond"] >= 50:
        personality = "Playful"
    elif d["hunger"] < 25:
        personality = "Grumpy"
    elif d["cleanliness"] < 25:
        personality = "Messy"
    elif d["energy"] < 25:
        personality = "Sleepy"
    else:
        personality = "Curious"

    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE dragon SET personality=? WHERE guild_id=?", (personality, guild_id))
    con.commit()
    con.close()

def apply_action(guild_id: int, user, action: str):
    feed_bonus = 5 if has_item(guild_id, "golden_bowl") and action == "feed" else 0
    train_bonus = 3 if has_item(guild_id, "training_dummy") and action == "train" else 0
    clean_bonus = 5 if has_item(guild_id, "bubble_bath") and action == "clean" else 0

    effects = {
        "feed":  {"hunger": 10 + feed_bonus, "xp": 2, "tokens": 8, "guild_tokens": 4, "points": 8, "pose": "eating", "text": "fed the dragon 🍖"},
        "play":  {"happiness": 8, "energy": -5, "xp": 2, "tokens": 8, "guild_tokens": 4, "points": 8, "pose": "playing", "text": "played with the dragon 🎾"},
        "train": {"bond": 5, "energy": -10, "xp": 4 + train_bonus, "tokens": 10, "guild_tokens": 5, "points": 10, "pose": "training", "text": "trained the dragon 🏋️"},
        "clean": {"cleanliness": 10 + clean_bonus, "xp": 2, "tokens": 8, "guild_tokens": 4, "points": 8, "pose": "clean", "text": "cleaned the dragon 🛁"},
        "rest":  {"energy": 15, "xp": 1, "tokens": 4, "guild_tokens": 2, "points": 4, "pose": "sleeping", "text": "let the dragon rest 😴"},
        "bond":  {"bond": 8, "happiness": 3, "xp": 2, "tokens": 8, "guild_tokens": 4, "points": 8, "pose": "bonding", "text": "bonded with the dragon ❤️"},
    }

    e = effects[action]
    d = get_dragon(guild_id)
    old_stage, _ = get_stage(d["xp"])

    hunger = clamp(d["hunger"] + e.get("hunger", 0))
    happiness = clamp(d["happiness"] + e.get("happiness", 0))
    energy = clamp(d["energy"] + e.get("energy", 0))
    cleanliness = clamp(d["cleanliness"] + e.get("cleanliness", 0))
    bond = clamp(d["bond"] + e.get("bond", 0))
    xp = d["xp"] + e.get("xp", 0)
    guild_tokens = d["guild_tokens"] + e.get("guild_tokens", 0)

    dragon_message = random.choice(DRAGON_MESSAGES[action])
    text = f"**{user.display_name}** {e['text']} and earned **{e['tokens']} Dragon Tokens**."

    new_stage, _ = get_stage(xp)
    if new_stage != old_stage:
        text += f"\n🎉 The dragon grew into **{new_stage}**!"
        dragon_message = f"I grew into a {new_stage}!"
        add_memory(guild_id, f"The dragon grew into {new_stage}. {user.display_name} triggered the milestone.")

    con = connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET hunger=?, happiness=?, energy=?, cleanliness=?, bond=?, xp=?, guild_tokens=?, pose=?, last_action_text=?, dragon_message=?
        WHERE guild_id=?
    """, (hunger, happiness, energy, cleanliness, bond, xp, guild_tokens, e["pose"], text, dragon_message, guild_id))

    con.commit()
    con.close()

    add_player_reward(guild_id, user.id, e["tokens"], e["points"], action)
    update_personality(guild_id)

def decay_dragon(guild_id: int):
    d = get_dragon(guild_id)

    con = connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET hunger=?,
            happiness=?,
            energy=?,
            cleanliness=?,
            pose=?,
            dragon_message=?,
            last_decay=?
        WHERE guild_id=?
    """, (
        clamp(d["hunger"] - 3),
        clamp(d["happiness"] - 2),
        clamp(d["energy"] - 2),
        clamp(d["cleanliness"] - 2),
        random.choice(["waiting", "sleeping", "looking around", "stretching", "guarding the lair"]),
        random.choice(DRAGON_MESSAGES["idle"]),
        datetime.now(timezone.utc).isoformat(),
        guild_id,
    ))
    con.commit()
    con.close()
    update_personality(guild_id)
