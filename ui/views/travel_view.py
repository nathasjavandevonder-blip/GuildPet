from __future__ import annotations

from datetime import UTC, datetime

import discord

from systems.travel.catalog import LOCATIONS
from ui.panel_manager import refresh_main_panel_in_place
from systems.travel.service import (
    finish_travel,
    get_location,
    start_travel,
)


def _remaining_text(arrival_time: str | None) -> str:
    if not arrival_time:
        return "Unknown"

    arrival = datetime.fromisoformat(arrival_time)

    if arrival.tzinfo is None:
        arrival = arrival.replace(tzinfo=UTC)

    remaining = max(
        0,
        int((arrival - datetime.now(UTC)).total_seconds()),
    )

    minutes, seconds = divmod(remaining, 60)

    if minutes:
        return f"{minutes}m {seconds}s"

    return f"{seconds}s"


def build_travel_embed(guild_id: int) -> discord.Embed:
    finish_travel(guild_id)
    state = get_location(guild_id)

    current = LOCATIONS.get(
        state["location_key"],
        LOCATIONS["guild_hall"],
    )

    if state["travelling"]:
        destination = LOCATIONS[state["destination_key"]]

        return discord.Embed(
            title="🗺️ Dragon Travel",
            description=(
                f"🐉 The dragon is travelling from "
                f"**{current.emoji} {current.name}** to "
                f"**{destination.emoji} {destination.name}**.\n\n"
                f"⏳ **Arrival:** "
                f"{_remaining_text(state['arrival_time'])}"
            ),
            color=discord.Color.orange(),
        )

    embed = discord.Embed(
        title="🗺️ Choose a Destination",
        description=(
            f"**Current location:** "
            f"{current.emoji} **{current.name}**\n"
            f"{current.description}"
        ),
        color=discord.Color.blurple(),
    )

    embed.set_footer(
        text="Travel time depends on the destination."
    )

    return embed


class TravelSelect(discord.ui.Select):
    def __init__(self, guild_id: int):
        state = get_location(guild_id)
        current_key = state["location_key"]

        options = [
            discord.SelectOption(
                label=location.name,
                value=location.key,
                emoji=location.emoji,
                description=(
                    f"{location.travel_minutes} min — "
                    f"{location.description}"
                )[:100],
            )
            for location in LOCATIONS.values()
            if location.key != current_key
        ]

        super().__init__(
            placeholder="Choose where the dragon should travel",
            options=options[:25],
            custom_id="v5_travel_destination",
            disabled=bool(state["travelling"]),
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ) -> None:
        destination = self.values[0]

        try:
            started = start_travel(
                interaction.guild_id,
                destination,
            )
        except KeyError:
            await interaction.response.send_message(
                "That destination does not exist.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if not started:
            await interaction.response.send_message(
                "The dragon is already there or is unable to travel.",
                ephemeral=True,
                delete_after=30,
            )
            return

        await interaction.response.edit_message(
            embed=build_travel_embed(interaction.guild_id),
            view=TravelView(interaction.guild_id),
        )

        await refresh_main_panel_in_place(
            interaction.guild,
        )


class TravelView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.add_item(TravelSelect(guild_id))

    @discord.ui.button(
        label="Refresh",
        emoji="🔄",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_travel_refresh",
    )
    async def refresh(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_travel_embed(interaction.guild_id),
            view=TravelView(interaction.guild_id),
        )



class TravelStateView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(
        label="Refresh Travel",
        emoji="🔄",
        style=discord.ButtonStyle.primary,
        custom_id="v5_travel_state_refresh",
    )
    async def refresh_travel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        arrived = finish_travel(interaction.guild_id)

        if arrived:
            from ui.view_manager import build_view
            from ui.main_panel import build_main_embed

            await interaction.response.edit_message(
                embed=build_main_embed(interaction.guild_id),
                view=build_view(interaction.guild_id),
            )
            return

        await interaction.response.send_message(
            embed=build_travel_embed(interaction.guild_id),
            ephemeral=True,
        )
