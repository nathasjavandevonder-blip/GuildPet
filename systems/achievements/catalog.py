from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from systems.achievements.models import AchievementDefinition

BASE_DIR = Path(__file__).resolve().parents[2]
CATALOG_FILE = BASE_DIR / "data" / "achievements" / "achievements.json"


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, AchievementDefinition]:
    raw = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))

    definitions: dict[str, AchievementDefinition] = {}

    for item in raw:
        achievement = AchievementDefinition(
            key=item["key"],
            name=item["name"],
            description=item["description"],
            category=item["category"],
            rarity=item["rarity"],
            metric=item["metric"],
            target=int(item["target"]),
            hidden=bool(item.get("hidden", False)),
        )
        definitions[achievement.key] = achievement

    return definitions


def get_definition(key: str) -> AchievementDefinition | None:
    return load_catalog().get(key)
