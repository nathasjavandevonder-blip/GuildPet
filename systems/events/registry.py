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
