from pathlib import Path

FILES = {
    "migrations/v5_007_world_engine.py": r'''
from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS guild_world_state_v5 (
                guild_id INTEGER PRIMARY KEY,
                location_key TEXT NOT NULL DEFAULT 'guild_hall',
                weather_key TEXT NOT NULL DEFAULT 'clear',
                time_period TEXT NOT NULL DEFAULT 'morning',
                season_key TEXT NOT NULL DEFAULT 'summer',
                weather_changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                world_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS guild_world_events_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                event_key TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location_key TEXT,
                weather_key TEXT,
                importance INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS dragon_location_history_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                from_location TEXT,
                to_location TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_world_events_guild
            ON guild_world_events_v5 (guild_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_location_history_guild
            ON dragon_location_history_v5 (guild_id, created_at DESC);
            """
        )
''',

    "data/world/locations.json": r'''
[
  {
    "key": "guild_hall",
    "name": "Guild Hall",
    "emoji": "🏰",
    "description": "The safe home of the guild dragon.",
    "danger": 0,
    "available_times": ["morning", "afternoon", "evening", "night"],
    "weather": ["clear", "cloudy", "rain", "storm", "fog", "snow"]
  },
  {
    "key": "whispering_forest",
    "name": "Whispering Forest",
    "emoji": "🌲",
    "description": "An ancient forest filled with hidden paths.",
    "danger": 2,
    "available_times": ["morning", "afternoon", "evening", "night"],
    "weather": ["clear", "cloudy", "rain", "storm", "fog", "snow"]
  },
  {
    "key": "crystal_caverns",
    "name": "Crystal Caverns",
    "emoji": "💎",
    "description": "Glittering tunnels beneath the mountains.",
    "danger": 3,
    "available_times": ["morning", "afternoon", "evening", "night"],
    "weather": ["clear"]
  },
  {
    "key": "mountain_pass",
    "name": "Mountain Pass",
    "emoji": "⛰️",
    "description": "A steep route leading into dangerous heights.",
    "danger": 4,
    "available_times": ["morning", "afternoon", "evening"],
    "weather": ["clear", "cloudy", "rain", "storm", "fog", "snow"]
  },
  {
    "key": "ancient_ruins",
    "name": "Ancient Ruins",
    "emoji": "🏛️",
    "description": "Forgotten stones hiding old secrets.",
    "danger": 4,
    "available_times": ["morning", "afternoon", "evening", "night"],
    "weather": ["clear", "cloudy", "rain", "fog"]
  },
  {
    "key": "frozen_peaks",
    "name": "Frozen Peaks",
    "emoji": "❄️",
    "description": "A cold and unforgiving mountain region.",
    "danger": 5,
    "available_times": ["morning", "afternoon"],
    "weather": ["cloudy", "storm", "fog", "snow"]
  }
]
''',

    "data/world/weather.json": r'''
[
  {
    "key": "clear",
    "name": "Clear",
    "emoji": "☀️",
    "mood_modifier": 2,
    "adventure_modifier": 1.0
  },
  {
    "key": "cloudy",
    "name": "Cloudy",
    "emoji": "☁️",
    "mood_modifier": 0,
    "adventure_modifier": 1.0
  },
  {
    "key": "rain",
    "name": "Rain",
    "emoji": "🌧️",
    "mood_modifier": -1,
    "adventure_modifier": 0.95
  },
  {
    "key": "storm",
    "name": "Storm",
    "emoji": "⛈️",
    "mood_modifier": -3,
    "adventure_modifier": 0.8
  },
  {
    "key": "fog",
    "name": "Fog",
    "emoji": "🌫️",
    "mood_modifier": -1,
    "adventure_modifier": 0.9
  },
  {
    "key": "snow",
    "name": "Snow",
    "emoji": "❄️",
    "mood_modifier": 1,
    "adventure_modifier": 0.85
  }
]
''',

    "systems/world/__init__.py": "",

    "systems/world/models.py": r'''
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LocationDefinition:
    key: str
    name: str
    emoji: str
    description: str
    danger: int
    available_times: tuple[str, ...]
    weather: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WeatherDefinition:
    key: str
    name: str
    emoji: str
    mood_modifier: int
    adventure_modifier: float


@dataclass(frozen=True, slots=True)
class WorldState:
    guild_id: int
    location_key: str
    weather_key: str
    time_period: str
    season_key: str
''',

    "systems/world/catalog.py": r'''
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
''',

    "systems/world/service.py": r'''
from __future__ import annotations

import random
from datetime import UTC, datetime

from core.database import db_session
from systems.chronicle.service import add_chronicle_entry
from systems.world.catalog import (
    get_location,
    get_weather,
    load_weather,
)
from systems.world.models import WorldState


TIME_PERIODS = (
    "morning",
    "afternoon",
    "evening",
    "night",
)


def current_time_period(
    now: datetime | None = None,
) -> str:
    moment = now or datetime.now(UTC)
    hour = moment.hour

    if 5 <= hour < 12:
        return "morning"

    if 12 <= hour < 18:
        return "afternoon"

    if 18 <= hour < 23:
        return "evening"

    return "night"


def current_season(
    now: datetime | None = None,
) -> str:
    moment = now or datetime.now(UTC)
    month = moment.month

    if month in (12, 1, 2):
        return "winter"

    if month in (3, 4, 5):
        return "spring"

    if month in (6, 7, 8):
        return "summer"

    return "autumn"


def ensure_world_state(guild_id: int) -> WorldState:
    with db_session() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO guild_world_state_v5 (
                guild_id,
                time_period,
                season_key
            )
            VALUES (?, ?, ?)
            """,
            (
                guild_id,
                current_time_period(),
                current_season(),
            ),
        )

    return get_world_state(guild_id)


def get_world_state(guild_id: int) -> WorldState:
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM guild_world_state_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

    if row is None:
        return ensure_world_state(guild_id)

    return WorldState(
        guild_id=int(row["guild_id"]),
        location_key=str(row["location_key"]),
        weather_key=str(row["weather_key"]),
        time_period=str(row["time_period"]),
        season_key=str(row["season_key"]),
    )


def set_location(
    guild_id: int,
    location_key: str,
    *,
    reason: str | None = None,
) -> WorldState:
    current = ensure_world_state(guild_id)
    location = get_location(location_key)

    with db_session() as connection:
        connection.execute(
            """
            UPDATE guild_world_state_v5
            SET location_key = ?,
                world_updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                location.key,
                guild_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO dragon_location_history_v5 (
                guild_id,
                from_location,
                to_location,
                reason
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                guild_id,
                current.location_key,
                location.key,
                reason,
            ),
        )

    return get_world_state(guild_id)


def choose_new_weather(guild_id: int) -> WorldState:
    current = ensure_world_state(guild_id)
    location = get_location(current.location_key)

    possible = list(location.weather) or list(load_weather())

    if current.weather_key in possible and len(possible) > 1:
        possible.remove(current.weather_key)

    weather_key = random.choice(possible)

    with db_session() as connection:
        connection.execute(
            """
            UPDATE guild_world_state_v5
            SET weather_key = ?,
                weather_changed_at = CURRENT_TIMESTAMP,
                world_updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                weather_key,
                guild_id,
            ),
        )

    weather = get_weather(weather_key)

    add_world_event(
        guild_id,
        event_key="weather_change",
        title=f"{weather.emoji} Weather changed",
        description=f"The weather is now {weather.name.lower()}.",
        weather_key=weather.key,
    )

    return get_world_state(guild_id)


def update_world_clock(guild_id: int) -> WorldState:
    time_period = current_time_period()
    season = current_season()

    with db_session() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO guild_world_state_v5 (
                guild_id,
                time_period,
                season_key
            )
            VALUES (?, ?, ?)
            """,
            (
                guild_id,
                time_period,
                season,
            ),
        )

        connection.execute(
            """
            UPDATE guild_world_state_v5
            SET time_period = ?,
                season_key = ?,
                world_updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                time_period,
                season,
                guild_id,
            ),
        )

    return get_world_state(guild_id)


def world_tick(guild_id: int) -> WorldState:
    state = update_world_clock(guild_id)

    if random.random() < 0.20:
        state = choose_new_weather(guild_id)

    return state


def add_world_event(
    guild_id: int,
    *,
    event_key: str,
    title: str,
    description: str,
    location_key: str | None = None,
    weather_key: str | None = None,
    importance: int = 1,
) -> int:
    with db_session() as connection:
        cursor = connection.execute(
            """
            INSERT INTO guild_world_events_v5 (
                guild_id,
                event_key,
                title,
                description,
                location_key,
                weather_key,
                importance
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                event_key,
                title,
                description,
                location_key,
                weather_key,
                importance,
            ),
        )

        event_id = int(cursor.lastrowid)

    if importance >= 2:
        add_chronicle_entry(
            guild_id,
            entry_type="world_event",
            title=title,
            description=description,
            importance=importance,
            metadata={
                "world_event_id": event_id,
                "location_key": location_key,
                "weather_key": weather_key,
            },
        )

    return event_id


def get_recent_world_events(
    guild_id: int,
    *,
    limit: int = 10,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM guild_world_events_v5
            WHERE guild_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                guild_id,
                limit,
            ),
        ).fetchall()
''',

    "systems/world/dialogue.py": r'''
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
''',

    "tests/test_v5_world_engine.py": r'''
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
''',
}

for filename, content in FILES.items():
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")
    print(f"Created {filename}")

print(f"\nCreated {len(FILES)} world-engine files.")
