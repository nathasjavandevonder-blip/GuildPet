from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from systems.world.models import (
    LocationDefinition,
    WeatherDefinition,
)

BASE_DIR = Path(__file__).resolve().parents[2]
WORLD_DIR = BASE_DIR / "data" / "world"


@lru_cache(maxsize=1)
def load_locations() -> dict[str, LocationDefinition]:
    raw = json.loads(
        (WORLD_DIR / "locations.json").read_text(encoding="utf-8")
    )

    return {
        item["key"]: LocationDefinition(
            key=item["key"],
            name=item["name"],
            emoji=item.get("emoji", "📍"),
            description=item["description"],
            danger=int(item.get("danger", 0)),
            available_times=tuple(item.get("available_times", [])),
            weather=tuple(item.get("weather", [])),
        )
        for item in raw
    }


@lru_cache(maxsize=1)
def load_weather() -> dict[str, WeatherDefinition]:
    raw = json.loads(
        (WORLD_DIR / "weather.json").read_text(encoding="utf-8")
    )

    return {
        item["key"]: WeatherDefinition(
            key=item["key"],
            name=item["name"],
            emoji=item.get("emoji", "🌤️"),
            mood_modifier=int(item.get("mood_modifier", 0)),
            adventure_modifier=float(
                item.get("adventure_modifier", 1.0)
            ),
        )
        for item in raw
    }


def get_location(key: str) -> LocationDefinition:
    location = load_locations().get(key)

    if location is None:
        raise KeyError(f"Unknown location: {key}")

    return location


def get_weather(key: str) -> WeatherDefinition:
    weather = load_weather().get(key)

    if weather is None:
        raise KeyError(f"Unknown weather: {key}")

    return weather
