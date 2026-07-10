from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS guild_world_state_v5 (
                guild_id INTEGER PRIMARY KEY,
                location_key TEXT NOT NULL DEFAULT 'guild_hall',
                weather_key TEXT NOT NULL DEFAULT 'clear',
                time_period TEXT NOT NULL DEFAULT 'morning',
                season_key TEXT NOT NULL DEFAULT 'summer',
                weather_changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                world_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS guild_world_events_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                event_key TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location_key TEXT,
                weather_key TEXT,
                importance INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS dragon_location_history_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                from_location TEXT,
                to_location TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_world_events_guild
            ON guild_world_events_v5 (guild_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_location_history_guild
            ON dragon_location_history_v5 (guild_id, created_at DESC);
            """
        )
