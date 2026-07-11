from pathlib import Path

path = Path("systems/travel/arrival.py")
text = path.read_text(encoding="utf-8")

if "SAFE_LOCATIONS" not in text:
    insert = '''

SAFE_LOCATIONS = {
    "guild_hall",
}

'''
    marker = "AMBIENT_TABLES = {"
    text = text.replace(marker, insert + marker, 1)

old = '''    return {
        "location_key": location_key,
        "story": choice(ambient_lines),
        "encounter": roll_encounter(),
    }
'''

new = '''    encounter = (
        "nothing"
        if location_key in SAFE_LOCATIONS
        else roll_encounter()
    )

    return {
        "location_key": location_key,
        "story": choice(ambient_lines),
        "encounter": encounter,
    }
'''

if old not in text:
    raise RuntimeError("Arrival return block not found.")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("Safe locations added.")
