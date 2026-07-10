from pathlib import Path

path = Path("bot_v5.py")
text = path.read_text(encoding="utf-8")

import_marker = "from ui.view_manager import build_view\n"

new_imports = """from ui.view_manager import build_view
from ui.main_panel import build_main_embed
from ui.panel_manager import (
    move_main_panel_to_bottom,
    refresh_main_panel_in_place,
    restore_registered_panels,
)
"""

if import_marker in text:
    text = text.replace(
        import_marker,
        new_imports,
        1,
    )
elif "from ui.panel_manager import" not in text:
    raise SystemExit("Could not locate ui.view_manager import.")

start = text.find("def build_main_embed(guild_id: int)")
end = text.find("\n\nclass AdventureSelect", start)

if start != -1 and end != -1:
    text = text[:start] + text[end + 2:]

setup_old = """        await self.tree.sync()
        print(f"Synced {len(self.tree.get_commands())} application commands.")
"""

setup_new = """        await restore_registered_panels(self)
        await self.tree.sync()
        print(f"Synced {len(self.tree.get_commands())} application commands.")
"""

if setup_old in text:
    text = text.replace(
        setup_old,
        setup_new,
        1,
    )
elif "await restore_registered_panels(self)" not in text:
    raise SystemExit("Could not locate setup_hook sync block.")

panel_start = text.find(
    "@bot.tree.command(\n"
    '    name="v5panel",'
)
panel_end = text.find(
    "\n\n@bot.tree.command(\n"
    '    name="v5refresh",',
    panel_start,
)

if panel_start == -1 or panel_end == -1:
    raise SystemExit("Could not locate /v5panel command.")

new_panel_command = '''@bot.tree.command(
    name="v5panel",
    description="Post or move the GuildPet v5 panel to the bottom.",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def v5panel(interaction: discord.Interaction) -> None:
    ensure_state(interaction.guild_id)

    await interaction.response.defer(
        ephemeral=True,
    )

    await move_main_panel_to_bottom(
        interaction.guild,
        interaction.channel,
    )

    await interaction.followup.send(
        "🐉 The GuildPet panel was moved to the bottom.",
        ephemeral=True,
    )
'''

text = (
    text[:panel_start]
    + new_panel_command
    + text[panel_end:]
)

refresh_start = text.find(
    "@bot.tree.command(\n"
    '    name="v5refresh",'
)
refresh_end = text.find(
    "\n\n@bot.tree.command(\n"
    '    name="v5adventure",',
    refresh_start,
)

if refresh_start == -1 or refresh_end == -1:
    raise SystemExit("Could not locate /v5refresh command.")

new_refresh_command = '''@bot.tree.command(
    name="v5refresh",
    description="Refresh the current GuildPet v5 main panel.",
)
async def v5refresh(interaction: discord.Interaction) -> None:
    await interaction.response.defer(
        ephemeral=True,
    )

    message = await refresh_main_panel_in_place(
        interaction.guild,
    )

    if message is None:
        await move_main_panel_to_bottom(
            interaction.guild,
            interaction.channel,
        )
        response = "🐉 A new GuildPet panel was created."
    else:
        response = "🐉 The GuildPet panel was refreshed."

    await interaction.followup.send(
        response,
        ephemeral=True,
    )
'''

text = (
    text[:refresh_start]
    + new_refresh_command
    + text[refresh_end:]
)

path.write_text(text, encoding="utf-8")
print("Updated bot_v5.py")
