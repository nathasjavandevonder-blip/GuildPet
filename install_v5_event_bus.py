from pathlib import Path

FILES = {
    "migrations/v5_008_event_bus.py": r'''
from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS domain_events_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                actor_user_id INTEGER,
                actor_username TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}',
                source TEXT,
                status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS event_handler_log_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                handler_name TEXT NOT NULL,
                status TEXT NOT NULL,
                error_text TEXT,
                handled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (event_id, handler_name),
                FOREIGN KEY (event_id)
                    REFERENCES domain_events_v5(event_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS guild_notifications_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                event_id TEXT,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                delivered INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                delivered_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_domain_events_guild
            ON domain_events_v5 (guild_id, id DESC);

            CREATE INDEX IF NOT EXISTS idx_domain_events_type
            ON domain_events_v5 (event_type, id DESC);

            CREATE INDEX IF NOT EXISTS idx_handler_log_event
            ON event_handler_log_v5 (event_id);

            CREATE INDEX IF NOT EXISTS idx_notifications_pending
            ON guild_notifications_v5 (
                guild_id,
                delivered,
                id
            );
            """
        )
''',

    "core/events/__init__.py": r'''
from core.events.bus import event_bus
from core.events.models import DomainEvent

__all__ = [
    "DomainEvent",
    "event_bus",
]
''',

    "core/events/models.py": r'''
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
''',

    "core/events/repository.py": r'''
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
''',

    "core/events/bus.py": r'''
from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from core.events.models import DomainEvent
from core.events.repository import (
    record_handler_result,
    save_event,
)

EventHandler = Callable[
    [DomainEvent],
    Awaitable[None] | None,
]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[
            str,
            list[EventHandler],
        ] = defaultdict(list)

        self._wildcard_handlers: list[EventHandler] = []

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        handlers = self._handlers[event_type]

        if handler not in handlers:
            handlers.append(handler)

    def subscribe_all(
        self,
        handler: EventHandler,
    ) -> None:
        if handler not in self._wildcard_handlers:
            self._wildcard_handlers.append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        handlers = self._handlers.get(event_type)

        if handlers and handler in handlers:
            handlers.remove(handler)

    async def publish(
        self,
        event: DomainEvent,
    ) -> list[Exception]:
        save_event(event)

        handlers = [
            *self._handlers.get(event.event_type, []),
            *self._wildcard_handlers,
        ]

        errors: list[Exception] = []

        for handler in handlers:
            handler_name = (
                f"{handler.__module__}."
                f"{getattr(handler, '__qualname__', handler.__name__)}"
            )

            try:
                result = handler(event)

                if inspect.isawaitable(result):
                    await result

                record_handler_result(
                    event.event_id,
                    handler_name,
                    status="success",
                )

            except Exception as exc:
                errors.append(exc)

                record_handler_result(
                    event.event_id,
                    handler_name,
                    status="failed",
                    error_text=repr(exc),
                )

                print(
                    f"Event handler failed: "
                    f"{event.event_type} -> "
                    f"{handler_name}: {exc}"
                )

        return errors

    async def emit(
        self,
        event_type: str,
        *,
        guild_id: int,
        actor_user_id: int | None = None,
        actor_username: str | None = None,
        payload: dict[str, Any] | None = None,
        source: str | None = None,
    ) -> DomainEvent:
        event = DomainEvent(
            event_type=event_type,
            guild_id=guild_id,
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            payload=payload or {},
            source=source,
        )

        await self.publish(event)
        return event


event_bus = EventBus()
''',

    "systems/events/__init__.py": r'''
from systems.events.registry import register_event_handlers

__all__ = ["register_event_handlers"]
''',

    "systems/events/types.py": r'''
DRAGON_CARE_COMPLETED = "dragon.care.completed"
DRAGON_WOKE_GENTLY = "dragon.woke_gently"

COMBAT_STARTED = "combat.started"
COMBAT_ACTION_USED = "combat.action_used"
COMBAT_WON = "combat.won"
COMBAT_LOST = "combat.lost"
COMBAT_RETREATED = "combat.retreated"

ADVENTURE_STARTED = "adventure.started"
ADVENTURE_CHOICE_MADE = "adventure.choice_made"
ADVENTURE_COMPLETED = "adventure.completed"

WORLD_WEATHER_CHANGED = "world.weather_changed"
WORLD_LOCATION_CHANGED = "world.location_changed"

ACHIEVEMENT_UNLOCKED = "achievement.unlocked"
''',

    "systems/events/notifications.py": r'''
from __future__ import annotations

import json
from typing import Any

from core.database import db_session
from core.events.models import DomainEvent


NOTIFICATION_EVENTS = {
    "combat.won": (
        "combat_reward",
        "Combat Victory",
    ),
    "combat.lost": (
        "combat_result",
        "Combat Defeat",
    ),
    "adventure.completed": (
        "adventure_reward",
        "Adventure Complete",
    ),
    "achievement.unlocked": (
        "achievement",
        "Achievement Unlocked",
    ),
    "world.weather_changed": (
        "world",
        "Weather Changed",
    ),
}


def _description_for(
    event: DomainEvent,
) -> str:
    payload = event.payload

    if event.event_type == "combat.won":
        enemy = payload.get("enemy_name", "an enemy")
        xp = payload.get("xp", 0)
        tokens = payload.get("tokens", 0)

        return (
            f"The dragon defeated **{enemy}** and earned "
            f"**{xp} XP** and **{tokens} tokens**."
        )

    if event.event_type == "adventure.completed":
        adventure = payload.get(
            "adventure_name",
            "an adventure",
        )

        return (
            f"The dragon safely completed "
            f"**{adventure}**."
        )

    if event.event_type == "achievement.unlocked":
        name = payload.get(
            "achievement_name",
            payload.get("achievement_key", "Unknown"),
        )

        return f"**{name}** was unlocked."

    if event.event_type == "world.weather_changed":
        weather = payload.get("weather_name", "Unknown")

        return f"The weather is now **{weather}**."

    return str(
        payload.get(
            "description",
            event.event_type,
        )
    )


async def notification_listener(
    event: DomainEvent,
) -> None:
    notification = NOTIFICATION_EVENTS.get(
        event.event_type
    )

    if notification is None:
        return

    notification_type, title = notification

    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO guild_notifications_v5 (
                guild_id,
                event_id,
                notification_type,
                title,
                description,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.guild_id,
                event.event_id,
                notification_type,
                title,
                _description_for(event),
                json.dumps(
                    event.payload,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    default=str,
                ),
            ),
        )


def get_pending_notifications(
    guild_id: int,
    *,
    limit: int = 20,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM guild_notifications_v5
            WHERE guild_id = ?
              AND delivered = 0
            ORDER BY id ASC
            LIMIT ?
            """,
            (
                guild_id,
                limit,
            ),
        ).fetchall()


def mark_notifications_delivered(
    notification_ids: list[int],
) -> None:
    if not notification_ids:
        return

    placeholders = ",".join(
        "?" for _ in notification_ids
    )

    with db_session() as connection:
        connection.execute(
            f"""
            UPDATE guild_notifications_v5
            SET delivered = 1,
                delivered_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
            """,
            notification_ids,
        )
''',

    "systems/events/chronicle_listener.py": r'''
from __future__ import annotations

from core.events.models import DomainEvent
from systems.chronicle.service import add_chronicle_entry


CHRONICLE_EVENTS = {
    "combat.won": 2,
    "combat.lost": 1,
    "adventure.completed": 2,
    "world.location_changed": 1,
}


async def chronicle_event_listener(
    event: DomainEvent,
) -> None:
    importance = CHRONICLE_EVENTS.get(
        event.event_type
    )

    if importance is None:
        return

    payload = event.payload

    if event.event_type == "combat.won":
        title = (
            f"Victory over "
            f"{payload.get('enemy_name', 'an enemy')}"
        )
        description = (
            f"{event.actor_username or 'A guild member'} "
            f"guided the dragon to victory."
        )

    elif event.event_type == "combat.lost":
        title = "The dragon was defeated"
        description = (
            "The dragon returned home to recover."
        )

    elif event.event_type == "adventure.completed":
        title = (
            f"Completed: "
            f"{payload.get('adventure_name', 'Adventure')}"
        )
        description = (
            f"The dragon returned with "
            f"{payload.get('xp', 0)} XP and "
            f"{payload.get('tokens', 0)} tokens."
        )

    elif event.event_type == "world.location_changed":
        title = "The dragon travelled"
        description = (
            f"The dragon moved to "
            f"{payload.get('location_name', 'a new location')}."
        )

    else:
        return

    add_chronicle_entry(
        event.guild_id,
        entry_type=event.event_type,
        title=title,
        description=description,
        importance=importance,
        metadata={
            "event_id": event.event_id,
            **payload,
        },
    )
''',

    "systems/events/registry.py": r'''
from __future__ import annotations

from core.events.bus import event_bus
from systems.events.chronicle_listener import (
    chronicle_event_listener,
)
from systems.events.notifications import (
    notification_listener,
)

_registered = False


def register_event_handlers() -> None:
    global _registered

    if _registered:
        return

    event_bus.subscribe_all(
        notification_listener,
    )

    # Chronicle listener is disabled for combat/adventure
    # while old direct Chronicle calls still exist.
    # It becomes active after those old calls are removed.
    #
    # event_bus.subscribe_all(
    #     chronicle_event_listener,
    # )

    _registered = True
    print("GuildPet v5 event handlers registered.")
''',

    "tests/test_v5_event_bus.py": r'''
from core.database import db_session
from core.events.bus import EventBus
from core.events.models import DomainEvent
from core.events.repository import recent_events


async def main() -> None:
    guild_id = 990009
    received: list[str] = []

    bus = EventBus()

    async def test_handler(
        event: DomainEvent,
    ) -> None:
        received.append(event.event_type)

    bus.subscribe(
        "test.completed",
        test_handler,
    )

    event = await bus.emit(
        "test.completed",
        guild_id=guild_id,
        actor_user_id=123,
        actor_username="Event Tester",
        payload={
            "value": 42,
        },
        source="test_suite",
    )

    assert received == ["test.completed"]

    events = recent_events(
        guild_id,
        limit=5,
    )

    assert events
    assert events[0]["event_id"] == event.event_id
    assert events[0]["event_type"] == "test.completed"

    with db_session() as connection:
        handler = connection.execute(
            """
            SELECT *
            FROM event_handler_log_v5
            WHERE event_id = ?
            """,
            (event.event_id,),
        ).fetchone()

    assert handler is not None
    assert handler["status"] == "success"

    print("Event ID:", event.event_id)
    print("Recorded events:", len(events))
    print("V5 event bus test passed.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
''',
}

for filename, content in FILES.items():
    path = Path(filename)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        content.lstrip(),
        encoding="utf-8",
    )
    print(f"Created {filename}")

print(
    f"\nCreated {len(FILES)} "
    "Event Bus files."
)
