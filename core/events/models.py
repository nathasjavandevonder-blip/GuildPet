from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_type: str
    guild_id: int
    actor_user_id: int | None = None
    actor_username: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    source: str | None = None
    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
