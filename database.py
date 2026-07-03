import sqlite3
from datetime import datetime, timezone
from config import DB_FILE

DRAGON_COLUMNS = {
    "channel_id": "INTEGER",
    "message_id": "INTEGER",
    "event_channel_id": "INTEGER",
    "hunger": "INTEGER DEFAULT 60",
    "happiness": "INTEGER DEFAULT 60",
    "energy": "INTEGER DEFAULT 60",
    "cleanliness": "INTEGER DEFAULT 60",
    "bond": "INTEGER DEFAULT 0",
    "xp": "INTEGER DEFAULT 0",
    "guild_tokens": "INTEGER DEFAULT 0",
    "personality": "TEXT DEFAULT 'Curious'",
    "lair": "TEXT DEFAULT 'Empty Cave'",
    "pose": "TEXT DEFAULT 'waiting'",
    "last_action_text": "TEXT DEFAULT 'The dragon is waiting for care.'",
    "last_decay": "TEXT",
    "dragon_message": "TEXT DEFAULT 'I am waiting for someone to take care of me.'"
}

PLAYER_COLUMNS = {
    "tokens": "INTEGER DEFAULT 0",
    "points": "INTEGER DEFAULT 0",
    "feeds": "INTEGER DEFAULT 0",
    "plays": "INTEGER DEFAULT 0",
    "trains": "INTEGER DEFAULT 0",
    "cleans": "INTEGER DEFAULT 0",
    "rests": "INTEGER DEFAULT 0",
    "bonds": "INTEGER DEFAULT 0",
    "events": "INTEGER DEFAULT 0"
}

def connect():
    return sqlite3.connect(DB_FILE)

def add_missing_columns(cur, table, columns):
    cur.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}
    for name, definition in columns.items():
        if name not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

def init_db():
    con = connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dragon (
        guild_id INTEGER PRIMARY KEY
    )
    """)
    add_missing_columns(cur, "dragon", DRAGON_COLUMNS)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        guild_id INTEGER,
        user_id INTEGER,
        PRIMARY KEY (guild_id, user_id)
    )
    """)
    add_missing_columns(cur, "players", PLAYER_COLUMNS)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cooldowns (
        guild_id INTEGER,
        user_id INTEGER,
        action TEXT,
        last_used TEXT,
        PRIMARY KEY (guild_id, user_id, action)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shop_items (
        guild_id INTEGER,
        item_key TEXT,
        bought INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, item_key)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS achievements (
        guild_id INTEGER,
        user_id INTEGER,
        achievement_key TEXT,
        unlocked_at TEXT,
        PRIMARY KEY (guild_id, user_id, achievement_key)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        text TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        guild_id INTEGER PRIMARY KEY,
        event_type TEXT,
        expires_at TEXT,
        claimed_by INTEGER,
        message_id INTEGER
    )
    """)

    con.commit()
    con.close()

def ensure_dragon(guild_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO dragon (guild_id, last_decay) VALUES (?, ?)",
        (guild_id, datetime.now(timezone.utc).isoformat())
    )
    con.commit()
    con.close()

def get_dragon(guild_id: int):
    ensure_dragon(guild_id)
    con = connect()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM dragon WHERE guild_id = ?", (guild_id,))
    row = cur.fetchone()
    con.close()
    return row
