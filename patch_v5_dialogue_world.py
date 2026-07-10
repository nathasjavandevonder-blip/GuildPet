from pathlib import Path

path = Path("systems/dialogue/service.py")
text = path.read_text(encoding="utf-8")

if "from systems.world.dialogue import world_dialogue" not in text:
    text = text.replace(
        "from systems.relationships.service import (\n",
        "from systems.world.dialogue import world_dialogue\n"
        "from systems.relationships.service import (\n",
        1,
    )

old = """    return "\\n".join(lines)
"""

new = """    lines.extend([
        "",
        world_dialogue(guild_id),
    ])

    return "\\n".join(lines)
"""

if old not in text:
    raise SystemExit("Dialogue return block not found.")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Updated systems/dialogue/service.py")
