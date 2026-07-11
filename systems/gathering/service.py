from __future__ import annotations

import random
from dataclasses import dataclass

from systems.gathering.catalog import GATHER_TABLES
from systems.items.catalog import ItemDefinition, get_item


@dataclass(frozen=True, slots=True)
class GatherResult:
    location_key: str
    item_key: str
    quantity: int
    definition: ItemDefinition


def roll_resource(location_key: str) -> GatherResult:
    table = GATHER_TABLES.get(location_key)

    if not table:
        raise ValueError(
            f"No gathering table exists for {location_key!r}."
        )

    resource = random.choices(
        table,
        weights=[entry.weight for entry in table],
        k=1,
    )[0]

    quantity = random.randint(
        resource.minimum,
        resource.maximum,
    )

    return GatherResult(
        location_key=location_key,
        item_key=resource.item_key,
        quantity=quantity,
        definition=get_item(resource.item_key),
    )
