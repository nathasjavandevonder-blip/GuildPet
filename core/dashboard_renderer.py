from __future__ import annotations

import discord

from core.dragon_status import DragonStatus
from core.i18n import DEFAULT_LOCALE, tr


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

    def text(self, key: str, **kwargs: object) -> str:
        return tr(self.locale, key, **kwargs)

    def build(self) -> discord.Embed:
        status = self.status

        embed = discord.Embed(
            title=self.text("dashboard.title"),
            description=(
                f"*{self.text('dashboard.subtitle')}*\n\n"
                f"## {status.name}\n"
                f"**{status.stage_label}** • "
                f"{self.text('dashboard.level')} {status.level}\n"
                f"*{status.title}*"
            ),
            color=STAGE_COLORS.get(
                status.stage,
                discord.Color.blurple(),
            ),
        )

        embed.add_field(
            name=self.text("dashboard.today_thought"),
            value=f'“{status.thought}”',
            inline=False,
        )

        embed.add_field(
            name=f"❤️ {self.text('stat.bond')}",
            value=progress_bar(status.bond),
            inline=True,
        )
        embed.add_field(
            name=f"🍖 {self.text('stat.hunger')}",
            value=progress_bar(status.hunger),
            inline=True,
        )
        embed.add_field(
            name=f"⚡ {self.text('stat.energy')}",
            value=progress_bar(status.energy),
            inline=True,
        )
        embed.add_field(
            name=f"😊 {self.text('stat.happiness')}",
            value=progress_bar(status.happiness),
            inline=True,
        )
        embed.add_field(
            name=f"🛁 {self.text('stat.cleanliness')}",
            value=progress_bar(status.cleanliness),
            inline=True,
        )
        embed.add_field(
            name=f"⭐ {self.text('stat.growth')}",
            value=progress_bar(status.growth),
            inline=True,
        )

        embed.add_field(
            name=self.text("dashboard.dragon_status"),
            value=(
                f"**{self.text('stat.mood')}:** "
                f"{status.mood.title()}\n"
                f"**{self.text('stat.state')}:** "
                f"{status.state_label}\n"
                f"**{self.text('stat.activity')}:** "
                f"{status.activity.title()}\n"
                f"**{self.text('stat.personality')}:** "
                f"{status.personality}"
            ),
            inline=True,
        )

        embed.add_field(
            name=self.text("dashboard.world"),
            value=(
                f"{status.location_emoji} "
                f"**{status.location_name}**\n"
                f"{status.weather_emoji} "
                f"{status.weather_name}\n"
                f"🕒 {status.time_period.title()}\n"
                f"🍂 {status.season.title()}"
            ),
            inline=True,
        )

        if status.stage == "egg_vote":
            journey = self.text("dashboard.journey_egg_vote")
        elif status.stage == "incubating":
            egg = (
                status.selected_egg or "ancient"
            ).replace("_", " ").title()
            journey = self.text(
                "dashboard.journey_incubating",
                egg=egg,
            )
        elif status.stage == "hatchling":
            journey = self.text("dashboard.journey_hatchling")
        else:
            journey = self.text("dashboard.journey_growing")

        embed.add_field(
            name=self.text("dashboard.journey"),
            value=journey,
            inline=False,
        )

        activities = status.recent_activity or (
            self.text("dashboard.waiting_memory"),
        )

        embed.add_field(
            name=self.text("dashboard.latest_memories"),
            value="\n".join(
                f"• {item}" for item in activities
            ),
            inline=False,
        )

        embed.set_footer(
            text=self.text("dashboard.footer"),
        )

        return embed
