from datetime import datetime, timezone
from database import connect

ACHIEVEMENTS = {
    "first_feed": ("🍖 First Meal", "Feed the dragon once."),
    "feed_25": ("🍖 Dragon Chef", "Feed the dragon 25 times."),
    "play_25": ("🎮 Play Champion", "Play with the dragon 25 times."),
    "train_25": ("🏋️ Trainer", "Train the dragon 25 times."),
    "clean_25": ("🛁 Clean Keeper", "Clean the dragon 25 times."),
    "bond_25": ("❤️ Dragon Friend", "Bond with the dragon 25 times."),
    "events_10": ("🎲 Event Hunter", "Claim 10 random events."),
    "streak_7": ("🔥 One Week Keeper", "Keep a 7 day streak."),
    "streak_30": ("🔥 Loyal Keeper", "Keep a 30 day streak."),
    "points_500": ("⭐ Caretaker", "Earn 500 points."),
    "points_2500": ("🌟 Dragon Keeper", "Earn 2,500 points."),
}

ACHIEVEMENT_REQUIREMENTS = {
    "first_feed": ("feeds", 1),
    "feed_25": ("feeds", 25),
    "play_25": ("plays", 25),
    "train_25": ("trains", 25),
    "clean_25": ("cleans", 25),
    "bond_25": ("bonds", 25),
    "events_10": ("events", 10),
    "streak_7": ("streak", 7),
    "streak_30": ("streak", 30),
    "points_500": ("points", 500),
    "points_2500": ("points", 2500),
}

def check_achievements(guild, user_id: int):
    con = connect()
    con.row_factory = __import__("sqlite3").Row
    cur = con.cursor()
    cur.execute("SELECT * FROM players WHERE guild_id=? AND user_id=?", (guild.id, user_id))
    p = cur.fetchone()
    if not p:
        con.close()
        return []

    to_unlock = []
    for key, (field, target) in ACHIEVEMENT_REQUIREMENTS.items():
        if p[field] >= target:
            to_unlock.append(key)

    unlocked = []
    now = datetime.now(timezone.utc).isoformat()

    for key in to_unlock:
        cur.execute(
            "INSERT OR IGNORE INTO achievements (guild_id, user_id, achievement_key, unlocked_at) VALUES (?, ?, ?, ?)",
            (guild.id, user_id, key, now),
        )
        if cur.rowcount:
            unlocked.append(key)

    con.commit()
    con.close()
    return unlocked

def get_user_achievements(guild_id: int, user_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute(
        "SELECT achievement_key FROM achievements WHERE guild_id=? AND user_id=? ORDER BY unlocked_at ASC",
        (guild_id, user_id),
    )
    rows = [r[0] for r in cur.fetchall()]
    con.close()
    return rows

def get_achievement_progress(guild_id: int, user_id: int):
    con = connect()
    con.row_factory = __import__("sqlite3").Row
    cur = con.cursor()

    cur.execute("SELECT * FROM players WHERE guild_id=? AND user_id=?", (guild_id, user_id))
    p = cur.fetchone()

    cur.execute(
        "SELECT achievement_key FROM achievements WHERE guild_id=? AND user_id=?",
        (guild_id, user_id),
    )
    unlocked = {r[0] for r in cur.fetchall()}
    con.close()

    if not p:
        return []

    rows = []
    for key, (name, desc) in ACHIEVEMENTS.items():
        field, target = ACHIEVEMENT_REQUIREMENTS[key]
        current = int(p[field] or 0)
        done = key in unlocked or current >= target
        remaining = max(target - current, 0)
        rows.append({
            "key": key,
            "name": name,
            "desc": desc,
            "current": current,
            "target": target,
            "remaining": remaining,
            "done": done,
        })

    return rows
