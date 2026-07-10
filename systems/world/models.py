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
