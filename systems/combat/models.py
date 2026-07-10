from __future__ import annotations

from dataclasses import dataclass


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


@dataclass(frozen=True, slots=True)
class CombatResult:
    combat_id: int
    description: str
    dragon_hp: int
    dragon_max_hp: int
    enemy_hp: int
    enemy_max_hp: int
    status: str
    turn_number: int
