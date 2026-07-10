from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS achievement_progress_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                achievement_key TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                unlocked_at TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id, achievement_key)
            );

            CREATE TABLE IF NOT EXISTS achievement_showcase_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                achievement_key TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS combat_participants_v5 (
                combat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                contribution INTEGER NOT NULL DEFAULT 0,
                last_action TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (combat_id, user_id),
                FOREIGN KEY (combat_id)
                    REFERENCES combat_sessions(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS combat_actions_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                combat_id INTEGER NOT NULL,
                user_id INTEGER,
                action_key TEXT NOT NULL,
                damage INTEGER NOT NULL DEFAULT 0,
                healing INTEGER NOT NULL DEFAULT 0,
                description TEXT NOT NULL,
                turn_number INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (combat_id)
                    REFERENCES combat_sessions(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_achievement_progress_user
            ON achievement_progress_v5 (guild_id, user_id);

            CREATE INDEX IF NOT EXISTS idx_combat_actions_session
            ON combat_actions_v5 (combat_id, turn_number);
            """
        )
