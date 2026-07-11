from __future__ import annotations

import random


def roll_encounter() -> str:
    roll = random.randint(1, 100)

    if roll <= 40:
        return "nothing"

    if roll <= 65:
        return "gather"

    if roll <= 80:
        return "combat"

    if roll <= 90:
        return "npc"

    if roll <= 98:
        return "treasure"

    return "rare"
