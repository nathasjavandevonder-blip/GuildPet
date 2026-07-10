from pathlib import Path

path = Path("ui/main_panel.py")
text = path.read_text(encoding="utf-8")

if "from systems.world.catalog import" not in text:
    text = text.replace(
        "from systems.state.service import resolve_expired_state\n",
        "from systems.state.service import resolve_expired_state\n"
        "from systems.world.catalog import get_location, get_weather\n"
        "from systems.world.service import ensure_world_state\n",
        1,
    )

old = """    living = get_living_state(guild_id)
    state = resolve_expired_state(guild_id)
"""

new = """    living = get_living_state(guild_id)
    state = resolve_expired_state(guild_id)
    world = ensure_world_state(guild_id)
    location = get_location(world.location_key)
    weather = get_weather(world.weather_key)
"""

if old not in text:
    raise SystemExit("Main panel state block not found.")

text = text.replace(old, new, 1)

marker = """    embed.add_field(
        name="🍖 Hunger",
"""

world_fields = """    embed.add_field(
        name="🌍 World",
        value=(
            f"{location.emoji} **{location.name}**\\n"
            f"{weather.emoji} {weather.name}\\n"
            f"🕒 {world.time_period.title()}\\n"
            f"🍂 {world.season_key.title()}"
        ),
        inline=False,
    )

"""

if world_fields not in text:
    text = text.replace(marker, world_fields + marker, 1)

path.write_text(text, encoding="utf-8")
print("Updated ui/main_panel.py")
