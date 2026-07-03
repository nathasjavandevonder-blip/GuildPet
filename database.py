import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from config import DB_FILE

DRAGON_COLUMNS = {
    "channel_id": "INTEGER",
    "message_id": "INTEGER",
    "event_channel_id": "INTEGER",
    "dragon_name": "TEXT DEFAULT 'Guild Dragon'",
    "dragon_color": "TEXT DEFAULT 'Purple'",
    "hunger": "INTEGER DEFAULT 60",
    "happiness": "INTEGER DEFAULT 60",
    "energy": "INTEGER DEFAULT 60",
    "cleanliness": "INTEGER DEFAULT 60",
    "bond": "INTEGER DEFAULT 0",
    "xp": "INTEGER DEFAULT 0",
    "guild_tokens": "INTEGER DEFAULT 0",
    "lifetime_guild_tokens": "INTEGER DEFAULT 0",
    "guild_level": "INTEGER DEFAULT 1",
    "guild_level_xp": "INTEGER DEFAULT 0",
    "research_points": "INTEGER DEFAULT 0",
    "prestige": "INTEGER DEFAULT 0",
    "personality": "TEXT DEFAULT 'Curious'",
    "lair": "TEXT DEFAULT 'Empty Cave'",
    "pose": "TEXT DEFAULT 'waiting'",
    "mood": "TEXT DEFAULT 'Curious'",
    "weather": "TEXT DEFAULT 'Clear'",
    "accessory": "TEXT DEFAULT 'None'",
    "visual_event": "TEXT DEFAULT 'None'",
    "world_event": "TEXT DEFAULT 'None'",
    "dragon_trait": "TEXT DEFAULT 'Unchosen'",
    "last_daily_gift": "TEXT",
    "sleep_blocked_actions": "INTEGER DEFAULT 1",
    "last_action_text": "TEXT DEFAULT 'The dragon is waiting for care.'",
    "last_decay": "TEXT",
    "last_living_update": "TEXT",
    "last_care_request": "TEXT",
    "sleeping": "INTEGER DEFAULT 0",
    "birthday": "TEXT",
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
    "events": "INTEGER DEFAULT 0",
    "streak": "INTEGER DEFAULT 0",
    "best_streak": "INTEGER DEFAULT 0",
    "last_daily": "TEXT",
    "keeper_title": "TEXT"
}

def connect():
    con = sqlite3.connect(DB_FILE, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA foreign_keys=ON")
    return con

@contextmanager
def db_session(row_factory=False):
    con = connect()
    if row_factory:
        con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except sqlite3.OperationalError as exc:
        con.rollback()
        raise exc
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def execute_with_retry(fn, retries=5, delay=0.25):
    last_error = None

    for attempt in range(retries):
        try:
            return fn()
        except sqlite3.OperationalError as exc:
            last_error = exc
            if "locked" not in str(exc).lower():
                raise
            time.sleep(delay * (attempt + 1))

    raise last_error

def add_missing_columns(cur, table, columns):
    cur.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}

    for name, definition in columns.items():
        if name not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

def init_db():
    def work():
        with db_session() as con:
            cur = con.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS dragon (guild_id INTEGER PRIMARY KEY)")
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

    execute_with_retry(work)

def ensure_dragon(guild_id: int):
    def work():
        with db_session() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO dragon (guild_id, last_decay, birthday) VALUES (?, ?, ?)",
                (
                    guild_id,
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).date().isoformat(),
                )
            )

    execute_with_retry(work)

def get_dragon(guild_id: int):
    ensure_dragon(guild_id)

    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM dragon WHERE guild_id = ?", (guild_id,))
        return cur.fetchone()

def add_memory_tx(cur, guild_id: int, text: str):
    cur.execute(
        "INSERT INTO memories (guild_id, text, created_at) VALUES (?, ?, ?)",
        (guild_id, text, datetime.now(timezone.utc).isoformat())
    )
