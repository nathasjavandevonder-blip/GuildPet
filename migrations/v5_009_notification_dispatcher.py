from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS notification_queue_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT NOT NULL UNIQUE,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER,
                user_id INTEGER,
                event_id TEXT,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                priority INTEGER NOT NULL DEFAULT 50,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                delete_after_seconds INTEGER,
                refresh_panel INTEGER NOT NULL DEFAULT 0,
                available_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                locked_at TEXT,
                locked_by TEXT,
                last_error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                delivered_at TEXT
            );

            CREATE TABLE IF NOT EXISTS notification_history_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                discord_message_id INTEGER,
                error_text TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notification_dead_letters_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT NOT NULL UNIQUE,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                attempts INTEGER NOT NULL,
                last_error TEXT,
                failed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_notification_queue_ready
            ON notification_queue_v5 (
                status,
                available_at,
                priority DESC,
                id ASC
            );

            CREATE INDEX IF NOT EXISTS idx_notification_queue_guild
            ON notification_queue_v5 (
                guild_id,
                status,
                id DESC
            );

            CREATE INDEX IF NOT EXISTS idx_notification_history_guild
            ON notification_history_v5 (
                guild_id,
                id DESC
            );
            """
        )
