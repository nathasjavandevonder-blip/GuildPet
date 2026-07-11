from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS domain_events_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                actor_user_id INTEGER,
                actor_username TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}',
                source TEXT,
                status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS event_handler_log_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                handler_name TEXT NOT NULL,
                status TEXT NOT NULL,
                error_text TEXT,
                handled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (event_id, handler_name),
                FOREIGN KEY (event_id)
                    REFERENCES domain_events_v5(event_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS guild_notifications_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                event_id TEXT,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                delivered INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                delivered_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_domain_events_guild
            ON domain_events_v5 (guild_id, id DESC);

            CREATE INDEX IF NOT EXISTS idx_domain_events_type
            ON domain_events_v5 (event_type, id DESC);

            CREATE INDEX IF NOT EXISTS idx_handler_log_event
            ON event_handler_log_v5 (event_id);

            CREATE INDEX IF NOT EXISTS idx_notifications_pending
            ON guild_notifications_v5 (
                guild_id,
                delivered,
                id
            );
            """
        )
