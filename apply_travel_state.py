from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")

    if old not in text:
        raise RuntimeError(f"Required block not found in {path}")

    file.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"Updated {path}")


# ---------------------------------------------------------
# 1. Add TRAVELLING to DragonState
# ---------------------------------------------------------

replace_once(
    "systems/state/models.py",
    '''    COMBAT = "combat"
    RECOVERING = "recovering"
''',
    '''    COMBAT = "combat"
    TRAVELLING = "travelling"
    RECOVERING = "recovering"
''',
)


# ---------------------------------------------------------
# 2. Add valid state transitions
# ---------------------------------------------------------

replace_once(
    "systems/state/service.py",
    '''        DragonState.COMBAT,
        DragonState.CELEBRATING,
''',
    '''        DragonState.COMBAT,
        DragonState.TRAVELLING,
        DragonState.CELEBRATING,
''',
)

replace_once(
    "systems/state/service.py",
    '''    DragonState.COMBAT: {
        DragonState.ADVENTURE,
        DragonState.IDLE,
        DragonState.RECOVERING,
        DragonState.CELEBRATING,
    },
''',
    '''    DragonState.COMBAT: {
        DragonState.ADVENTURE,
        DragonState.IDLE,
        DragonState.RECOVERING,
        DragonState.CELEBRATING,
    },
    DragonState.TRAVELLING: {
        DragonState.IDLE,
        DragonState.COMBAT,
        DragonState.RECOVERING,
    },
''',
)


# ---------------------------------------------------------
# 3. Travel service controls the DragonState
# ---------------------------------------------------------

path = Path("systems/travel/service.py")
text = path.read_text(encoding="utf-8")

if "from systems.state.models import DragonState" not in text:
    text = text.replace(
        "from systems.travel.catalog import LOCATIONS\n",
        "from systems.travel.catalog import LOCATIONS\n"
        "from systems.state.models import DragonState\n"
        "from systems.state.service import reset_to_idle, set_state\n",
        1,
    )

old = '''    return True


def finish_travel(guild_id: int):
'''

new = '''    set_state(
        guild_id,
        DragonState.TRAVELLING,
        duration=timedelta(minutes=minutes),
        payload={
            "from_location": current,
            "destination": destination,
            "arrival_time": arrival.isoformat(),
        },
        force=True,
    )

    return True


def finish_travel(guild_id: int):
'''

if old not in text:
    raise RuntimeError("start_travel return block not found")

text = text.replace(old, new, 1)

old = '''    return True
'''

# Replace the final return only.
position = text.rfind(old)

if position == -1:
    raise RuntimeError("finish_travel return block not found")

text = (
    text[:position]
    + '''    reset_to_idle(
        guild_id,
        reason="travel_finished",
    )

    return True
'''
    + text[position + len(old):]
)

path.write_text(text, encoding="utf-8")
print("Updated systems/travel/service.py")


# ---------------------------------------------------------
# 4. Add travelling view routing
# ---------------------------------------------------------

replace_once(
    "ui/view_manager.py",
    '''    if state_record.state == DragonState.RECOVERING:
''',
    '''    if state_record.state == DragonState.TRAVELLING:
        from ui.views.travel_view import TravelStateView

        return TravelStateView(guild_id)

    if state_record.state == DragonState.RECOVERING:
''',
)


# ---------------------------------------------------------
# 5. Add Travel button to IdleView
# ---------------------------------------------------------

path = Path("ui/views/idle_view.py")
text = path.read_text(encoding="utf-8")

marker = '''    @discord.ui.button(
        label="Rest",
'''

travel_button = '''    @discord.ui.button(
        label="Travel",
        emoji="🗺️",
        style=discord.ButtonStyle.primary,
        custom_id="v5_idle_travel",
    )
    async def travel(self, interaction, button):
        from ui.views.travel_view import (
            TravelView,
            build_travel_embed,
        )

        await interaction.response.send_message(
            embed=build_travel_embed(interaction.guild_id),
            view=TravelView(interaction.guild_id),
            ephemeral=True,
        )

'''

if "custom_id=\"v5_idle_travel\"" not in text:
    if marker not in text:
        raise RuntimeError("Rest button marker not found in idle_view.py")

    text = text.replace(marker, travel_button + marker, 1)

path.write_text(text, encoding="utf-8")
print("Updated ui/views/idle_view.py")


# ---------------------------------------------------------
# 6. Upgrade travel view
# ---------------------------------------------------------

path = Path("ui/views/travel_view.py")
text = path.read_text(encoding="utf-8")

if "from ui.panel_manager import refresh_main_panel_in_place" not in text:
    text = text.replace(
        "from systems.travel.service import (\n",
        "from ui.panel_manager import refresh_main_panel_in_place\n"
        "from systems.travel.service import (\n",
        1,
    )

old = '''        await interaction.response.edit_message(
            embed=build_travel_embed(interaction.guild_id),
            view=TravelView(interaction.guild_id),
        )
'''

new = '''        await interaction.response.edit_message(
            embed=build_travel_embed(interaction.guild_id),
            view=TravelView(interaction.guild_id),
        )

        await refresh_main_panel_in_place(
            interaction.guild,
        )
'''

# Only replace the select callback occurrence.
if old not in text:
    raise RuntimeError("Travel selection callback block not found")

text = text.replace(old, new, 1)

append_code = '''


class TravelStateView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(
        label="Refresh Travel",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
        custom_id="v5_travel_state_refresh",
    )
    async def refresh_travel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        arrived = finish_travel(interaction.guild_id)

        if arrived:
            from ui.view_manager import build_view
            from ui.main_panel import build_main_embed

            await interaction.response.edit_message(
                embed=build_main_embed(interaction.guild_id),
                view=build_view(interaction.guild_id),
            )
            return

        await interaction.response.send_message(
            embed=build_travel_embed(interaction.guild_id),
            ephemeral=True,
        )
'''

if "class TravelStateView" not in text:
    text += append_code

path.write_text(text, encoding="utf-8")
print("Updated ui/views/travel_view.py")


# ---------------------------------------------------------
# 7. Main-panel state label
# ---------------------------------------------------------

path = Path("ui/main_panel.py")
text = path.read_text(encoding="utf-8")

if 'DragonState.TRAVELLING: "Travelling",' not in text:
    text = text.replace(
        '    DragonState.COMBAT: "In Combat",\n',
        '    DragonState.COMBAT: "In Combat",\n'
        '    DragonState.TRAVELLING: "Travelling",\n',
        1,
    )

path.write_text(text, encoding="utf-8")
print("Updated ui/main_panel.py")

print("Travel state integration applied.")
