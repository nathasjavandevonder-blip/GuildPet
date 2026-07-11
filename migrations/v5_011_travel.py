from core.database import db_session


def upgrade():
    with db_session() as con:
        con.executescript("""

CREATE TABLE IF NOT EXISTS dragon_location_v5(

guild_id INTEGER PRIMARY KEY,

location_key TEXT NOT NULL,

travelling INTEGER NOT NULL DEFAULT 0,

destination_key TEXT,

arrival_time TEXT,

last_updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

);

CREATE TABLE IF NOT EXISTS travel_history_v5(

id INTEGER PRIMARY KEY AUTOINCREMENT,

guild_id INTEGER NOT NULL,

from_location TEXT NOT NULL,

to_location TEXT NOT NULL,

started_at TEXT NOT NULL,

arrived_at TEXT

);

""")
