from datetime import UTC, datetime

from systems.world.catalog import (
    get_location,
    get_weather,
    load_locations,
)
from systems.world.dialogue import world_dialogue
from systems.world.service import (
    current_season,
    current_time_period,
    ensure_world_state,
    set_location,
    update_world_clock,
)


def main() -> None:
    guild_id = 990008

    assert current_time_period(
        datetime(2026, 7, 10, 7, tzinfo=UTC)
    ) == "morning"

    assert current_time_period(
        datetime(2026, 7, 10, 21, tzinfo=UTC)
    ) == "evening"

    assert current_season(
        datetime(2026, 7, 10, tzinfo=UTC)
    ) == "summer"

    state = ensure_world_state(guild_id)
    print("Initial world:", state)

    state = set_location(
        guild_id,
        "whispering_forest",
        reason="test journey",
    )

    assert state.location_key == "whispering_forest"
    assert get_location(state.location_key).name == "Whispering Forest"
    assert get_weather(state.weather_key).name
    assert len(load_locations()) >= 5

    updated = update_world_clock(guild_id)
    print("Updated world:", updated)
    print("Dialogue:\n", world_dialogue(guild_id))
    print("V5 world engine test passed.")


if __name__ == "__main__":
    main()
