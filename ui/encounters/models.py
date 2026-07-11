from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EncounterContext:
    guild_id: int
    location_key: str
    encounter_key: str
    story: str
