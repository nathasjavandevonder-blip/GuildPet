from systems.items.catalog import get_item
from systems.treasure.service import roll_treasure


def main() -> None:
    valid_items = {
        "gold_coin",
        "forest_herb",
        "forest_mushroom",
        "fallen_branch",
        "polished_gem",
        "ancient_key",
    }

    for _ in range(100):
        reward = roll_treasure("forest")

        assert reward.item_key in valid_items
        assert reward.quantity >= 1
        assert reward.definition == get_item(
            reward.item_key
        )

    print("Treasure table: passed")
    print("Treasure item definitions: passed")
    print("V5 treasure test passed.")


if __name__ == "__main__":
    main()
