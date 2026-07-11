from __future__ import annotations

import random
from dataclasses import dataclass

from systems.items.catalog import (
    ItemDefinition,
    get_item,
)
from systems.treasure.catalog import TREASURE_TABLES


@dataclass(frozen=True, slots=True)
class TreasureReward:
    location_key: str
    item_key: str
    quantity: int
    definition: ItemDefinition


def roll_treasure(
    location_key: str,
) -> TreasureReward:
    table = TREASURE_TABLES.get(location_key)

    if not table:
        raise ValueError(
            f"No treasure table exists for {location_key!r}."
        )

    entry = random.choices(
        table,
        weights=[item.weight for item in table],
        k=1,
    )[0]

    quantity = random.randint(
        entry.minimum,
        entry.maximum,
    )

    return TreasureReward(
        location_key=location_key,
        item_key=entry.item_key,
        quantity=quantity,
        definition=get_item(entry.item_key),
    )
