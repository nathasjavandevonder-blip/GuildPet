from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from core.dispatcher.models import (
    NotificationJob,
    NotificationPriority,
    QueuedNotification,
)
from core.dispatcher.repository import (
    claim_next,
    enqueue,
    get_by_notification_id,
    mark_delivered,
    mark_retry,
    move_to_dead_letter,
    pending_count,
    release_stale_locks,
)


class NotificationQueue:
    def enqueue(
        self,
        *,
        guild_id: int,
        notification_type: str,
        title: str,
        description: str,
        channel_id: int | None = None,
        user_id: int | None = None,
        event_id: str | None = None,
        payload: dict[str, Any] | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        delete_after_seconds: int | None = None,
        refresh_panel: bool = False,
        max_attempts: int = 3,
        delay_seconds: int = 0,
    ) -> str:
        available_at = datetime.now(UTC) + timedelta(
            seconds=max(delay_seconds, 0)
        )

        job = NotificationJob(
            guild_id=guild_id,
            notification_type=notification_type,
            title=title,
            description=description,
            channel_id=channel_id,
            user_id=user_id,
            event_id=event_id,
            payload=payload or {},
            priority=priority,
            delete_after_seconds=delete_after_seconds,
            refresh_panel=refresh_panel,
            max_attempts=max_attempts,
            available_at=available_at,
        )

        return enqueue(job)

    def get(
        self,
        notification_id: str,
    ) -> QueuedNotification | None:
        return get_by_notification_id(notification_id)

    def claim(
        self,
        worker_id: str,
    ) -> QueuedNotification | None:
        return claim_next(worker_id)

    def delivered(
        self,
        notification: QueuedNotification,
        *,
        discord_message_id: int | None = None,
    ) -> None:
        mark_delivered(
            notification,
            discord_message_id=discord_message_id,
        )

    def failed(
        self,
        notification: QueuedNotification,
        *,
        error: Exception | str,
    ) -> str:
        error_text = str(error)

        if notification.attempts >= notification.max_attempts:
            move_to_dead_letter(
                notification,
                error_text=error_text,
            )
            return "dead_letter"

        retry_delay = min(
            30 * (2 ** max(notification.attempts - 1, 0)),
            900,
        )

        mark_retry(
            notification,
            error_text=error_text,
            retry_after_seconds=retry_delay,
        )

        return "retry"

    def pending_count(
        self,
        guild_id: int | None = None,
    ) -> int:
        return pending_count(guild_id)

    def recover_stale_jobs(
        self,
        *,
        older_than_minutes: int = 5,
    ) -> int:
        return release_stale_locks(
            older_than_minutes=older_than_minutes
        )


notification_queue = NotificationQueue()
