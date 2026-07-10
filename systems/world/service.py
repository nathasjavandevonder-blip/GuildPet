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
