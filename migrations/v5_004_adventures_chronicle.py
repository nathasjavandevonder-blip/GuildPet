from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS adventure_runs_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                starter_user_id INTEGER,
                starter_username TEXT,
                adventure_key TEXT NOT NULL,
                current_node TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                total_xp INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                loot_json TEXT NOT NULL DEFAULT '[]',
                story_log_json TEXT NOT NULL DEFAULT '[]',
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS adventure_choices_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adventure_run_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                node_key TEXT NOT NULL,
                choice_key TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (adventure_run_id)
                    REFERENCES adventure_runs_v5(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS player_wallet_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                tokens INTEGER NOT NULL DEFAULT 0,
                adventure_xp INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS player_items_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                item_key TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id, item_key)
            );

            CREATE TABLE IF NOT EXISTS guild_chronicle_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                entry_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                importance INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_adventure_runs_guild
            ON adventure_runs_v5 (guild_id, status);

            CREATE INDEX IF NOT EXISTS idx_adventure_choices_run
            ON adventure_choices_v5 (adventure_run_id);

            CREATE INDEX IF NOT EXISTS idx_chronicle_guild
            ON guild_chronicle_v5 (guild_id, created_at DESC);
            """
        )
