from systems.dialogue.service import dragon_talk
from systems.living.models import CareAction
from systems.living.personality import (
    dominant_personality,
    get_personality,
)
from systems.living.service import (
    apply_passive_decay,
    get_living_state,
    perform_care_action,
)
from systems.relationships.service import (
    relationship_title,
    top_relationships,
)


def main() -> None:
    guild_id = 889002
    user_id = 778002
    username = "Test Keeper"

    print("Initial:", get_living_state(guild_id))

    for action in (
        CareAction.FEED,
        CareAction.PLAY,
        CareAction.TRAIN,
        CareAction.CLEAN,
        CareAction.BOND,
        CareAction.CUDDLE,
        CareAction.WAKE_GENTLY,
    ):
        result = perform_care_action(
            guild_id,
            user_id=user_id,
            username=username,
            action=action,
        )

        print(
            action.value,
            result.living_state.mood.value,
            result.relationship_bond,
            result.unlocked_achievements,
        )

    decayed = apply_passive_decay(
        guild_id,
        steps=3,
    )
    print("After decay:", decayed)

    print(
        "Personality:",
        get_personality(guild_id),
    )
    print(
        "Dominant:",
        dominant_personality(guild_id),
    )
    print(
        "Relationship title:",
        relationship_title(guild_id, user_id),
    )
    print(
        "Top relationships:",
        [
            (row["username"], row["bond"])
            for row in top_relationships(guild_id)
        ],
    )
    print(
        "Dialogue:\n",
        dragon_talk(
            guild_id,
            user_id=user_id,
            username=username,
        ),
    )

    assert get_living_state(guild_id).guild_id == guild_id
    assert relationship_title(guild_id, user_id) != "New Keeper"

    print("V5 living dragon test passed.")


if __name__ == "__main__":
    main()
