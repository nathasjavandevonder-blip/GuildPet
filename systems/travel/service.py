from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.database import db_session
from systems.travel.catalog import LOCATIONS


def get_location(guild_id: int):

    with db_session() as con:

        row = con.execute(
            """
            SELECT *
            FROM dragon_location_v5
            WHERE guild_id=?
            """,
            (guild_id,),
        ).fetchone()

    if row is None:

        with db_session() as con:

            con.execute(
                """
                INSERT INTO dragon_location_v5(
                    guild_id,
                    location_key
                )
                VALUES(?,?)
                """,
                (
                    guild_id,
                    "guild_hall",
                ),
            )

        return get_location(guild_id)

    return row


def start_travel(
    guild_id: int,
    destination: str,
):

    location = get_location(guild_id)

    current = location["location_key"]

    if current == destination:
        return False

    minutes = LOCATIONS[destination].travel_minutes

    arrival = datetime.now(UTC) + timedelta(
        minutes=minutes
    )

    with db_session() as con:

        con.execute(
            """
            UPDATE dragon_location_v5
            SET travelling=1,
                destination_key=?,
                arrival_time=?,
                last_updated=CURRENT_TIMESTAMP
            WHERE guild_id=?
            """,
            (
                destination,
                arrival.isoformat(),
                guild_id,
            ),
        )

        con.execute(
            """
            INSERT INTO travel_history_v5(
                guild_id,
                from_location,
                to_location,
                started_at
            )
            VALUES(
                ?,?,?,CURRENT_TIMESTAMP
            )
            """,
            (
                guild_id,
                current,
                destination,
            ),
        )

    return True


def finish_travel(guild_id: int):

    location = get_location(guild_id)

    if not location["travelling"]:
        return False

    if location["arrival_time"]:

        arrival = datetime.fromisoformat(
            location["arrival_time"]
        )

        if arrival > datetime.now(UTC):
            return False

    with db_session() as con:

        con.execute(
            """
            UPDATE dragon_location_v5
            SET
                location_key=destination_key,
                travelling=0,
                destination_key=NULL,
                arrival_time=NULL,
                last_updated=CURRENT_TIMESTAMP
            WHERE guild_id=?
            """,
            (guild_id,),
        )

        con.execute(
            """
            UPDATE travel_history_v5
            SET arrived_at=CURRENT_TIMESTAMP
            WHERE id=(
                SELECT id
                FROM travel_history_v5
                WHERE guild_id=?
                ORDER BY id DESC
                LIMIT 1
            )
            """,
            (guild_id,),
        )

    return True
