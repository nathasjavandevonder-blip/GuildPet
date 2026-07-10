from pathlib import Path

path = Path("ui/views/combat_view.py")
text = path.read_text(encoding="utf-8")

if "import asyncio" not in text:
    text = text.replace(
        "from __future__ import annotations\n\n",
        "from __future__ import annotations\n\nimport asyncio\n\n",
        1,
    )

import_marker = "import discord\n"

manager_import = """import discord

from ui.panel_manager import move_main_panel_to_bottom
"""

if (
    "from ui.panel_manager import move_main_panel_to_bottom"
    not in text
):
    text = text.replace(
        import_marker,
        manager_import,
        1,
    )

helper_marker = "\ndef health_bar("

helper_code = '''
async def delete_message_later(
    message: discord.Message,
    seconds: int,
) -> None:
    try:
        await asyncio.sleep(seconds)
        await message.delete()
    except (
        discord.NotFound,
        discord.Forbidden,
        discord.HTTPException,
    ):
        pass


'''

if "async def delete_message_later(" not in text:
    text = text.replace(
        helper_marker,
        "\n" + helper_code + "def health_bar(",
        1,
    )

old = '''        await interaction.response.edit_message(
            embed=build_finished_combat_embed(result),
            view=FinishedCombatView(),
        )

        if result.status == "victory":
            await interaction.followup.send(
                embed=build_reward_embed(result),
                delete_after=300,
            )
'''

new = '''        await interaction.response.edit_message(
            embed=build_finished_combat_embed(result),
            view=FinishedCombatView(),
        )

        if result.status == "victory":
            await interaction.followup.send(
                embed=build_reward_embed(result),
                delete_after=300,
            )

        # Keep the finished combat visible for 10 minutes.
        asyncio.create_task(
            delete_message_later(
                interaction.message,
                600,
            )
        )

        # The permanent GuildPet panel is recreated last,
        # so it remains the bottom-most visible message.
        await move_main_panel_to_bottom(
            interaction.guild,
            interaction.channel,
        )
'''

if old not in text:
    raise SystemExit(
        "Could not locate finished combat response block."
    )

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Updated ui/views/combat_view.py")
