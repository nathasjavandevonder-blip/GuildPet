from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class DragonLocation:

    guild_id: int

    location_key: str

    travelling: bool

    destination_key: str | None

    arrival_time: datetime | None
