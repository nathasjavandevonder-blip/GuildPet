from systems.adventures.service import (
    choose_adventure_path,
    get_active_adventure,
    start_adventure,
)
from systems.achievements.service import (
    add_progress,
    completion_summary,
    get_showcase,
    set_showcase,
)
from systems.chronicle.service import get_chronicle
from systems.state.models import DragonState
from systems.state.service import get_state


def main() -> None:
    guild_id = 990005
    user_id = 880005
    username = "Alpha Tester"

    add_progress(guild_id, user_id, "feeds", 25)
    assert set_showcase(
        guild_id,
        user_id,
        "dragon_chef_25",
    )
    assert get_showcase(guild_id, user_id) is not None

    result = start_adventure(
        guild_id,
        user_id=user_id,
        username=username,
        adventure_key="whispering_forest",
    )

    print("Started:", result.adventure_name)
    print("Node:", result.current_node)
    print("Choices:", [choice.key for choice in result.choices])

    safety = 0

    while get_active_adventure(guild_id) is not None:
        run = get_active_adventure(guild_id)
        result = choose_adventure_path(
            guild_id,
            user_id=user_id,
            username=username,
            choice_key=result.choices[0].key,
        )

        safety += 1
        print(
            "Step:",
            result.current_node,
            result.status,
            result.total_xp,
            result.total_tokens,
            result.loot,
        )

        if result.status == "completed":
            break

        if safety > 10:
            raise RuntimeError("Adventure did not finish.")

    assert result.status == "completed"
    assert get_state(guild_id).state == DragonState.IDLE

    chronicle = get_chronicle(guild_id)
    print("Chronicle entries:", len(chronicle))
    print("Completion:", completion_summary(guild_id, user_id))
    print("V5 Alpha pack test passed.")


if __name__ == "__main__":
    main()
