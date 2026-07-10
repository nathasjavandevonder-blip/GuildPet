from __future__ import annotations

import json
from typing import Any

from core.database import db_session


def add_chronicle_entry(
    guild_id: int,
    *,
    entry_type: str,
    title: str,
    description: str,
    importance: int = 1,
    metadata: dict[str, Any] | None = None,
) -> int:
    with db_session() as connection:
        cursor = connection.execute(
            """
            INSERT INTO guild_chronicle_v5 (
                guild_id,
                entry_type,
                title,
                description,
                importance,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                entry_type,
                title,
                description,
                importance,
                json.dumps(metadata or {}, separators=(",", ":")),
            ),
        )

        return int(cursor.lastrowid)


def get_chronicle(
    guild_id: int,
    *,
    limit: int = 20,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM guild_chronicle_v5
            WHERE guild_id = ?
            ORDER BY importance DESC, id DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ).fetchall()
