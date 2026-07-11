from __future__ import annotations

import json

from core.database import db_session
from core.events.models import DomainEvent


def save_event(event: DomainEvent) -> None:
    with db_session() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO domain_events_v5 (
                event_id,
                event_type,
                guild_id,
                actor_user_id,
                actor_username,
                payload_json,
                source,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'published', ?)
            """,
            (
                event.event_id,
                event.event_type,
                event.guild_id,
                event.actor_user_id,
                event.actor_username,
                json.dumps(
                    event.payload,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    default=str,
                ),
                event.source,
                event.created_at.isoformat(),
            ),
        )


def record_handler_result(
    event_id: str,
    handler_name: str,
    *,
    status: str,
    error_text: str | None = None,
) -> None:
    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO event_handler_log_v5 (
                event_id,
                handler_name,
                status,
                error_text
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT (event_id, handler_name)
            DO UPDATE SET
                status = excluded.status,
                error_text = excluded.error_text,
                handled_at = CURRENT_TIMESTAMP
            """,
            (
                event_id,
                handler_name,
                status,
                error_text,
            ),
        )


def recent_events(
    guild_id: int,
    *,
    limit: int = 25,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM domain_events_v5
            WHERE guild_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                guild_id,
                limit,
            ),
        ).fetchall()
