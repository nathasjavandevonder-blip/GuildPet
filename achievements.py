from datetime import datetime, timezone
from database import connect

ACHIEVEMENTS = {
    "first_feed": ("🍖 First Meal", "Feed the dragon once."),
    "feed_25": ("🍗 Dragon Chef", "Feed the dragon 25 times."),
    "play_25": ("🎾 Play Champion", "Play with the dragon 25 times."),
    "train_25": ("🔥 Trainer", "Train the dragon 25 times."),
    "clean_25": ("🛁 Clean Keeper", "Clean the dragon 25 times."),
    "bond_25": ("❤️ Dragon Friend", "Bond with the dragon 25 times."),
    "points_500": ("🏅 Caretaker", "Earn 500 points."),
    "points_2500": ("🏆 Dragon Keeper", "Earn 2,500 points."),
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
    if p["feeds"] >= 1: to_unlock.append("first_feed")
    if p["feeds"] >= 25: to_unlock.append("feed_25")
    if p["plays"] >= 25: to_unlock.append("play_25")
    if p["trains"] >= 25: to_unlock.append("train_25")
    if p["cleans"] >= 25: to_unlock.append("clean_25")
    if p["bonds"] >= 25: to_unlock.append("bond_25")
    if p["points"] >= 500: to_unlock.append("points_500")
    if p["points"] >= 2500: to_unlock.append("points_2500")

    unlocked = []
    now = datetime.now(timezone.utc).isoformat()
    for key in to_unlock:
        cur.execute("""
            INSERT OR IGNORE INTO achievements (guild_id, user_id, achievement_key, unlocked_at)
            VALUES (?, ?, ?, ?)
        """, (guild.id, user_id, key, now))
        if cur.rowcount:
            unlocked.append(key)

    con.commit()
    con.close()
    return unlocked
