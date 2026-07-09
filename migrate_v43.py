from database import init_db, db_session
from rpg import ensure_rpg_tables

init_db()
ensure_rpg_tables()
with db_session() as con:
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS lair_upgrades (guild_id INTEGER, upgrade_key TEXT, level INTEGER DEFAULT 0, updated_at TEXT, PRIMARY KEY (guild_id, upgrade_key))")
    cur.execute("CREATE TABLE IF NOT EXISTS adventure_log (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, area_key TEXT, result TEXT, reward_text TEXT, created_at TEXT)")
print("GuildPet v4.3 migration complete: combat, lair upgrades, quest claims and adventure log ready.")
