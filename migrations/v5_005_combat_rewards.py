from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS player_combat_progress_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                combat_xp INTEGER NOT NULL DEFAULT 0,
                victories INTEGER NOT NULL DEFAULT 0,
                defeats INTEGER NOT NULL DEFAULT 0,
                retreats INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS combat_rewards_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                combat_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                tokens INTEGER NOT NULL DEFAULT 0,
                loot_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (combat_id)
                    REFERENCES combat_sessions(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_combat_rewards_session
            ON combat_rewards_v5 (combat_id);

            CREATE INDEX IF NOT EXISTS idx_combat_progress_guild
            ON player_combat_progress_v5 (
                guild_id,
                victories DESC,
                combat_xp DESC
            );
            """
        )
