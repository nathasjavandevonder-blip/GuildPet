from core.database import db_session
from systems.combat.service import (
    get_active_combat,
    get_combat,
    get_recent_actions,
    perform_action,
    start_combat,
)


def clean_test_data(guild_id: int) -> None:
    with db_session() as connection:
        combat_rows = connection.execute(
            "SELECT id FROM combat_sessions WHERE guild_id = ?",
            (guild_id,),
        ).fetchall()

        combat_ids = [int(row["id"]) for row in combat_rows]

        for combat_id in combat_ids:
            connection.execute(
                "DELETE FROM combat_rewards_v5 WHERE combat_id = ?",
                (combat_id,),
            )
            connection.execute(
                "DELETE FROM combat_actions_v5 WHERE combat_id = ?",
                (combat_id,),
            )
            connection.execute(
                "DELETE FROM combat_participants_v5 WHERE combat_id = ?",
                (combat_id,),
            )

        connection.execute(
            "DELETE FROM combat_sessions WHERE guild_id = ?",
            (guild_id,),
        )


def main() -> None:
    guild_id = 990006
    user_id = 880006

    clean_test_data(guild_id)

    combat_id = start_combat(
        guild_id,
        enemy_key="training_goblin",
    )

    result = None

    for round_number in range(1, 15):
        result = await perform_action(
            guild_id,
            user_id=user_id,
            username="Combat Tester",
            action_key="fire_breath",
        )

        print(
            "Round",
            round_number,
            result.status,
            result.dragon_hp,
            result.enemy_hp,
        )

        if result.status != "active":
            break

    assert result is not None
    assert result.status == "victory"
    assert get_active_combat(guild_id) is None
    assert get_combat(combat_id)["status"] == "victory"
    assert len(get_recent_actions(combat_id)) >= 1
    assert result.xp_reward > 0
    assert result.token_reward > 0

    print("Loot:", result.loot)
    print("Achievements:", result.unlocked_achievements)
    print("V5 Combat 2.0 test passed.")


if __name__ == "__main__":
    main()
