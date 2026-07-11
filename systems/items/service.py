from __future__ import annotations

from systems.items.catalog import get_item
from systems.items.models import InventoryItem
from systems.items.repository import (
    add_quantity,
    clear_all,
    get_all_stacks,
    get_stack,
    remove_quantity,
)


def _validate_quantity(quantity: int) -> None:
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("Quantity must be an integer.")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")


def count_item(
    guild_id: int,
    item_key: str,
) -> int:
    row = get_stack(guild_id, item_key)

    if row is None:
        return 0

    return int(row["quantity"])


def has_item(
    guild_id: int,
    item_key: str,
    quantity: int = 1,
) -> bool:
    _validate_quantity(quantity)
    return count_item(guild_id, item_key) >= quantity


def add_item(
    guild_id: int,
    item_key: str,
    quantity: int = 1,
) -> InventoryItem:
    _validate_quantity(quantity)

    new_quantity = add_quantity(
        guild_id,
        item_key,
        quantity,
    )

    return InventoryItem(
        guild_id=guild_id,
        item_key=item_key,
        quantity=new_quantity,
        definition=get_item(item_key),
    )


def remove_item(
    guild_id: int,
    item_key: str,
    quantity: int = 1,
) -> InventoryItem | None:
    _validate_quantity(quantity)

    remaining = remove_quantity(
        guild_id,
        item_key,
        quantity,
    )

    if remaining is None:
        return None

    return InventoryItem(
        guild_id=guild_id,
        item_key=item_key,
        quantity=remaining,
        definition=get_item(item_key),
    )


def get_inventory(
    guild_id: int,
) -> list[InventoryItem]:
    rows = get_all_stacks(guild_id)

    return [
        InventoryItem(
            guild_id=int(row["guild_id"]),
            item_key=str(row["item_key"]),
            quantity=int(row["quantity"]),
            definition=get_item(str(row["item_key"])),
        )
        for row in rows
    ]


def clear_inventory(guild_id: int) -> int:
    return clear_all(guild_id)
