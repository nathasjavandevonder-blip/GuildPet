from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ITEM_FILE = BASE_DIR / "data" / "items" / "items.json"

RARITY_ICONS = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟠",
    "mythic": "🔴",
}


@dataclass(frozen=True, slots=True)
class ItemDefinition:
    key: str
    name: str
    emoji: str
    rarity: str
    description: str

    @property
    def rarity_icon(self) -> str:
        return RARITY_ICONS.get(self.rarity, "⚪")

    @property
    def display_name(self) -> str:
        return f"{self.emoji} {self.name}"


@lru_cache(maxsize=1)
def load_items() -> dict[str, ItemDefinition]:
    raw = json.loads(ITEM_FILE.read_text(encoding="utf-8"))

    return {
        item["key"]: ItemDefinition(
            key=item["key"],
            name=item["name"],
            emoji=item.get("emoji", "📦"),
            rarity=item.get("rarity", "common"),
            description=item.get("description", ""),
        )
        for item in raw
    }


def get_item(item_key: str) -> ItemDefinition:
    item = load_items().get(item_key)

    if item is not None:
        return item

    readable_name = item_key.replace("_", " ").title()

    return ItemDefinition(
        key=item_key,
        name=readable_name,
        emoji="📦",
        rarity="common",
        description="An unidentified item.",
    )


def format_item(item_key: str) -> str:
    item = get_item(item_key)
    return (
        f"{item.rarity_icon} {item.display_name} "
        f"— *{item.rarity.title()}*"
    )
