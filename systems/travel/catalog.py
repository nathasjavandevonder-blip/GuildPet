from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Location:

    key: str

    name: str

    emoji: str

    travel_minutes: int

    description: str


LOCATIONS = {

    "guild_hall": Location(
        "guild_hall",
        "Guild Hall",
        "🏰",
        0,
        "Home of your dragon.",
    ),

    "forest": Location(
        "forest",
        "Forest",
        "🌲",
        5,
        "A peaceful forest full of wildlife.",
    ),

    "river": Location(
        "river",
        "River",
        "🌊",
        8,
        "Fresh water and fish.",
    ),

    "mine": Location(
        "mine",
        "Old Mine",
        "⛏",
        12,
        "A dangerous abandoned mine.",
    ),

    "volcano": Location(
        "volcano",
        "Volcano",
        "🌋",
        20,
        "Extremely dangerous.",
    ),

    "snow_peaks": Location(
        "snow_peaks",
        "Snow Peaks",
        "❄️",
        18,
        "Frozen mountains.",
    ),
}
