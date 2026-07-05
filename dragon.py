import random
from datetime import datetime, timedelta, timezone, date

from database import connect, get_dragon
from memories import add_memory
from shop import has_item
from utils import clamp, get_stage, utc_today
from progression import research_bonus, add_guild_level_xp
from living import affection_event_text

DRAGON_MESSAGES = {
    "feed": [
        "That was delicious!",
        "More meat, please!",
        "I feel stronger already.",
        "My belly is happy now.",
        "You always know what I like.",
    ],
    "play": [
        "Again! Again!",
        "That was fun!",
        "I almost caught the ball with my wings.",
        "I like when the guild plays with me.",
        "I feel full of energy!",
    ],
    "train": [
        "My fire feels hotter today.",
        "I will protect this guild.",
        "Training makes me powerful!",
        "One day my roar will shake the sky.",
        "I am learning fast.",
    ],
    "clean": [
        "So fresh and shiny!",
        "My scales feel amazing.",
        "I smell better now.",
        "Even dragons need bath time.",
        "Look how shiny my scales are!",
    ],
    "rest": [
        "Good night, keepers...",
        "Wake me if treasure appears.",
        "Zzz... tiny dragon dreams...",
        "I will dream about flying.",
        "The lair feels cozy.",
    ],
    "bond": [
        "I trust you more now.",
        "You are one of my favorite keepers.",
        "I like when you sit with me.",
        "The guild feels like home.",
        "Stay a little longer.",
    ],
    "idle": [
        "I wonder what the guild is doing...",
        "Someone scratched behind my horns today. That felt nice.",
        "I am guarding the lair.",
        "Is it snack time yet?",
        "The cave is quiet today.",
        "I can hear wings in my dreams.",
        "One day I will fly above the whole guild.",
    ],
    "hungry": [
        "My tummy is rumbling...",
        "Did someone forget my food?",
        "I can smell snacks somewhere...",
    ],
    "sleepy": [
        "Five more minutes...",
        "I am getting sleepy.",
        "The nest looks very comfortable.",
    ],
    "messy": [
        "My scales feel dirty...",
        "The lair needs cleaning.",
        "I stepped in mud again.",
    ],
    "affectionate": [
        "I love this guild.",
        "You make this lair feel like home.",
        "I remember everyone who cared for me.",
    ],
    "night": [
        "The stars look beautiful tonight.",
        "I will guard the lair while everyone sleeps.",
        "The moon makes my scales glow.",
    ],
    "morning": [
        "Good morning, keepers!",
        "I woke up thinking about breakfast.",
        "A new day in the lair begins!",
    ],
}


def mood_from_stats(d):
    if d["hunger"] < 25:
        return "Hungry"
    if d["cleanliness"] < 25:
        return "Messy"
    if d["energy"] < 20:
        return "Sleepy"
    if d["bond"] >= 80 and d["happiness"] >= 80:
        return "Affectionate"
    if d["happiness"] >= 80:
        return "Happy"
    return "Curious"


def time_based_message():
    hour = datetime.now(timezone.utc).hour
    if 5 <= hour < 11:
        return random.choice(DRAGON_MESSAGES["morning"])
    if hour >= 22 or hour < 5:
        return random.choice(DRAGON_MESSAGES["night"])
    return None


def pick_idle_message(d):
    mood = mood_from_stats(d)
    timed = time_based_message()
    if timed and random.random() < 0.35:
        return timed
    if mood == "Hungry":
        return random.choice(DRAGON_MESSAGES["hungry"])
    if mood == "Sleepy":
        return random.choice(DRAGON_MESSAGES["sleepy"])
    if mood == "Messy":
        return random.choice(DRAGON_MESSAGES["messy"])
    if mood == "Affectionate":
        return random.choice(DRAGON_MESSAGES["affectionate"])
    return random.choice(DRAGON_MESSAGES["idle"])


