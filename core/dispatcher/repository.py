from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from core.database import db_session
from core.dispatcher.models import (
    NotificationJob,
    NotificationStatus,
    QueuedNotification,
)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)

    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed


def _decode_payload(value: str | None) -> dict:
    try:
        payload = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}

    return payload if isinstance(payload, dict) else {}


def _row_to_notification(row) -> QueuedNotification:
    return QueuedNotification(
        id=int(row["id"]),
        notification_id=str(row["notification_id"]),
        guild_id=int(row["guild_id"]),
        channel_id=(
            int(row["channel_id"])
            if row["channel_id"] is not None
            else None
        ),
        user_id=(
            int(row["user_id"])
            if row["user_id"] is not None
            else None
        ),
        event_id=(
            str(row["event_id"])
            if row["event_id"] is not None
            else None
        ),
        notification_type=str(row["notification_type"]),
        title=str(row["title"]),
        description=str(row["description"]),
        payload=_decode_payload(row["payload_json"]),
        priority=int(row["priority"]),
        status=NotificationStatus(row["status"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        delete_after_seconds=(
            int(row["delete_after_seconds"])
            if row["delete_after_seconds"] is not None
            else None
        ),
        refresh_panel=bool(row["refresh_panel"]),
        available_at=_parse_datetime(row["available_at"]),
    )


def enqueue(job: NotificationJob) -> str:
    with db_session() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO notification_queue_v5 (
                notification_id,
                guild_id,
                channel_id,
                user_id,
                event_id,
                notification_type,
                title,
                description,
                payload_json,
                priority,
                status,
                attempts,
                max_attempts,
                delete_after_seconds,
                refresh_panel,
                available_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                'pending', 0, ?, ?, ?, ?, CURRENT_TIMESTAMP
            )
            """,
            (
                job.notification_id,
                job.guild_id,
                job.channel_id,
                job.user_id,
                job.event_id,
                job.notification_type,
                job.title,
                job.description,
                json.dumps(
                    job.payload,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    default=str,
                ),
                int(job.priority),
                job.max_attempts,
                job.delete_after_seconds,
                int(job.refresh_panel),
                job.available_at.isoformat(),
            ),
        )

    return job.notification_id


def get_by_notification_id(
    notification_id: str,
) -> QueuedNotification | None:
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM notification_queue_v5
            WHERE notification_id = ?
            """,
            (notification_id,),
        ).fetchone()

    return _row_to_notification(row) if row else None


def claim_next(
    worker_id: str,
) -> QueuedNotification | None:
    now = datetime.now(UTC).isoformat()

    with db_session() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM notification_queue_v5
            WHERE status IN ('pending', 'retry')
              AND available_at <= ?
              AND locked_at IS NULL
            ORDER BY priority DESC, available_at ASC, id ASC
            LIMIT 1
            """,
            (now,),
        ).fetchone()

        if row is None:
            return None

        updated = connection.execute(
            """
            UPDATE notification_queue_v5
            SET status = 'processing',
                locked_at = ?,
                locked_by = ?,
                attempts = attempts + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND locked_at IS NULL
              AND status IN ('pending', 'retry')
            """,
            (
                now,
                worker_id,
                row["id"],
            ),
        )

        if updated.rowcount != 1:
            return None

        claimed = connection.execute(
            """
            SELECT *
            FROM notification_queue_v5
            WHERE id = ?
            """,
            (row["id"],),
        ).fetchone()

    return _row_to_notification(claimed)


def mark_delivered(
    notification: QueuedNotification,
    *,
    discord_message_id: int | None = None,
) -> None:
    with db_session() as connection:
        connection.execute(
            """
            UPDATE notification_queue_v5
            SET status = 'delivered',
                locked_at = NULL,
                locked_by = NULL,
                delivered_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (notification.id,),
        )

        connection.execute(
            """
            INSERT INTO notification_history_v5 (
                notification_id,
                guild_id,
                channel_id,
                notification_type,
                title,
                status,
                attempts,
                discord_message_id
            )
            VALUES (?, ?, ?, ?, ?, 'delivered', ?, ?)
            """,
            (
                notification.notification_id,
                notification.guild_id,
                notification.channel_id,
                notification.notification_type,
                notification.title,
                notification.attempts,
                discord_message_id,
            ),
        )


def mark_retry(
    notification: QueuedNotification,
    *,
    error_text: str,
    retry_after_seconds: int,
) -> None:
    next_attempt = datetime.now(UTC) + timedelta(
        seconds=retry_after_seconds
    )

    with db_session() as connection:
        connection.execute(
            """
            UPDATE notification_queue_v5
            SET status = 'retry',
                available_at = ?,
                locked_at = NULL,
                locked_by = NULL,
                last_error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                next_attempt.isoformat(),
                error_text[:2000],
                notification.id,
            ),
        )


def move_to_dead_letter(
    notification: QueuedNotification,
    *,
    error_text: str,
) -> None:
    with db_session() as connection:
        connection.execute(
            """
            UPDATE notification_queue_v5
            SET status = 'dead_letter',
                locked_at = NULL,
                locked_by = NULL,
                last_error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                error_text[:2000],
                notification.id,
            ),
        )

        connection.execute(
            """
            INSERT OR REPLACE INTO notification_dead_letters_v5 (
                notification_id,
                guild_id,
                channel_id,
                notification_type,
                title,
                description,
                payload_json,
                attempts,
                last_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                notification.notification_id,
                notification.guild_id,
                notification.channel_id,
                notification.notification_type,
                notification.title,
                notification.description,
                json.dumps(
                    notification.payload,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    default=str,
                ),
                notification.attempts,
                error_text[:2000],
            ),
        )

        connection.execute(
            """
            INSERT INTO notification_history_v5 (
                notification_id,
                guild_id,
                channel_id,
                notification_type,
                title,
                status,
                attempts,
                error_text
            )
            VALUES (?, ?, ?, ?, ?, 'dead_letter', ?, ?)
            """,
            (
                notification.notification_id,
                notification.guild_id,
                notification.channel_id,
                notification.notification_type,
                notification.title,
                notification.attempts,
                error_text[:2000],
            ),
        )


def release_stale_locks(
    *,
    older_than_minutes: int = 5,
) -> int:
    stale_before = datetime.now(UTC) - timedelta(
        minutes=older_than_minutes
    )

    with db_session() as connection:
        result = connection.execute(
            """
            UPDATE notification_queue_v5
            SET status = 'retry',
                locked_at = NULL,
                locked_by = NULL,
                available_at = CURRENT_TIMESTAMP,
                last_error = 'Recovered stale dispatcher lock',
                updated_at = CURRENT_TIMESTAMP
            WHERE status = 'processing'
              AND locked_at < ?
            """,
            (stale_before.isoformat(),),
        )

        return int(result.rowcount)


def pending_count(guild_id: int | None = None) -> int:
    query = """
        SELECT COUNT(*) AS total
        FROM notification_queue_v5
        WHERE status IN ('pending', 'retry', 'processing')
    """
    parameters: tuple = ()

    if guild_id is not None:
        query += " AND guild_id = ?"
        parameters = (guild_id,)

    with db_session() as connection:
        row = connection.execute(
            query,
            parameters,
        ).fetchone()

    return int(row["total"]) if row else 0
