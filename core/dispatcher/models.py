from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any
from uuid import uuid4


class NotificationPriority(IntEnum):
    LOW = 25
    NORMAL = 50
    HIGH = 75
    CRITICAL = 100


class NotificationStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    RETRY = "retry"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class NotificationJob:
    guild_id: int
    notification_type: str
    title: str
    description: str
    channel_id: int | None = None
    user_id: int | None = None
    event_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL
    delete_after_seconds: int | None = None
    refresh_panel: bool = False
    max_attempts: int = 3
    available_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    notification_id: str = field(
        default_factory=lambda: str(uuid4())
    )


@dataclass(frozen=True, slots=True)
class QueuedNotification:
    id: int
    notification_id: str
    guild_id: int
    channel_id: int | None
    user_id: int | None
    event_id: str | None
    notification_type: str
    title: str
    description: str
    payload: dict[str, Any]
    priority: int
    status: NotificationStatus
    attempts: int
    max_attempts: int
    delete_after_seconds: int | None
    refresh_panel: bool
    available_at: datetime
