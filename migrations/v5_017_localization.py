from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS user_settings_v55 (
                user_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'en',
                timezone TEXT NOT NULL DEFAULT 'UTC',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
