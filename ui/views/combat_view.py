from __future__ import annotations

import discord

from systems.combat.catalog import get_enemy
from systems.combat.service import (
    CombatFinished,
    CombatNotFound,
    get_active_combat,
    perform_action,
)
from ui.view_manager import build_view


def health_bar(current: int, maximum: int, size: int = 10) -> str:
    if maximum <= 0:
        return "░" * size

    filled = round((current / maximum) * size)
    filled = max(0, min(size, filled))

    return "█" * filled + "░" * (size - filled)


def build_combat_embed(
    guild_id: int,
    description: str | None = None,
) -> discord.Embed:
    combat = get_active_combat(guild_id)

    if combat is None:
        return discord.Embed(
            title="⚔️ Combat Ended",
            description=description or "There is no active combat.",
        )

    enemy = get_enemy(combat["enemy_key"])

    embed = discord.Embed(
        title=f"⚔️ {enemy.emoji} {enemy.name}",
        description=description or "Choose the dragon's next action.",
        color=discord.Color.red(),
    )

    embed.add_field(
        name="🐉 Dragon HP",
        value=(
            f"`{health_bar(combat['dragon_hp'], combat['dragon_max_hp'])}`\n"
            f"**{combat['dragon_hp']} / {combat['dragon_max_hp']}**"
        ),
        inline=True,
    )

    embed.add_field(
        name=f"{enemy.emoji} Enemy HP",
        value=(
            f"`{health_bar(combat['enemy_hp'], combat['enemy_max_hp'])}`\n"
            f"**{combat['enemy_hp']} / {combat['enemy_max_hp']}**"
        ),
        inline=True,
    )

    embed.set_footer(
        text=f"Turn {combat['turn_number']}"
    )

    return embed


class CombatStateView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    async def process_action(
        self,
        interaction: discord.Interaction,
        action_key: str,
    ) -> None:
        try:
            result = perform_action(
                interaction.guild_id,
                user_id=interaction.user.id,
                username=interaction.user.display_name,
                action_key=action_key,
            )
        except CombatNotFound:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="⚔️ Combat Ended",
                    description="This combat is no longer active.",
                ),
                view=build_view(interaction.guild_id),
            )
            return
        except CombatFinished:
            await interaction.response.send_message(
                "This combat has already finished.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if result.status == "active":
            await interaction.response.edit_message(
                embed=build_combat_embed(
                    interaction.guild_id,
                    result.description,
                ),
                view=CombatStateView(interaction.guild_id),
            )
            return

        embed = discord.Embed(
            title=(
                "🏆 Victory!"
                if result.status == "victory"
                else "⚔️ Combat Ended"
            ),
            description=result.description,
            color=(
                discord.Color.green()
                if result.status == "victory"
                else discord.Color.orange()
            ),
        )

        await interaction.response.edit_message(
            embed=embed,
            view=build_view(interaction.guild_id),
        )

    @discord.ui.button(
        label="Attack",
        emoji="🦴",
        style=discord.ButtonStyle.primary,
        custom_id="v5_combat_attack",
    )
    async def attack(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.process_action(interaction, "attack")

    @discord.ui.button(
        label="Fire Breath",
        emoji="🔥",
        style=discord.ButtonStyle.danger,
        custom_id="v5_combat_fire",
    )
    async def fire_breath(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.process_action(interaction, "fire_breath")

    @discord.ui.button(
        label="Guard",
        emoji="🛡️",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_combat_guard",
    )
    async def guard(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.process_action(interaction, "guard")

    @discord.ui.button(
        label="Retreat",
        emoji="🏃",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_combat_retreat",
    )
    async def retreat(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.process_action(interaction, "retreat")