def check_cooldown(guild_id: int, user_id: int, action: str, minutes: int = 30):
    con = connect()
    cur = con.cursor()
    cur.execute(
        "SELECT last_used FROM cooldowns WHERE guild_id=? AND user_id=? AND action=?",
        (guild_id, user_id, action),
    )
    row = cur.fetchone()
    now = datetime.now(timezone.utc)

    if row:
        last = datetime.fromisoformat(row[0])
        remaining = timedelta(minutes=minutes) - (now - last)
        if remaining.total_seconds() > 0:
            con.close()
            return False, int(remaining.total_seconds() // 60) + 1

    cur.execute(
        "INSERT OR REPLACE INTO cooldowns (guild_id, user_id, action, last_used) VALUES (?, ?, ?, ?)",
        (guild_id, user_id, action, now.isoformat()),
    )
    con.commit()
    con.close()
    return True, 0


def update_daily_streak(guild_id: int, user_id: int):
    today = utc_today()
    con = connect()
    con.row_factory = __import__("sqlite3").Row
    cur = con.cursor()
    cur.execute(
        "SELECT streak, best_streak, last_daily FROM players WHERE guild_id=? AND user_id=?",
        (guild_id, user_id),
    )
    p = cur.fetchone()

    if not p:
        con.close()
        return 0, False

    if p["last_daily"] == today:
        con.close()
        return p["streak"], False

    if p["last_daily"]:
        try:
            last = date.fromisoformat(p["last_daily"])
            now_date = date.fromisoformat(today)
            streak = p["streak"] + 1 if (now_date - last).days == 1 else 1
        except Exception:
            streak = 1
    else:
        streak = 1

    best = max(p["best_streak"], streak)
    cur.execute(
        "UPDATE players SET streak=?, best_streak=?, last_daily=? WHERE guild_id=? AND user_id=?",
        (streak, best, today, guild_id, user_id),
    )
    con.commit()
    con.close()
    return streak, True


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
    cur.execute(
        """
        INSERT INTO players (guild_id, user_id, tokens, points)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            tokens = tokens + excluded.tokens,
            points = points + excluded.points
        """,
        (guild_id, user_id, tokens, points),
    )
    if column:
        cur.execute(
            f"UPDATE players SET {column} = {column} + 1 WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
    con.commit()
    con.close()
    return update_daily_streak(guild_id, user_id)


def update_personality(guild_id: int):
    d = get_dragon(guild_id)
    personality = mood_from_stats(d)
    if personality in ["Hungry", "Messy", "Sleepy"]:
        personality = d["personality"] or "Curious"
    elif d["bond"] >= 80 and d["happiness"] >= 80:
        personality = "Affectionate"
    elif d["energy"] >= 70 and d["bond"] >= 50:
        personality = "Playful"
    else:
        personality = "Curious"

    mood = mood_from_stats(d)
    con = connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE dragon SET personality=?, mood=? WHERE guild_id=?",
        (personality, mood, guild_id),
    )
    con.commit()
    con.close()


def apply_action(guild_id: int, user, action: str):
    feed_bonus = 5 if has_item(guild_id, "golden_bowl") and action == "feed" else 0
    train_bonus = 3 if has_item(guild_id, "training_dummy") and action == "train" else 0
    clean_bonus = 5 if has_item(guild_id, "bubble_bath") and action == "clean" else 0
    bonus = research_bonus(guild_id, action)

    # Energy rebalance:
    # - Rest gives much more energy.
    # - Training/play drain less.
    # - Feeding/cleaning/bonding give a small energy recovery.
    effects = {
        "feed": {
            "hunger": 12 + feed_bonus,
            "energy": 3,
            "xp": 2,
            "tokens": 8,
            "guild_tokens": 4,
            "points": 8,
            "pose": "eating",
            "text": "fed the dragon 🍖",
        },
        "play": {
            "happiness": 10,
            "energy": -2,
            "xp": 2,
            "tokens": 8,
            "guild_tokens": 4,
            "points": 8,
            "pose": "playing",
            "text": "played with the dragon 🟢",
        },
        "train": {
            "bond": 5,
            "energy": -5,
            "xp": 4 + train_bonus,
            "tokens": 10,
            "guild_tokens": 5,
            "points": 10,
            "pose": "training",
            "text": "trained the dragon 🏋️",
        },
        "clean": {
            "cleanliness": 12 + clean_bonus,
            "energy": 2,
            "xp": 2,
            "tokens": 8,
            "guild_tokens": 4,
            "points": 8,
            "pose": "clean",
            "text": "cleaned the dragon 🛁",
        },
        "rest": {
            "energy": 35,
            "happiness": 2,
            "xp": 1,
            "tokens": 4,
            "guild_tokens": 2,
            "points": 4,
            "pose": "sleeping",
            "text": "let the dragon rest 😴",
        },
        "bond": {
            "bond": 8,
            "happiness": 4,
            "energy": 2,
            "xp": 2,
            "tokens": 8,
            "guild_tokens": 4,
            "points": 8,
            "pose": "bonding",
            "text": "bonded with the dragon ❤️",
        },
    }

    e = effects[action]
    d = get_dragon(guild_id)

    if d["sleeping"] and action not in ["bond", "rest"]:
        action = "bond"
        e = effects[action]

    old_stage, _ = get_stage(d["xp"])

    hunger = clamp(d["hunger"] + e.get("hunger", 0) + bonus.get("hunger", 0))
    happiness = clamp(d["happiness"] + e.get("happiness", 0) + bonus.get("happiness", 0))
    energy = clamp(d["energy"] + e.get("energy", 0) + bonus.get("energy", 0))
    cleanliness = clamp(d["cleanliness"] + e.get("cleanliness", 0) + bonus.get("cleanliness", 0))
    bond = clamp(d["bond"] + e.get("bond", 0) + bonus.get("bond", 0))
    xp = d["xp"] + e.get("xp", 0) + bonus.get("xp", 0)
    guild_tokens = d["guild_tokens"] + e.get("guild_tokens", 0)
    lifetime_guild_tokens = d["lifetime_guild_tokens"] + e.get("guild_tokens", 0)

    dragon_message = random.choice(DRAGON_MESSAGES[action])
    text = f"**{user.display_name}** {e['text']} and earned **{e['tokens']} Dragon Tokens**."

    if action == "bond" and random.random() < 0.35:
        text += "\n" + affection_event_text(user.display_name)

    new_stage, _ = get_stage(xp)
    if new_stage != old_stage:
        text += f"\n🌟 The dragon grew into **{new_stage}**!"
        dragon_message = f"I grew into a {new_stage}!"
        add_memory(guild_id, f"The dragon grew into {new_stage}. {user.display_name} triggered the milestone.")

    con = connect()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE dragon
        SET hunger=?, happiness=?, energy=?, cleanliness=?, bond=?, xp=?,
            guild_tokens=?, lifetime_guild_tokens=?, pose=?, visual_event=?,
            sleeping=0, last_action_text=?, dragon_message=?
        WHERE guild_id=?
        """,
        (
            hunger,
            happiness,
            energy,
            cleanliness,
            bond,
            xp,
            guild_tokens,
            lifetime_guild_tokens,
            e["pose"],
            "None",
            text,
            dragon_message,
            guild_id,
        ),
    )
    con.commit()
    con.close()

    streak, new_day = add_player_reward(guild_id, user.id, e["tokens"], e["points"], action)
    if new_day and streak > 1:
        add_memory(guild_id, f"{user.display_name} reached a {streak} day keeper streak.")

    add_guild_level_xp(guild_id, e.get("points", 0) + bonus.get("guild_level_xp", 0))
    update_personality(guild_id)


def decay_dragon(guild_id: int):
    d = get_dragon(guild_id)
    message = pick_idle_message(d)
    mood = mood_from_stats(d)

    weather_options = ["Clear", "Clear", "Clear", "Rain", "Stars"]
    if datetime.now(timezone.utc).month in [12, 1, 2]:
        weather_options.append("Snow")

    con = connect()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE dragon
        SET hunger=?, happiness=?, energy=?, cleanliness=?, pose=?, mood=?,
            weather=?, visual_event=?, dragon_message=?, last_decay=?
        WHERE guild_id=?
        """,
        (
            clamp(d["hunger"] - 2),
            clamp(d["happiness"] - 1),
            clamp(d["energy"] - 1),
            clamp(d["cleanliness"] - 1),
            random.choice(["waiting", "sleeping", "looking around", "stretching", "guarding the lair"]),
            mood,
            random.choice(weather_options),
            "None",
            message,
            datetime.now(timezone.utc).isoformat(),
            guild_id,
        ),
    )
    con.commit()
    con.close()
    update_personality(guild_id)
