from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS guild_setup_v55 (
                guild_id INTEGER PRIMARY KEY,
                setup_complete INTEGER NOT NULL DEFAULT 0,
                dragon_channel_id INTEGER,
                welcome_channel_id INTEGER,
                log_channel_id INTEGER,
                ai_activity TEXT NOT NULL DEFAULT 'normal',
                ai_max_per_hour INTEGER NOT NULL DEFAULT 4,
                welcome_enabled INTEGER NOT NULL DEFAULT 1,
                mention_replies INTEGER NOT NULL DEFAULT 1,
                spontaneous_chat INTEGER NOT NULL DEFAULT 1,
                vote_duration_hours INTEGER NOT NULL DEFAULT 48,
                incubation_days INTEGER NOT NULL DEFAULT 7,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS guild_ai_channels_v55 (
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, channel_id)
            );

            CREATE TABLE IF NOT EXISTS dragon_lifecycle_v55 (
                guild_id INTEGER PRIMARY KEY,
                lifecycle_stage TEXT NOT NULL DEFAULT 'unconfigured',
                selected_egg TEXT,
                vote_started_at TEXT,
                vote_ends_at TEXT,
                incubation_started_at TEXT,
                hatch_at TEXT,
                hatched_at TEXT,
                dragon_number INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS egg_votes_v55 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                egg_key TEXT NOT NULL,
                voted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS egg_care_v55 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                care_date TEXT NOT NULL,
                action_key TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id, care_date)
            );

            CREATE TABLE IF NOT EXISTS feature_unlocks_v55 (
                feature_key TEXT PRIMARY KEY,
                required_stage TEXT NOT NULL,
                description TEXT NOT NULL
            );

            INSERT OR IGNORE INTO feature_unlocks_v55 VALUES
                ('egg_care', 'incubating', 'Care for the selected egg'),
                ('feed', 'hatchling', 'Feed the hatchling'),
                ('play', 'hatchling', 'Play with the hatchling'),
                ('bond', 'hatchling', 'Build a bond'),
                ('sleep', 'hatchling', 'Rest and sleep'),
                ('travel', 'young', 'Travel beyond the nest'),
                ('combat', 'young', 'Fight and train in combat'),
                ('inventory', 'young', 'Use inventory and equipment'),
                ('lair', 'adult', 'Build and improve the lair'),
                ('crafting', 'adult', 'Craft items and upgrades'),
                ('raids', 'ancient', 'Join major guild raids'),
                ('second_egg', 'elder', 'Begin the dragon legacy');

            CREATE INDEX IF NOT EXISTS idx_egg_votes_guild
            ON egg_votes_v55 (guild_id, egg_key);
            """
        )
