from __future__ import annotations

from datetime import UTC, datetime

import asyncio
import contextlib

import discord

from systems.travel.catalog import LOCATIONS
from systems.travel.service import (
    finish_travel,
    get_location,
    start_travel,
)
from ui.encounters import EncounterContext, build_encounter
from ui.panel_manager import refresh_main_panel_in_place


ENCOUNTER_TITLES = {
    "nothing": "🌿 Peaceful Arrival",
    "gather": "🌿 Resources Discovered",
    "combat": "⚔️ Danger Nearby",
    "npc": "🧙 Someone Is Waiting",
    "treasure": "🎁 Treasure Discovered",
    "rare": "✨ Rare Discovery",
}

ENCOUNTER_TEXT = {
    "nothing": "The area appears peaceful.",
    "combat": "Something dangerous is moving nearby.",
    "npc": "A mysterious figure is waiting beside the path.",
    "treasure": "Something valuable may be hidden nearby.",
    "rare": "The air feels strange and unusually powerful.",
}



def _remaining_seconds(arrival_time: str | None) -> int:
    if not arrival_time:
        return 0

    arrival = datetime.fromisoformat(arrival_time)

    if arrival.tzinfo is None:
        arrival = arrival.replace(tzinfo=UTC)

    return max(
        0,
        int((arrival - datetime.now(UTC)).total_seconds()),
    )


def _schedule_original_delete(
    interaction: discord.Interaction,
    seconds: int,
) -> None:
    async def delete_later() -> None:
        await asyncio.sleep(max(1, seconds))

        with contextlib.suppress(
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            await interaction.delete_original_response()

    asyncio.create_task(delete_later())


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
                f"The dragon is travelling from "
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


def prepare_arrival(
    arrival: dict[str, str],
) -> tuple[discord.Embed, discord.ui.View | None]:
    location_key = arrival["location_key"]
    encounter_key = arrival.get("encounter", "nothing")
    story = arrival.get(
        "story",
        "The dragon arrived safely.",
    )

    location = LOCATIONS.get(
        location_key,
        LOCATIONS["guild_hall"],
    )

    embed = discord.Embed(
        title=f"{location.emoji} Arrived at {location.name}",
        description=story,
        color=discord.Color.green(),
    )

    context = EncounterContext(
        guild_id=0,
        location_key=location_key,
        encounter_key=encounter_key,
        story=story,
    )

    return build_encounter(context, embed)


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
                "The dragon is already there or cannot travel now.",
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

        travel_state = get_location(interaction.guild_id)
        _schedule_original_delete(
            interaction,
            _remaining_seconds(travel_state["arrival_time"]) + 300,
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
        arrival = finish_travel(interaction.guild_id)

        if isinstance(arrival, dict):
            embed, view = prepare_arrival(arrival)

            await interaction.response.edit_message(
                embed=embed,
                view=view,
            )

            await refresh_main_panel_in_place(
                interaction.guild,
            )

            _schedule_original_delete(
                interaction,
                300,
            )
            return

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
        arrival = finish_travel(interaction.guild_id)

        if isinstance(arrival, dict):
            embed, view = prepare_arrival(arrival)

            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True,
            )

            await refresh_main_panel_in_place(
                interaction.guild,
            )

            _schedule_original_delete(
                interaction,
                300,
            )
            return

        await interaction.response.send_message(
            embed=build_travel_embed(interaction.guild_id),
            ephemeral=True,
        )

        _schedule_original_delete(
            interaction,
            60,
        )
