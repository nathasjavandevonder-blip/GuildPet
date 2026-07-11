from pathlib import Path


path = Path("systems/travel/service.py")
text = path.read_text(encoding="utf-8")

if "from systems.travel.arrival import handle_arrival" not in text:
    text = text.replace(
        "from systems.travel.catalog import LOCATIONS\n",
        "from systems.travel.catalog import LOCATIONS\n"
        "from systems.travel.arrival import handle_arrival\n",
        1,
    )

old = '''    with db_session() as con:

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
'''

new = '''    destination_key = location["destination_key"]

    if not destination_key:
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
'''

if old not in text:
    raise RuntimeError("Travel update block was not found.")

text = text.replace(old, new, 1)

old = '''    reset_to_idle(
        guild_id,
        reason="travel_finished",
    )

    return True
'''

new = '''    reset_to_idle(
        guild_id,
        reason="travel_finished",
    )

    return handle_arrival(destination_key)
'''

if old not in text:
    raise RuntimeError("Travel return block was not found.")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("Updated systems/travel/service.py")
