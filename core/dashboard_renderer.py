from __future__ import annotations

import discord

from core.dragon_status import DragonStatus
from core.i18n import DEFAULT_LOCALE


STAGE_COLORS = {
    "unconfigured": discord.Color.dark_grey(),
    "egg_vote": discord.Color.gold(),
    "incubating": discord.Color.gold(),
    "hatchling": discord.Color.green(),
    "young": discord.Color.blue(),
    "adult": discord.Color.purple(),
    "ancient": discord.Color.orange(),
    "elder": discord.Color.red(),
    "legacy": discord.Color.dark_gold(),
}


def progress_bar(value: int, *, blocks: int = 10) -> str:
    value = max(0, min(100, int(value)))
    filled = round(value / 100 * blocks)
    return f"{'█' * filled}{'░' * (blocks - filled)} {value}%"


class DashboardRenderer:
    def __init__(
        self,
        status: DragonStatus,
        locale: str = DEFAULT_LOCALE,
    ) -> None:
        self.status = status
        self.locale = locale

    def build(self) -> discord.Embed:
        status = self.status
        embed = discord.Embed(
            title="🐉 GuildPet Ultimate",
            description=(
                "*Raise a Dragon. Build a Legacy.*\n\n"
                f"## {status.name}\n"
                f"**{status.stage_label}** • Level {status.level}\n"
                f"*{status.title}*"
            ),
            color=STAGE_COLORS.get(status.stage, discord.Color.blurple()),
        )

        embed.add_field(
            name="💬 Today's Thought",
            value=f'“{status.thought}”',
            inline=False,
        )

        embed.add_field(
            name="❤️ Bond",
            value=progress_bar(status.bond),
            inline=True,
        )
        embed.add_field(
            name="🍖 Hunger",
            value=progress_bar(status.hunger),
            inline=True,
        )
        embed.add_field(
            name="⚡ Energy",
            value=progress_bar(status.energy),
            inline=True,
        )
        embed.add_field(
            name="😊 Happiness",
            value=progress_bar(status.happiness),
            inline=True,
        )
        embed.add_field(
            name="🛁 Cleanliness",
            value=progress_bar(status.cleanliness),
            inline=True,
        )
        embed.add_field(
            name="⭐ Growth",
            value=progress_bar(status.growth),
            inline=True,
        )

        embed.add_field(
            name="🐲 Dragon Status",
            value=(
                f"**Mood:** {status.mood.title()}\n"
                f"**State:** {status.state_label}\n"
                f"**Activity:** {status.activity.title()}\n"
                f"**Personality:** {status.personality}"
            ),
            inline=True,
        )
        embed.add_field(
            name="🌍 World",
            value=(
                f"{status.location_emoji} **{status.location_name}**\n"
                f"{status.weather_emoji} {status.weather_name}\n"
                f"🕒 {status.time_period.title()}\n"
                f"🍂 {status.season.title()}"
            ),
            inline=True,
        )

        if status.stage == "egg_vote":
            journey = "The guild is choosing which Ancient Egg to protect."
        elif status.stage == "incubating":
            egg = (status.selected_egg or "ancient").replace("_", " ").title()
            journey = f"The **{egg} Egg** is being cared for by the guild."
        elif status.stage == "hatchling":
            journey = "Combat and travel remain locked while the hatchling grows."
        else:
            journey = "New actions unlock naturally as the dragon grows."

        embed.add_field(name="🔓 Journey", value=journey, inline=False)

        activities = status.recent_activity or (
            "The dragon is waiting for the guild's first new memory.",
        )
        embed.add_field(
            name="📖 Latest Memories",
            value="\n".join(f"• {item}" for item in activities),
            inline=False,
        )

        embed.set_footer(
            text="GuildPet Ultimate • Dashboard Foundation v5.5.3"
        )
        return embed
