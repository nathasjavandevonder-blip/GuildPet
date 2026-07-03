from datetime import datetime, timezone
from database import db_session, execute_with_retry

def add_memory(guild_id: int, text: str):
    def work():
        with db_session() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO memories (guild_id, text, created_at) VALUES (?, ?, ?)",
                (guild_id, text, datetime.now(timezone.utc).isoformat())
            )

    execute_with_retry(work)

def get_memories(guild_id: int, limit: int = 10):
    with db_session() as con:
        cur = con.cursor()
        cur.execute(
            "SELECT text, created_at FROM memories WHERE guild_id=? ORDER BY id DESC LIMIT ?",
            (guild_id, limit)
        )
        return cur.fetchall()
