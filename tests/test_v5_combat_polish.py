from systems.items.catalog import format_item, get_item
from systems.living.service import (
    apply_combat_aftermath,
    finish_combat_recovery,
)
from systems.state.models import DragonState
from systems.state.service import get_state


def main() -> None:
    guild_id = 990007

    item = get_item("goblin_tooth")
    assert item.name == "Goblin Tooth"
    assert "🦷" in format_item("goblin_tooth")

    recovering = apply_combat_aftermath(guild_id)
    assert recovering.current_activity == "catching its breath"

    recovered = finish_combat_recovery(guild_id)
    assert recovered.current_activity == "watching the guild"

    print("Formatted item:", format_item("goblin_tooth"))
    print("Recovery activity:", recovered.current_activity)
    print("V5 combat polish test passed.")


if __name__ == "__main__":
    main()
