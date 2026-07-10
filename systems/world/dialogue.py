from __future__ import annotations

import random

from systems.world.catalog import get_location, get_weather
from systems.world.service import get_world_state


TIME_LINES = {
    "morning": (
        "The day feels full of possibilities.",
        "I wonder what the morning will bring.",
    ),
    "afternoon": (
        "The guild hall is busy today.",
        "There is still plenty of time to explore.",
    ),
    "evening": (
        "The light outside is starting to fade.",
        "Evenings in the lair feel peaceful.",
    ),
    "night": (
        "The world sounds different at night.",
        "I wonder what hides beneath the moonlight.",
    ),
}


WEATHER_LINES = {
    "clear": (
        "The sky is clear. I want to stretch my wings.",
        "Perfect weather for exploring.",
    ),
    "cloudy": (
        "The clouds make the world feel quiet.",
        "I keep watching the sky.",
    ),
    "rain": (
        "I can hear the rain against the lair.",
        "The forest smells different after rain.",
    ),
    "storm": (
        "That thunder was louder than I expected.",
        "I will stay close to the guild during the storm.",
    ),
    "fog": (
        "The fog makes everything look mysterious.",
        "I can barely see beyond the guild hall.",
    ),
    "snow": (
        "Snow keeps landing on my nose.",
        "The whole world looks different in white.",
    ),
}


def world_dialogue(guild_id: int) -> str:
    state = get_world_state(guild_id)
    location = get_location(state.location_key)
    weather = get_weather(state.weather_key)

    time_line = random.choice(
        TIME_LINES.get(
            state.time_period,
            TIME_LINES["afternoon"],
        )
    )

    weather_line = random.choice(
        WEATHER_LINES.get(
            state.weather_key,
            WEATHER_LINES["clear"],
        )
    )

    return (
        f"**Location:** {location.emoji} {location.name}\n"
        f"**Weather:** {weather.emoji} {weather.name}\n"
        f"**Time:** {state.time_period.title()}\n\n"
        f"{time_line}\n{weather_line}"
    )
