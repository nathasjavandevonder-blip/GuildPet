from datetime import datetime, timezone
from database import connect

def add_memory(guild_id: int, text: str):
    con = connect()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO memories (guild_id, text, created_at) VALUES (?, ?, ?)",
        (guild_id, text, datetime.now(timezone.utc).isoformat())
    )
    con.commit()
    con.close()

def get_memories(guild_id: int, limit: int = 10):
    con = connect()
    cur = con.cursor()
    cur.execute("""
        SELECT text, created_at FROM memories
        WHERE guild_id=?
        ORDER BY id DESC
        LIMIT ?
    """, (guild_id, limit))
    rows = cur.fetchall()
    con.close()
    return rows
