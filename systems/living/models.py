from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DragonMood(StrEnum):
    HAPPY = "happy"
    EXCITED = "excited"
    CONTENT = "content"
    HUNGRY = "hungry"
    SLEEPY = "sleepy"
    LONELY = "lonely"
    DIRTY = "dirty"
    GRUMPY = "grumpy"


class CareAction(StrEnum):
    FEED = "feed"
    PLAY = "play"
    TRAIN = "train"
    CLEAN = "clean"
    BOND = "bond"
    WHISPER = "whisper"
    CUDDLE = "cuddle"
    LET_SLEEP = "let_sleep"
    WAKE_GENTLY = "wake_gently"


@dataclass(frozen=True, slots=True)
class LivingState:
    guild_id: int
    hunger: int
    happiness: int
    energy: int
    cleanliness: int
    bond: int
    mood: DragonMood
    current_activity: str


@dataclass(frozen=True, slots=True)
class CareResult:
    action: CareAction
    message: str
    living_state: LivingState
    unlocked_achievements: tuple[str, ...]
    relationship_bond: int
