from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class DragonState(StrEnum):
    IDLE = "idle"
    SLEEPING = "sleeping"
    ADVENTURE = "adventure"
    COMBAT = "combat"
    RECOVERING = "recovering"
    CELEBRATING = "celebrating"


@dataclass(slots=True)
class StateRecord:
    guild_id: int
    state: DragonState
    started_at: datetime
    ends_at: datetime | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def is_timed(self) -> bool:
        return self.ends_at is not None

    def has_expired(self, now: datetime) -> bool:
        return self.ends_at is not None and now >= self.ends_at
