from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS dragon_profile_v5 (
                guild_id INTEGER PRIMARY KEY,
                dragon_name TEXT NOT NULL DEFAULT 'Guild Dragon',
                title TEXT NOT NULL DEFAULT 'Guardian in Training',
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                growth INTEGER NOT NULL DEFAULT 0,
                personality TEXT NOT NULL DEFAULT 'Curious',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS dashboard_activity_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                activity_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_dashboard_activity_guild
            ON dashboard_activity_v5 (guild_id, id DESC);
            """
        )
