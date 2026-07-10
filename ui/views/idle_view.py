from __future__ import annotations

import discord

from systems.state.service import start_sleep


class IdleView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(
        label="Feed",
        emoji="🍖",
        style=discord.ButtonStyle.success,
        custom_id="v5_idle_feed",
    )
    async def feed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            "🍖 Feeding will be connected to the v5 care system.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.button(
        label="Play",
        emoji="🎮",
        style=discord.ButtonStyle.primary,
        custom_id="v5_idle_play",
    )
    async def play(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            "🎮 Playing will be connected to the v5 care system.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.button(
        label="Rest",
        emoji="😴",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_idle_rest",
    )
    async def rest(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        start_sleep(interaction.guild_id)

        from ui.view_manager import build_view

        await interaction.response.edit_message(
            view=build_view(interaction.guild_id),
        )
