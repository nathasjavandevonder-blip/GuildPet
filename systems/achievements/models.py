from __future__ import annotations

from dataclasses import dataclass


RARITY_ICONS = {
    "common": "⚪",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟠",
    "mythic": "🔴",
}


@dataclass(frozen=True, slots=True)
class AchievementDefinition:
    key: str
    name: str
    description: str
    category: str
    rarity: str
    metric: str
    target: int
    hidden: bool = False

    @property
    def icon(self) -> str:
        return RARITY_ICONS.get(self.rarity, "⚪")


@dataclass(frozen=True, slots=True)
class AchievementProgress:
    definition: AchievementDefinition
    current: int
    unlocked: bool

    @property
    def remaining(self) -> int:
        return max(self.definition.target - self.current, 0)

    @property
    def percentage(self) -> int:
        if self.definition.target <= 0:
            return 100

        return min(
            int((self.current / self.definition.target) * 100),
            100,
        )
