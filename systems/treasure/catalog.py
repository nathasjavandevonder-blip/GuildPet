from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TreasureEntry:
    item_key: str
    weight: int
    minimum: int = 1
    maximum: int = 1


TREASURE_TABLES: dict[
    str,
    tuple[TreasureEntry, ...],
] = {
    "forest": (
        TreasureEntry("gold_coin", 40, 10, 25),
        TreasureEntry("forest_herb", 25, 1, 2),
        TreasureEntry("forest_mushroom", 15, 1, 2),
        TreasureEntry("fallen_branch", 10, 1, 3),
        TreasureEntry("polished_gem", 8),
        TreasureEntry("ancient_key", 2),
    ),
}
