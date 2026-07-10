from __future__ import annotations

import discord

from systems.state.service import wake_dragon


class SleepingView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(
        label="Wake Gently",
        emoji="☕",
        style=discord.ButtonStyle.success,
        custom_id="v5_sleep_wake_gently",
    )
    async def wake_gently(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        wake_dragon(
            interaction.guild_id,
            keeper_id=interaction.user.id,
            gentle=True,
        )

        from ui.view_manager import build_view

        await interaction.response.edit_message(
            view=build_view(interaction.guild_id),
        )

        await interaction.followup.send(
            "☕ You gently woke the dragon.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Whisper",
        emoji="🤫",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_sleep_whisper",
    )
    async def whisper(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            "🤫 The dragon relaxes when it hears your voice.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.button(
        label="Cuddle",
        emoji="💖",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_sleep_cuddle",
    )
    async def cuddle(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            "💖 The dragon curls closer without waking.",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.button(
        label="Let Sleep",
        emoji="🌙",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_sleep_let_sleep",
    )
    async def let_sleep(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            "🌙 You let the dragon sleep peacefully.",
            ephemeral=True,
            delete_after=30,
        )
