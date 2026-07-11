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
