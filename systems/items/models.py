from __future__ import annotations

from dataclasses import dataclass

from systems.items.catalog import ItemDefinition


@dataclass(frozen=True, slots=True)
class InventoryItem:
    guild_id: int
    item_key: str
    quantity: int
    definition: ItemDefinition

    @property
    def display_name(self) -> str:
        return self.definition.display_name

    @property
    def rarity(self) -> str:
        return self.definition.rarity
