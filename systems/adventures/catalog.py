from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from systems.adventures.models import (
    AdventureChoice,
    AdventureDefinition,
    AdventureNode,
)

BASE_DIR = Path(__file__).resolve().parents[2]
ADVENTURE_DIR = BASE_DIR / "data" / "adventures"


@lru_cache(maxsize=1)
def load_adventures() -> dict[str, AdventureDefinition]:
    adventures: dict[str, AdventureDefinition] = {}

    for path in sorted(ADVENTURE_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        nodes: dict[str, AdventureNode] = {}

        for node_key, node_data in raw["nodes"].items():
            choices = tuple(
                AdventureChoice(
                    key=choice["key"],
                    label=choice["label"],
                    emoji=choice.get("emoji", "➡️"),
                    next_node=choice["next_node"],
                    xp=int(choice.get("xp", 0)),
                    tokens=int(choice.get("tokens", 0)),
                    loot=tuple(choice.get("loot", [])),
                )
                for choice in node_data.get("choices", [])
            )

            nodes[node_key] = AdventureNode(
                key=node_key,
                text=node_data["text"],
                choices=choices,
                complete=bool(node_data.get("complete", False)),
            )

        adventure = AdventureDefinition(
            key=raw["key"],
            name=raw["name"],
            emoji=raw.get("emoji", "🗺️"),
            description=raw["description"],
            start_node=raw["start_node"],
            nodes=nodes,
        )

        adventures[adventure.key] = adventure

    return adventures


def get_adventure(key: str) -> AdventureDefinition:
    adventure = load_adventures().get(key)

    if adventure is None:
        raise KeyError(f"Unknown adventure: {key}")

    return adventure
