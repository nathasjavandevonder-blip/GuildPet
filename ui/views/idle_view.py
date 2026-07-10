from __future__ import annotations

import discord

from systems.dialogue.service import dragon_talk
from systems.living.models import CareAction
from systems.living.service import perform_care_action
from systems.state.service import start_sleep


class IdleView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    async def care(
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

        state = result.living_state

        text = (
            f"{result.message}\n\n"
            f"🍖 Hunger: **{state.hunger}/100**\n"
            f"😊 Happiness: **{state.happiness}/100**\n"
            f"⚡ Energy: **{state.energy}/100**\n"
            f"🛁 Cleanliness: **{state.cleanliness}/100**\n"
            f"❤️ Guild Bond: **{state.bond}/100**\n"
            f"🎭 Mood: **{state.mood.value.title()}**"
        )

        if result.unlocked_achievements:
            text += (
                "\n\n🏆 Achievement unlocked: "
                + ", ".join(result.unlocked_achievements)
            )

        await interaction.response.send_message(
            text,
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.button(
        label="Feed",
        emoji="🍖",
        style=discord.ButtonStyle.success,
        custom_id="v5_idle_feed",
    )
    async def feed(self, interaction, button):
        await self.care(interaction, CareAction.FEED)

    @discord.ui.button(
        label="Play",
        emoji="🎮",
        style=discord.ButtonStyle.primary,
        custom_id="v5_idle_play",
    )
    async def play(self, interaction, button):
        await self.care(interaction, CareAction.PLAY)

    @discord.ui.button(
        label="Train",
        emoji="🏋️",
        style=discord.ButtonStyle.primary,
        custom_id="v5_idle_train",
    )
    async def train(self, interaction, button):
        await self.care(interaction, CareAction.TRAIN)

    @discord.ui.button(
        label="Clean",
        emoji="🛁",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_idle_clean",
    )
    async def clean(self, interaction, button):
        await self.care(interaction, CareAction.CLEAN)

    @discord.ui.button(
        label="Bond",
        emoji="❤️",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_idle_bond",
    )
    async def bond(self, interaction, button):
        await self.care(interaction, CareAction.BOND)

    @discord.ui.button(
        label="Talk",
        emoji="💬",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_idle_talk",
    )
    async def talk(self, interaction, button):
        text = dragon_talk(
            interaction.guild_id,
            user_id=interaction.user.id,
            username=interaction.user.display_name,
        )

        await interaction.response.send_message(
            f"🐉 **The dragon speaks**\n\n{text}",
            ephemeral=True,
            delete_after=30,
        )

    @discord.ui.button(
        label="Rest",
        emoji="😴",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_idle_rest",
    )
    async def rest(self, interaction, button):
        start_sleep(interaction.guild_id)

        from ui.view_manager import build_view

        await interaction.response.edit_message(
            view=build_view(interaction.guild_id),
        )
