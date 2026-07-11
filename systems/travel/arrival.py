from __future__ import annotations

from random import choice

from systems.travel.ambient import (
    FOREST_AMBIENT,
    MINE_AMBIENT,
    RIVER_AMBIENT,
    VOLCANO_AMBIENT,
)
from systems.travel.encounter import roll_encounter




SAFE_LOCATIONS = {
    "guild_hall",
}

AMBIENT_TABLES = {
    "forest": FOREST_AMBIENT,
    "river": RIVER_AMBIENT,
    "mine": MINE_AMBIENT,
    "volcano": VOLCANO_AMBIENT,
}


def handle_arrival(location_key: str) -> dict[str, str]:
    ambient_lines = AMBIENT_TABLES.get(
        location_key,
        ["🐉 The dragon arrived safely."],
    )

    encounter = (
        "nothing"
        if location_key in SAFE_LOCATIONS
        else roll_encounter()
    )

    return {
        "location_key": location_key,
        "story": choice(ambient_lines),
        "encounter": encounter,
    }
