from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EnemyDefinition:
    key: str
    name: str
    emoji: str
    max_hp: int
    attack_min: int
    attack_max: int
    armor: int
    fire_weakness: float
    xp_reward: int
    token_reward: int
    loot_table: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class CombatResult:
    combat_id: int
    enemy_key: str
    enemy_name: str
    enemy_emoji: str
    description: str
    dragon_hp: int
    dragon_max_hp: int
    enemy_hp: int
    enemy_max_hp: int
    status: str
    turn_number: int
    xp_reward: int = 0
    token_reward: int = 0
    loot: tuple[str, ...] = ()
    unlocked_achievements: tuple[str, ...] = ()
