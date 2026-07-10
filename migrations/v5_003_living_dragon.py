from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS dragon_living_v5 (
                guild_id INTEGER PRIMARY KEY,
                hunger INTEGER NOT NULL DEFAULT 70,
                happiness INTEGER NOT NULL DEFAULT 70,
                energy INTEGER NOT NULL DEFAULT 70,
                cleanliness INTEGER NOT NULL DEFAULT 70,
                bond INTEGER NOT NULL DEFAULT 0,
                mood TEXT NOT NULL DEFAULT 'content',
                current_activity TEXT NOT NULL DEFAULT 'relaxing',
                last_care_at TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS dragon_personality_v5 (
                guild_id INTEGER NOT NULL,
                trait TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, trait)
            );

            CREATE TABLE IF NOT EXISTS dragon_relationships_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                bond INTEGER NOT NULL DEFAULT 0,
                trust INTEGER NOT NULL DEFAULT 0,
                care_actions INTEGER NOT NULL DEFAULT 0,
                play_actions INTEGER NOT NULL DEFAULT 0,
                training_actions INTEGER NOT NULL DEFAULT 0,
                gentle_wakeups INTEGER NOT NULL DEFAULT 0,
                last_interaction TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS dragon_memories_living_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER,
                username TEXT,
                memory_type TEXT NOT NULL,
                memory_text TEXT NOT NULL,
                importance INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_relationships_v5_guild_bond
            ON dragon_relationships_v5 (guild_id, bond DESC);

            CREATE INDEX IF NOT EXISTS idx_living_memories_guild
            ON dragon_memories_living_v5 (guild_id, created_at DESC);
            """
        )
