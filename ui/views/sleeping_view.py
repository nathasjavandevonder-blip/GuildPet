from __future__ import annotations

import discord

from systems.dialogue.service import dragon_talk
from systems.living.models import CareAction
from systems.living.service import perform_care_action
from systems.state.service import wake_dragon


class SleepingView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    async def sleep_action(
        self,
        interaction: discord.Interaction,
        action: CareAction,
    ) -> None:
        result = perform_care_action(
            interaction.guild_id,
            user_id=interaction.user.id,
            username=interaction.user.display_name,
            action=action,
        )

        await interaction.response.send_message(
            result.message,
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.button(
        label="Wake Gently",
        emoji="☕",
        style=discord.ButtonStyle.success,
        custom_id="v5_sleep_wake_gently",
    )
    async def wake_gently(self, interaction, button):
        result = perform_care_action(
            interaction.guild_id,
            user_id=interaction.user.id,
            username=interaction.user.display_name,
            action=CareAction.WAKE_GENTLY,
        )

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
            result.message,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Whisper",
        emoji="🤫",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_sleep_whisper",
    )
    async def whisper(self, interaction, button):
        await self.sleep_action(
            interaction,
            CareAction.WHISPER,
        )

    @discord.ui.button(
        label="Cuddle",
        emoji="💖",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_sleep_cuddle",
    )
    async def cuddle(self, interaction, button):
        await self.sleep_action(
            interaction,
            CareAction.CUDDLE,
        )

    @discord.ui.button(
        label="Let Sleep",
        emoji="🌙",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_sleep_let_sleep",
    )
    async def let_sleep(self, interaction, button):
        await self.sleep_action(
            interaction,
            CareAction.LET_SLEEP,
        )

    @discord.ui.button(
        label="Talk",
        emoji="💬",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_sleep_talk",
    )
    async def talk(self, interaction, button):
        text = dragon_talk(
            interaction.guild_id,
            user_id=interaction.user.id,
            username=interaction.user.display_name,
        )

        await interaction.response.send_message(
            f"💤 **The sleeping dragon murmurs**\n\n{text}",
            ephemeral=True,
            delete_after=30,
        )
