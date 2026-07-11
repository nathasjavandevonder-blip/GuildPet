from ui.encounters.gathering import (
    build_gathering_encounter,
)
from ui.encounters.models import EncounterContext
from ui.encounters.registry import (
    build_encounter,
    register_handler,
)
from ui.encounters.treasure import (
    build_treasure_encounter,
)


register_handler(
    "gather",
    build_gathering_encounter,
)

register_handler(
    "treasure",
    build_treasure_encounter,
)


__all__ = [
    "EncounterContext",
    "build_encounter",
    "register_handler",
]
