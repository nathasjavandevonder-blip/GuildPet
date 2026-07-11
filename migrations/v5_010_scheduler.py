from core.database import db_session


def upgrade():
    with db_session() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS scheduler_jobs_v5 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_uuid TEXT NOT NULL UNIQUE,
            guild_id INTEGER NOT NULL,
            job_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            run_at TEXT NOT NULL,
            interval_seconds INTEGER,
            repeat INTEGER NOT NULL DEFAULT 0,
            priority INTEGER NOT NULL DEFAULT 50,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            locked_by TEXT,
            locked_at TEXT,
            last_error TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_scheduler_ready
        ON scheduler_jobs_v5 (
            status,
            run_at,
            priority DESC,
            id ASC
        );
        """)
