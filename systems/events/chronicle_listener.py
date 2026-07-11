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
