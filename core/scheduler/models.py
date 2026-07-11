from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any
from uuid import uuid4


class JobPriority(IntEnum):
    LOW = 25
    NORMAL = 50
    HIGH = 75
    CRITICAL = 100


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class SchedulerJob:
    guild_id: int
    job_type: str
    payload: dict[str, Any] = field(default_factory=dict)

    run_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    priority: JobPriority = JobPriority.NORMAL

    repeat: bool = False

    interval_seconds: int | None = None

    max_attempts: int = 3

    job_uuid: str = field(
        default_factory=lambda: str(uuid4())
    )


@dataclass(slots=True)
class QueuedJob:
    id: int
    job_uuid: str

    guild_id: int

    job_type: str

    payload: dict[str, Any]

    run_at: datetime

    priority: int

    repeat: bool

    interval_seconds: int | None

    attempts: int

    max_attempts: int

    status: JobStatus
