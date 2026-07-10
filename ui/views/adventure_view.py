from __future__ import annotations

import discord

from systems.adventures.service import (
    AdventureFinished,
    AdventureNotFound,
    InvalidAdventureChoice,
    choose_adventure_path,
    get_active_adventure,
    get_adventure_result,
)


def build_adventure_embed(guild_id: int) -> discord.Embed:
    run = get_active_adventure(guild_id)

    if run is None:
        return discord.Embed(
            title="🗺️ Adventure Complete",
            description="The dragon has returned home.",
            color=discord.Color.green(),
        )

    result = get_adventure_result(int(run["id"]))

    embed = discord.Embed(
        title=f"🗺️ {result.adventure_name}",
        description=result.node_text,
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="Current rewards",
        value=(
            f"⭐ **{result.total_xp} XP**\n"
            f"🪙 **{result.total_tokens} Tokens**\n"
            f"🎒 **{len(result.loot)} Items**"
        ),
        inline=False,
    )

    embed.set_footer(text=f"Adventure run #{result.run_id}")
    return embed


class AdventureChoiceButton(discord.ui.Button):
    def __init__(self, *, choice, row: int):
        super().__init__(
            label=choice.label,
            emoji=choice.emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"v5_adventure_choice:{choice.key}",
            row=row,
        )
        self.choice_key = choice.key

    async def callback(
        self,
        interaction: discord.Interaction,
    ) -> None:
        view = self.view

        if not isinstance(view, AdventureStateView):
            return

        await view.process_choice(
            interaction,
            self.choice_key,
        )


class AdventureStateView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

        run = get_active_adventure(guild_id)

        if run is None:
            return

        result = get_adventure_result(int(run["id"]))

        for index, choice in enumerate(result.choices[:5]):
            self.add_item(
                AdventureChoiceButton(
                    choice=choice,
                    row=index // 5,
                )
            )

    async def process_choice(
        self,
        interaction: discord.Interaction,
        choice_key: str,
    ) -> None:
        try:
            result = choose_adventure_path(
                interaction.guild_id,
                user_id=interaction.user.id,
                username=interaction.user.display_name,
                choice_key=choice_key,
            )
        except (
            AdventureNotFound,
            AdventureFinished,
            InvalidAdventureChoice,
        ) as exc:
            await interaction.response.send_message(
                f"Adventure action failed: {exc}",
                ephemeral=True,
                delete_after=30,
            )
            return

        if result.status == "completed":
            loot_text = (
                ", ".join(result.loot)
                if result.loot
                else "No items"
            )

            embed = discord.Embed(
                title="🏆 Adventure Complete",
                description=(
                    f"The dragon returned from "
                    f"**{result.adventure_name}**.\n\n"
                    f"⭐ **{result.total_xp} XP**\n"
                    f"🪙 **{result.total_tokens} Tokens**\n"
                    f"🎒 **{loot_text}**\n\n"
                    "Rewards were added automatically."
                ),
                color=discord.Color.green(),
            )

            from ui.view_manager import build_view

            await interaction.response.edit_message(
                embed=embed,
                view=build_view(interaction.guild_id),
            )
            return

        await interaction.response.edit_message(
            embed=build_adventure_embed(interaction.guild_id),
            view=AdventureStateView(interaction.guild_id),
        )
