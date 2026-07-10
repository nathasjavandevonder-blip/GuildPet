from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AdventureChoice:
    key: str
    label: str
    emoji: str
    next_node: str
    xp: int = 0
    tokens: int = 0
    loot: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AdventureNode:
    key: str
    text: str
    choices: tuple[AdventureChoice, ...] = ()
    complete: bool = False


@dataclass(frozen=True, slots=True)
class AdventureDefinition:
    key: str
    name: str
    emoji: str
    description: str
    start_node: str
    nodes: dict[str, AdventureNode] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AdventureResult:
    run_id: int
    adventure_name: str
    node_text: str
    status: str
    current_node: str
    total_xp: int
    total_tokens: int
    loot: tuple[str, ...]
    choices: tuple[AdventureChoice, ...]
    story_log: tuple[str, ...]
