from __future__ import annotations

from datetime import UTC, datetime

import discord

from systems.chronicle.service import add_chronicle_entry
from systems.gathering.service import GatherResult, roll_resource
from systems.items.service import add_item
from systems.travel.catalog import LOCATIONS
from systems.travel.service import (
    finish_travel,
    get_location,
    start_travel,
)
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
    encounter = arrival.get("encounter", "nothing")
    location = LOCATIONS.get(
        location_key,
        LOCATIONS["guild_hall"],
    )

    embed = discord.Embed(
        title=f"{location.emoji} Arrived at {location.name}",
        description=arrival.get(
            "story",
            "The dragon arrived safely.",
        ),
        color=discord.Color.green(),
    )

    if encounter == "gather":
        result = roll_resource(location_key)

        embed.add_field(
            name="🌿 Gathering Opportunity",
            value=(
                f"You discovered:\n\n"
                f"{result.definition.emoji} "
                f"**{result.definition.name}** "
                f"×{result.quantity}"
            ),
            inline=False,
        )

        return embed, GatheringView(result)

    embed.add_field(
        name=ENCOUNTER_TITLES.get(
            encounter,
            "❓ Something Happened",
        ),
        value=ENCOUNTER_TEXT.get(
            encounter,
            "The dragon looks around curiously.",
        ),
        inline=False,
    )

    return embed, None


class GatheringView(discord.ui.View):
    def __init__(self, result: GatherResult):
        super().__init__(timeout=300)
        self.result = result
        self.claimed = False

    @discord.ui.button(
        label="Collect",
        emoji="🌿",
        style=discord.ButtonStyle.success,
        custom_id="v5_gather_collect",
    )
    async def collect(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self.claimed:
            await interaction.response.send_message(
                "These resources were already collected.",
                ephemeral=True,
                delete_after=30,
            )
            return

        self.claimed = True
        button.disabled = True

        inventory_item = add_item(
            interaction.guild_id,
            self.result.item_key,
            self.result.quantity,
        )

        location = LOCATIONS.get(
            self.result.location_key,
            LOCATIONS["guild_hall"],
        )

        add_chronicle_entry(
            interaction.guild_id,
            entry_type="gathering",
            title=f"Gathered {self.result.definition.name}",
            description=(
                f"The dragon gathered "
                f"{self.result.quantity} "
                f"{self.result.definition.name} "
                f"at {location.name}."
            ),
            importance=1,
            metadata={
                "location_key": self.result.location_key,
                "item_key": self.result.item_key,
                "quantity": self.result.quantity,
            },
        )

        embed = discord.Embed(
            title="🌿 Resources Collected",
            description=(
                f"Added **{self.result.quantity}× "
                f"{self.result.definition.display_name}** "
                f"to the guild inventory.\n\n"
                f"**New total:** {inventory_item.quantity}"
            ),
            color=discord.Color.green(),
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self,
        )

        await refresh_main_panel_in_place(
            interaction.guild,
        )


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
                delete_after=300,
            )

            await refresh_main_panel_in_place(
                interaction.guild,
            )
            return

        await interaction.response.send_message(
            embed=build_travel_embed(interaction.guild_id),
            ephemeral=True,
            delete_after=60,
        )
