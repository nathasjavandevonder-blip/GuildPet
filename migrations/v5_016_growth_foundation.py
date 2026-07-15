from core.database import db_session


def _add_column_if_missing(connection, table: str, column: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def upgrade() -> None:
    with db_session() as connection:
        _add_column_if_missing(
            connection,
            "dragon_lifecycle_v55",
            "egg_care_required",
            "INTEGER NOT NULL DEFAULT 5",
        )
        _add_column_if_missing(
            connection,
            "dragon_lifecycle_v55",
            "hatch_delayed_announced",
            "INTEGER NOT NULL DEFAULT 0",
        )

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS dragon_traits_v55 (
                guild_id INTEGER PRIMARY KEY,
                courage INTEGER NOT NULL DEFAULT 50,
                determination INTEGER NOT NULL DEFAULT 50,
                strength INTEGER NOT NULL DEFAULT 50,
                wisdom INTEGER NOT NULL DEFAULT 50,
                patience INTEGER NOT NULL DEFAULT 50,
                magic INTEGER NOT NULL DEFAULT 50,
                compassion INTEGER NOT NULL DEFAULT 50,
                healing INTEGER NOT NULL DEFAULT 50,
                growth INTEGER NOT NULL DEFAULT 50,
                loyalty INTEGER NOT NULL DEFAULT 50,
                balance INTEGER NOT NULL DEFAULT 50,
                protection INTEGER NOT NULL DEFAULT 50,
                curiosity INTEGER NOT NULL DEFAULT 50,
                cunning INTEGER NOT NULL DEFAULT 50,
                adaptability INTEGER NOT NULL DEFAULT 50,
                leadership INTEGER NOT NULL DEFAULT 50,
                charisma INTEGER NOT NULL DEFAULT 50,
                luck INTEGER NOT NULL DEFAULT 50,
                source_egg TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS hatchling_care_v55 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                care_date TEXT NOT NULL,
                action_key TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id, care_date)
            );

            CREATE TABLE IF NOT EXISTS dragon_diary_v55 (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                entry_type TEXT NOT NULL,
                entry_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS guild_chronicle_v55 (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                event_key TEXT NOT NULL,
                event_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_hatchling_care_guild_date
            ON hatchling_care_v55 (guild_id, care_date);

            CREATE INDEX IF NOT EXISTS idx_dragon_diary_guild
            ON dragon_diary_v55 (guild_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_guild_chronicle_guild
            ON guild_chronicle_v55 (guild_id, created_at DESC);
            """
        )
