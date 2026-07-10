from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from systems.combat.models import EnemyDefinition

BASE_DIR = Path(__file__).resolve().parents[2]
ENEMY_DIR = BASE_DIR / "data" / "enemies"


@lru_cache(maxsize=1)
def load_enemies() -> dict[str, EnemyDefinition]:
    enemies: dict[str, EnemyDefinition] = {}

    for path in sorted(ENEMY_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))

        enemy = EnemyDefinition(
            key=raw["key"],
            name=raw["name"],
            emoji=raw.get("emoji", "👾"),
            max_hp=int(raw["max_hp"]),
            attack_min=int(raw["attack_min"]),
            attack_max=int(raw["attack_max"]),
            armor=int(raw.get("armor", 0)),
            fire_weakness=float(raw.get("fire_weakness", 1.0)),
            xp_reward=int(raw.get("xp_reward", 0)),
            token_reward=int(raw.get("token_reward", 0)),
            loot_table=tuple(raw.get("loot_table", [])),
        )
        enemies[enemy.key] = enemy

    return enemies


def get_enemy(key: str) -> EnemyDefinition:
    enemy = load_enemies().get(key)

    if enemy is None:
        raise KeyError(f"Unknown enemy: {key}")

    return enemy
