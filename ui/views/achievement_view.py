from __future__ import annotations

import discord

from systems.achievements.service import (
    completion_summary,
    get_progress,
    get_showcase,
    set_showcase,
)


def progress_bar(current: int, target: int, size: int = 10) -> str:
    if target <= 0:
        return "█" * size

    filled = round(min(current / target, 1) * size)
    return "█" * filled + "░" * (size - filled)


def build_achievement_embed(
    guild_id: int,
    user_id: int,
    display_name: str,
) -> discord.Embed:
    progress = get_progress(guild_id, user_id)
    completed, total, percentage = completion_summary(
        guild_id,
        user_id,
    )
    showcase = get_showcase(guild_id, user_id)

    embed = discord.Embed(
        title=f"🏆 {display_name}'s Achievement Hall",
        description=(
            f"**Completion:** {completed}/{total} ({percentage}%)\n"
            f"**Showcase:** "
            f"{showcase.icon + ' ' + showcase.name if showcase else 'None selected'}"
        ),
        color=discord.Color.gold(),
    )

    visible = [
        entry
        for entry in progress
        if not entry.definition.hidden or entry.unlocked
    ]

    for entry in visible[:15]:
        status = "✅" if entry.unlocked else "⬜"
        definition = entry.definition

        embed.add_field(
            name=(
                f"{status} {definition.icon} "
                f"{definition.name}"
            ),
            value=(
                f"`{progress_bar(entry.current, definition.target)}` "
                f"{entry.current}/{definition.target}\n"
                f"{definition.description}"
            ),
            inline=False,
        )

    return embed


class ShowcaseSelect(discord.ui.Select):
    def __init__(self, guild_id: int, user_id: int):
        unlocked = [
            entry
            for entry in get_progress(guild_id, user_id)
            if entry.unlocked
        ]

        options = [
            discord.SelectOption(
                label=entry.definition.name[:100],
                value=entry.definition.key,
                emoji=entry.definition.icon,
                description=entry.definition.rarity.title(),
            )
            for entry in unlocked[:25]
        ]

        if not options:
            options = [
                discord.SelectOption(
                    label="No achievements unlocked",
                    value="none",
                    emoji="🔒",
                )
            ]

        super().__init__(
            placeholder="Choose one showcase achievement",
            options=options,
            custom_id="v5_achievement_showcase_select",
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ) -> None:
        achievement_key = self.values[0]

        if achievement_key == "none":
            await interaction.response.send_message(
                "You have not unlocked an achievement yet.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if not set_showcase(
            interaction.guild_id,
            interaction.user.id,
            achievement_key,
        ):
            await interaction.response.send_message(
                "That achievement cannot be selected.",
                ephemeral=True,
                delete_after=30,
            )
            return

        await interaction.response.edit_message(
            embed=build_achievement_embed(
                interaction.guild_id,
                interaction.user.id,
                interaction.user.display_name,
            ),
            view=AchievementHallView(
                interaction.guild_id,
                interaction.user.id,
            ),
        )


class AchievementHallView(discord.ui.View):
    def __init__(self, guild_id: int, user_id: int):
        super().__init__(timeout=300)
        self.add_item(ShowcaseSelect(guild_id, user_id))
