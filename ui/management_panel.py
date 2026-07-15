from __future__ import annotations

import discord

from systems.onboarding.service import (
    EGGS,
    advance_lifecycle_time,
    finalize_vote,
    force_select_egg,
    force_stage,
    get_ai_channels,
    get_lifecycle,
    get_setup,
    reset_guildpet_journey,
    vote_counts,
)
from ui.egg_view import EggCareView, EggVoteView, build_egg_embed

OWNER_ID = 176308213489205249


def _channel(guild: discord.Guild, value: int | None) -> str:
    if not value:
        return "Not configured"
    channel = guild.get_channel(int(value))
    return channel.mention if channel else f"Deleted channel ({value})"


def build_management_embed(guild: discord.Guild) -> discord.Embed:
    setup = get_setup(guild.id)
    lifecycle = get_lifecycle(guild.id)
    embed = discord.Embed(
        title="🐉 GuildPet Management",
        description="Manage this server's single GuildPet journey.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Current stage", value=lifecycle.stage.replace("_", " ").title(), inline=True)
    egg = EGGS.get(lifecycle.selected_egg or "")
    embed.add_field(name="Chosen egg", value=egg[0] if egg else "Not chosen", inline=True)
    if setup:
        embed.add_field(name="Dragon channel", value=_channel(guild, setup["dragon_channel_id"]), inline=False)
        embed.add_field(name="Welcome channel", value=_channel(guild, setup["welcome_channel_id"]), inline=False)
        ai_channels = [_channel(guild, channel_id) for channel_id in get_ai_channels(guild.id)]
        embed.add_field(name="Dragon chat", value=f"{setup['ai_activity'].title()}\n" + (", ".join(ai_channels) or "No channels"), inline=False)
    if lifecycle.stage == "egg_vote":
        counts = vote_counts(guild.id)
        embed.add_field(name="Votes cast", value=str(sum(counts.values())), inline=True)
    embed.set_footer(text="GuildPet Ultimate • Raise a Dragon. Build a Legacy.")
    return embed


class EggSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Developer: choose an egg",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=data[0], value=key, description=data[2][:100], emoji="🥚") for key, data in EGGS.items()],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("Developer access required.", ephemeral=True)
            return
        force_select_egg(interaction.guild_id, self.values[0])
        await interaction.response.edit_message(embed=build_developer_embed(interaction.guild), view=DeveloperPanel())


class StageSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Egg Vote", value="egg_vote", emoji="🗳️"),
            discord.SelectOption(label="Incubating", value="incubating", emoji="🥚"),
            discord.SelectOption(label="Hatchling", value="hatchling", emoji="🐣"),
            discord.SelectOption(label="Young", value="young", emoji="🐲"),
            discord.SelectOption(label="Adult", value="adult", emoji="🐉"),
            discord.SelectOption(label="Ancient", value="ancient", emoji="👑"),
            discord.SelectOption(label="Elder", value="elder", emoji="✨"),
        ]
        super().__init__(placeholder="Developer: set lifecycle stage", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("Developer access required.", ephemeral=True)
            return
        force_stage(interaction.guild_id, self.values[0])
        await interaction.response.edit_message(embed=build_developer_embed(interaction.guild), view=DeveloperPanel())


def build_developer_embed(guild: discord.Guild) -> discord.Embed:
    lifecycle = get_lifecycle(guild.id)
    egg = EGGS.get(lifecycle.selected_egg or "")
    embed = discord.Embed(
        title="👑 GuildPet Developer Panel",
        description="Owner-only testing controls. Changes affect only this server.",
        color=discord.Color.dark_gold(),
    )
    embed.add_field(name="Stage", value=lifecycle.stage.replace("_", " ").title(), inline=True)
    embed.add_field(name="Egg", value=egg[0] if egg else "None", inline=True)
    embed.add_field(name="Owner", value=f"<@{OWNER_ID}>", inline=False)
    embed.set_footer(text="Developer tools • Use Reset carefully")
    return embed


class DeveloperPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(StageSelect())
        self.add_item(EggSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == OWNER_ID:
            return True
        await interaction.response.send_message("Only the GuildPet owner can use these controls.", ephemeral=True)
        return False

    @discord.ui.button(label="End Vote Now", emoji="🏁", style=discord.ButtonStyle.primary, row=2)
    async def end_vote(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        try:
            finalize_vote(interaction.guild_id, force=True)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_developer_embed(interaction.guild), view=DeveloperPanel())

    @discord.ui.button(label="Hatch Now", emoji="🐣", style=discord.ButtonStyle.success, row=2)
    async def hatch_now(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        force_stage(interaction.guild_id, "hatchling")
        await interaction.response.edit_message(embed=build_developer_embed(interaction.guild), view=DeveloperPanel())

    @discord.ui.button(label="+1 Day", emoji="⏩", style=discord.ButtonStyle.secondary, row=2)
    async def day(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        advance_lifecycle_time(interaction.guild_id, hours=24)
        await interaction.response.edit_message(embed=build_developer_embed(interaction.guild), view=DeveloperPanel())

    @discord.ui.button(label="+7 Days", emoji="⏩", style=discord.ButtonStyle.secondary, row=2)
    async def week(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        advance_lifecycle_time(interaction.guild_id, hours=168)
        await interaction.response.edit_message(embed=build_developer_embed(interaction.guild), view=DeveloperPanel())

    @discord.ui.button(label="Reset Journey", emoji="♻️", style=discord.ButtonStyle.danger, row=3)
    async def reset(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        reset_guildpet_journey(interaction.guild_id)
        await interaction.response.edit_message(embed=build_developer_embed(interaction.guild), view=DeveloperPanel())


class ManagementPanel(discord.ui.View):
    def __init__(self, *, show_developer: bool):
        super().__init__(timeout=180)
        self.show_developer = show_developer
        if not show_developer:
            self.remove_item(self.developer)

    @discord.ui.button(label="Current Journey", emoji="🐉", style=discord.ButtonStyle.primary)
    async def journey(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        lifecycle = get_lifecycle(interaction.guild_id)
        view: discord.ui.View | None = None
        if lifecycle.stage == "egg_vote":
            view = EggVoteView(interaction.guild_id)
        elif lifecycle.stage == "incubating":
            view = EggCareView(interaction.guild_id)
        await interaction.response.send_message(embed=build_egg_embed(interaction.guild_id), view=view, ephemeral=True)

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(embed=build_management_embed(interaction.guild), view=ManagementPanel(show_developer=interaction.user.id == OWNER_ID))

    @discord.ui.button(label="Developer", emoji="👑", style=discord.ButtonStyle.danger)
    async def developer(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("Developer access required.", ephemeral=True)
            return
        await interaction.response.send_message(embed=build_developer_embed(interaction.guild), view=DeveloperPanel(), ephemeral=True)
