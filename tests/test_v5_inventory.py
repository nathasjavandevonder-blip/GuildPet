from systems.items.service import (
    add_item,
    clear_inventory,
    count_item,
    get_inventory,
    has_item,
    remove_item,
)


def main() -> None:
    guild_id = 990014

    clear_inventory(guild_id)

    first = add_item(
        guild_id,
        "forest_herb",
        3,
    )

    assert first.quantity == 3
    assert count_item(guild_id, "forest_herb") == 3
    assert has_item(guild_id, "forest_herb")
    assert has_item(guild_id, "forest_herb", 3)
    assert not has_item(guild_id, "forest_herb", 4)

    stacked = add_item(
        guild_id,
        "forest_herb",
        2,
    )

    assert stacked.quantity == 5

    mushroom = add_item(
        guild_id,
        "forest_mushroom",
        4,
    )

    assert mushroom.quantity == 4

    removed = remove_item(
        guild_id,
        "forest_herb",
        2,
    )

    assert removed is not None
    assert removed.quantity == 3

    failed = remove_item(
        guild_id,
        "forest_herb",
        99,
    )

    assert failed is None
    assert count_item(guild_id, "forest_herb") == 3

    inventory = get_inventory(guild_id)

    assert len(inventory) == 2

    quantities = {
        item.item_key: item.quantity
        for item in inventory
    }

    assert quantities == {
        "forest_herb": 3,
        "forest_mushroom": 4,
    }

    deleted = clear_inventory(guild_id)

    assert deleted == 2
    assert get_inventory(guild_id) == []

    print("Inventory stacking: passed")
    print("Inventory removal: passed")
    print("Inventory validation: passed")
    print("V5 inventory test passed.")


if __name__ == "__main__":
    main()
