from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GatherResource:
    item_key: str
    weight: int
    minimum: int = 1
    maximum: int = 1


GATHER_TABLES: dict[str, tuple[GatherResource, ...]] = {
    "forest": (
        GatherResource("forest_herb", 40, 1, 2),
        GatherResource("forest_mushroom", 30, 1, 2),
        GatherResource("fallen_branch", 20, 1, 3),
        GatherResource("forest_berries", 10, 1, 2),
    ),
}
