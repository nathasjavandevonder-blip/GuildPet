from systems.achievements.service import (
    add_progress,
    completion_summary,
    get_progress,
    set_showcase,
)
from systems.combat.service import (
    get_active_combat,
    perform_action,
    start_combat,
)


def main() -> None:
    guild_id = 888001
    user_id = 777001

    unlocked = add_progress(
        guild_id,
        user_id,
        "feeds",
        25,
    )

    print("Unlocked:", unlocked)

    progress = get_progress(
        guild_id,
        user_id,
    )
    print("Achievements:", len(progress))
    print(
        "Completion:",
        completion_summary(guild_id, user_id),
    )

    assert set_showcase(
        guild_id,
        user_id,
        "dragon_chef_25",
    )

    combat_id = start_combat(
        guild_id,
        enemy_key="training_goblin",
    )
    print("Combat ID:", combat_id)

    rounds = 0

    while get_active_combat(guild_id) is not None:
        result = perform_action(
            guild_id,
            user_id=user_id,
            username="Test Keeper",
            action_key="fire_breath",
        )
        rounds += 1

        print(
            f"Round {rounds}:",
            result.status,
            result.dragon_hp,
            result.enemy_hp,
        )

        if result.status != "active":
            break

        if rounds > 20:
            raise RuntimeError("Combat test did not finish.")

    print("V5 gameplay test passed.")


if __name__ == "__main__":
    main()
