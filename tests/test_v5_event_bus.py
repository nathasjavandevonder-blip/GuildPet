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
