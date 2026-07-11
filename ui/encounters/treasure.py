from __future__ import annotations

import discord

from systems.chronicle.service import add_chronicle_entry
from systems.items.service import add_item
from systems.travel.catalog import LOCATIONS
from systems.treasure.service import (
    TreasureReward,
    roll_treasure,
)
from ui.encounters.models import EncounterContext
from ui.panel_manager import refresh_main_panel_in_place


class TreasureView(discord.ui.View):
    def __init__(self, reward: TreasureReward):
        super().__init__(timeout=300)
        self.reward = reward
        self.opened = False

    @discord.ui.button(
        label="Open Chest",
        emoji="🗝️",
        style=discord.ButtonStyle.success,
        custom_id="v5_treasure_open",
    )
    async def open_chest(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self.opened:
            await interaction.response.send_message(
                "This chest was already opened.",
                ephemeral=True,
                delete_after=30,
            )
            return

        self.opened = True
        button.disabled = True

        inventory_item = add_item(
            interaction.guild_id,
            self.reward.item_key,
            self.reward.quantity,
        )

        location = LOCATIONS.get(
            self.reward.location_key,
            LOCATIONS["guild_hall"],
        )

        add_chronicle_entry(
            interaction.guild_id,
            entry_type="treasure",
            title=f"Found {self.reward.definition.name}",
            description=(
                f"The dragon opened an old chest at "
                f"{location.name} and discovered "
                f"{self.reward.quantity} "
                f"{self.reward.definition.name}."
            ),
            importance=(
                3
                if self.reward.definition.rarity
                in {"rare", "epic", "legendary", "mythic"}
                else 1
            ),
            metadata={
                "location_key": self.reward.location_key,
                "item_key": self.reward.item_key,
                "quantity": self.reward.quantity,
            },
        )

        embed = discord.Embed(
            title="🎁 Treasure Collected",
            description=(
                f"The chest contained:\n\n"
                f"**{self.reward.quantity}× "
                f"{self.reward.definition.display_name}**\n"
                f"{self.reward.definition.rarity_icon} "
                f"{self.reward.definition.rarity.title()}\n\n"
                f"*{self.reward.definition.description}*\n\n"
                f"**Inventory total:** {inventory_item.quantity}"
            ),
            color=discord.Color.gold(),
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self,
        )

        await refresh_main_panel_in_place(
            interaction.guild,
        )


def build_treasure_encounter(
    context: EncounterContext,
    embed: discord.Embed,
) -> tuple[discord.Embed, discord.ui.View]:
    reward = roll_treasure(context.location_key)

    embed.add_field(
        name="🎁 Hidden Treasure",
        value=(
            "The dragon discovered an old chest hidden "
            "beneath leaves and twisted roots.\n\n"
            "Open it to discover what is inside."
        ),
        inline=False,
    )

    return embed, TreasureView(reward)
