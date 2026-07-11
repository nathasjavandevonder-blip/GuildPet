from __future__ import annotations

import discord

from systems.chronicle.service import add_chronicle_entry
from systems.gathering.service import (
    GatherResult,
    roll_resource,
)
from systems.items.service import add_item
from systems.travel.catalog import LOCATIONS
from ui.encounters.models import EncounterContext
from ui.panel_manager import refresh_main_panel_in_place


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
                f"While exploring {location.name}, the dragon "
                f"collected {self.result.quantity} "
                f"{self.result.definition.name}."
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
                f"**{self.result.quantity}× "
                f"{self.result.definition.display_name}**\n\n"
                f"{self.result.definition.description}\n\n"
                f"**Inventory total:** {inventory_item.quantity}"
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


def build_gathering_encounter(
    context: EncounterContext,
    embed: discord.Embed,
) -> tuple[discord.Embed, discord.ui.View]:
    result = roll_resource(context.location_key)

    embed.add_field(
        name="🌿 Gathering Opportunity",
        value=(
            f"You discovered:\n\n"
            f"{result.definition.emoji} "
            f"**{result.definition.name}** "
            f"×{result.quantity}\n"
            f"*{result.definition.description}*"
        ),
        inline=False,
    )

    return embed, GatheringView(result)
