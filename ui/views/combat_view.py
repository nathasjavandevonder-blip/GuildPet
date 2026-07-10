from __future__ import annotations

import discord

from systems.combat.catalog import get_enemy
from systems.combat.models import CombatResult
from systems.combat.service import (
    CombatFinished,
    CombatNotFound,
    get_active_combat,
    get_combat,
    get_recent_actions,
    perform_action,
)


def health_bar(current: int, maximum: int, size: int = 10) -> str:
    if maximum <= 0:
        return "░" * size

    filled = round((current / maximum) * size)
    filled = max(0, min(size, filled))

    return "█" * filled + "░" * (size - filled)


def _battle_log(combat_id: int) -> str:
    rows = get_recent_actions(
        combat_id,
        limit=4,
    )

    if not rows:
        return "The battle has just begun."

    sections = []

    for row in rows:
        sections.append(
            f"**Round {row['turn_number']}**\n"
            f"{row['description']}"
        )

    return "\n\n".join(sections)[-1900:]


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

    embed.add_field(
        name="📜 Battle Log",
        value=_battle_log(int(combat["id"])),
        inline=False,
    )

    embed.set_footer(
        text=f"Turn {combat['turn_number']}"
    )

    return embed


def build_finished_combat_embed(
    result: CombatResult,
) -> discord.Embed:
    if result.status == "victory":
        title = "🏆 Victory!"
        color = discord.Color.green()
    elif result.status == "defeat":
        title = "💔 Defeat"
        color = discord.Color.red()
    else:
        title = "🏃 Combat Ended"
        color = discord.Color.orange()

    embed = discord.Embed(
        title=title,
        description=result.description,
        color=color,
    )

    embed.add_field(
        name="🐉 Dragon HP",
        value=(
            f"`{health_bar(result.dragon_hp, result.dragon_max_hp)}`\n"
            f"**{result.dragon_hp} / {result.dragon_max_hp}**"
        ),
        inline=True,
    )

    embed.add_field(
        name=f"{result.enemy_emoji} Enemy HP",
        value=(
            f"`{health_bar(result.enemy_hp, result.enemy_max_hp)}`\n"
            f"**{result.enemy_hp} / {result.enemy_max_hp}**"
        ),
        inline=True,
    )

    embed.add_field(
        name="📜 Final Battle Log",
        value=_battle_log(result.combat_id),
        inline=False,
    )

    embed.set_footer(
        text="Combat finished — controls disabled"
    )
    return embed


def build_reward_embed(
    result: CombatResult,
) -> discord.Embed:
    loot_text = (
        "\n".join(f"• `{item}`" for item in result.loot)
        if result.loot
        else "No item drops this time."
    )

    embed = discord.Embed(
        title="🎁 Combat Rewards",
        description=(
            f"⭐ **{result.xp_reward} Combat XP**\n"
            f"🪙 **{result.token_reward} Tokens**\n\n"
            f"**Loot**\n{loot_text}"
        ),
        color=discord.Color.gold(),
    )

    if result.unlocked_achievements:
        embed.add_field(
            name="🏆 Achievements Unlocked",
            value="\n".join(
                f"• `{key}`"
                for key in result.unlocked_achievements
            ),
            inline=False,
        )

    embed.set_footer(
        text="This reward message disappears after 5 minutes."
    )
    return embed


class FinishedCombatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        buttons = (
            ("Attack", "🦴", discord.ButtonStyle.primary),
            ("Fire Breath", "🔥", discord.ButtonStyle.danger),
            ("Guard", "🛡️", discord.ButtonStyle.secondary),
            ("Retreat", "🏃", discord.ButtonStyle.secondary),
        )

        for index, (label, emoji, style) in enumerate(buttons):
            self.add_item(
                discord.ui.Button(
                    label=label,
                    emoji=emoji,
                    style=style,
                    disabled=True,
                    custom_id=f"v5_combat_finished_{index}",
                )
            )


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
            await interaction.response.send_message(
                "This combat is no longer active.",
                ephemeral=True,
                delete_after=30,
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

        await interaction.response.edit_message(
            embed=build_finished_combat_embed(result),
            view=FinishedCombatView(),
        )

        if result.status == "victory":
            await interaction.followup.send(
                embed=build_reward_embed(result),
                delete_after=300,
            )

    @discord.ui.button(
        label="Attack",
        emoji="🦴",
        style=discord.ButtonStyle.primary,
        custom_id="v5_combat_attack",
    )
    async def attack(self, interaction, button):
        await self.process_action(interaction, "attack")

    @discord.ui.button(
        label="Fire Breath",
        emoji="🔥",
        style=discord.ButtonStyle.danger,
        custom_id="v5_combat_fire",
    )
    async def fire_breath(self, interaction, button):
        await self.process_action(interaction, "fire_breath")

    @discord.ui.button(
        label="Guard",
        emoji="🛡️",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_combat_guard",
    )
    async def guard(self, interaction, button):
        await self.process_action(interaction, "guard")

    @discord.ui.button(
        label="Retreat",
        emoji="🏃",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_combat_retreat",
    )
    async def retreat(self, interaction, button):
        await self.process_action(interaction, "retreat")
