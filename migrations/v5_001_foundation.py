from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS dragon_state_v5 (
                guild_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL DEFAULT 'idle',
                state_started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                state_ends_at TEXT,
                state_payload TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS player_showcase_achievement (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                achievement_key TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS achievement_role_rewards (
                guild_id INTEGER NOT NULL,
                achievement_key TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, achievement_key)
            );

            CREATE TABLE IF NOT EXISTS combat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER,
                message_id INTEGER,
                dragon_hp INTEGER NOT NULL,
                dragon_max_hp INTEGER NOT NULL,
                enemy_key TEXT NOT NULL,
                enemy_hp INTEGER NOT NULL,
                enemy_max_hp INTEGER NOT NULL,
                turn_number INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'active',
                combat_data TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS temporary_messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                delete_at TEXT NOT NULL,
                message_type TEXT NOT NULL
            );
            """
        )
