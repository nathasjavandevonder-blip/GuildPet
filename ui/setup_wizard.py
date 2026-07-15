from __future__ import annotations

import discord

from systems.onboarding.service import get_setup, save_setup, set_ai_channels, start_egg_vote
from ui.panel_manager import move_main_panel_to_bottom


class DragonChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Choose the main dragon channel", channel_types=[discord.ChannelType.text], min_values=1, max_values=1, custom_id="v55_setup_dragon_channel")

    async def callback(self, interaction: discord.Interaction) -> None:
        save_setup(interaction.guild_id, dragon_channel_id=self.values[0].id)
        await interaction.response.send_message(f"Main dragon channel set to {self.values[0].mention}.", ephemeral=True, delete_after=20)


class WelcomeChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Choose the welcome channel", channel_types=[discord.ChannelType.text], min_values=1, max_values=1, custom_id="v55_setup_welcome_channel")

    async def callback(self, interaction: discord.Interaction) -> None:
        save_setup(interaction.guild_id, welcome_channel_id=self.values[0].id)
        await interaction.response.send_message(f"Welcome channel set to {self.values[0].mention}.", ephemeral=True, delete_after=20)


class AIChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="Choose channels where the dragon may speak", channel_types=[discord.ChannelType.text], min_values=1, max_values=10, custom_id="v55_setup_ai_channels")

    async def callback(self, interaction: discord.Interaction) -> None:
        set_ai_channels(interaction.guild_id, [channel.id for channel in self.values])
        await interaction.response.send_message("Dragon AI channels saved.", ephemeral=True, delete_after=20)


class ActivitySelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Choose dragon chat activity",
            custom_id="v55_setup_ai_activity",
            options=[
                discord.SelectOption(label="Off", value="off", description="No dragon chat"),
                discord.SelectOption(label="Silent", value="silent", description="Only event messages and welcomes"),
                discord.SelectOption(label="Rare", value="rare", description="Very occasional replies"),
                discord.SelectOption(label="Normal", value="normal", description="Balanced activity", default=True),
                discord.SelectOption(label="Talkative", value="talkative", description="More frequent, still rate-limited"),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        limits = {"off": 0, "silent": 1, "rare": 2, "normal": 4, "talkative": 8}
        value = self.values[0]
        save_setup(interaction.guild_id, ai_activity=value, ai_max_per_hour=limits[value])
        await interaction.response.send_message(f"Dragon chat activity set to **{value.title()}**.", ephemeral=True, delete_after=20)


class SetupWizardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=900)
        self.add_item(DragonChannelSelect())
        self.add_item(WelcomeChannelSelect())
        self.add_item(AIChannelSelect())
        self.add_item(ActivitySelect())

    @discord.ui.button(label="Finish Setup & Start Egg Vote", emoji="🥚", style=discord.ButtonStyle.success, row=4)
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        setup = get_setup(interaction.guild_id)
        if setup is None or not setup["dragon_channel_id"]:
            await interaction.response.send_message("Choose the main dragon channel first.", ephemeral=True, delete_after=30)
            return
        save_setup(interaction.guild_id, setup_complete=1)
        try:
            start_egg_vote(interaction.guild_id)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True, delete_after=30)
            return
        channel = interaction.guild.get_channel(int(setup["dragon_channel_id"]))
        if channel is None:
            await interaction.response.send_message("I can no longer access the selected dragon channel.", ephemeral=True, delete_after=30)
            return
        await interaction.response.defer(ephemeral=True)
        await move_main_panel_to_bottom(interaction.guild, channel)
        await interaction.followup.send("Setup complete. The server has one active GuildPet setup and the guild egg vote is now live.", ephemeral=True)
