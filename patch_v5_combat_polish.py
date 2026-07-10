from __future__ import annotations

from pathlib import Path
import shutil
from datetime import datetime


ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / "backups" / f"combat_polish_{datetime.now():%Y%m%d_%H%M%S}"
BACKUP.mkdir(parents=True, exist_ok=True)


def backup(path: Path) -> None:
    if path.exists():
        target = BACKUP / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")

    if old not in text:
        raise RuntimeError(
            f"Required code block not found in {path}:\n{old[:180]}"
        )

    backup(path)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"Updated {path.relative_to(ROOT)}")


# ------------------------------------------------------------------
# Item catalog
# ------------------------------------------------------------------

items_dir = ROOT / "data" / "items"
items_dir.mkdir(parents=True, exist_ok=True)

items_file = items_dir / "items.json"
items_file.write_text(
    """[
  {
    "key": "goblin_tooth",
    "name": "Goblin Tooth",
    "emoji": "🦷",
    "rarity": "common",
    "description": "A small tooth collected after defeating a goblin."
  },
  {
    "key": "training_badge",
    "name": "Training Badge",
    "emoji": "🎖️",
    "rarity": "rare",
    "description": "Proof that the dragon completed combat training."
  },
  {
    "key": "small_healing_herb",
    "name": "Small Healing Herb",
    "emoji": "🌿",
    "rarity": "common",
    "description": "A useful herb with mild restorative properties."
  },
  {
    "key": "fairy_dust",
    "name": "Fairy Dust",
    "emoji": "✨",
    "rarity": "rare",
    "description": "Glittering dust found in an enchanted glade."
  },
  {
    "key": "ancient_leaf",
    "name": "Ancient Leaf",
    "emoji": "🍂",
    "rarity": "rare",
    "description": "A leaf from a tree older than the guild."
  },
  {
    "key": "river_crystal",
    "name": "River Crystal",
    "emoji": "💠",
    "rarity": "rare",
    "description": "A crystal polished by underground water."
  },
  {
    "key": "forest_relic",
    "name": "Forest Relic",
    "emoji": "🗿",
    "rarity": "epic",
    "description": "A mysterious relic covered in glowing vines."
  },
  {
    "key": "dragon_snack",
    "name": "Dragon Snack",
    "emoji": "🍖",
    "rarity": "common",
    "description": "A tasty snack saved for later."
  },
  {
    "key": "blue_crystal",
    "name": "Blue Crystal",
    "emoji": "🔷",
    "rarity": "rare",
    "description": "A crystal found beside an underground lake."
  },
  {
    "key": "ember_stone",
    "name": "Ember Stone",
    "emoji": "🔥",
    "rarity": "epic",
    "description": "A warm stone carrying a faint inner flame."
  },
  {
    "key": "golden_scale",
    "name": "Golden Scale",
    "emoji": "🌟",
    "rarity": "legendary",
    "description": "A beautiful golden scale found deep underground."
  }
]
""",
    encoding="utf-8",
)
print("Created data/items/items.json")


items_system = ROOT / "systems" / "items"
items_system.mkdir(parents=True, exist_ok=True)
(items_system / "__init__.py").touch()

(items_system / "catalog.py").write_text(
    '''from __future__ import annotations

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
''',
    encoding="utf-8",
)
print("Created systems/items/catalog.py")


# ------------------------------------------------------------------
# Living-dragon combat aftermath
# ------------------------------------------------------------------

living_service = ROOT / "systems" / "living" / "service.py"
backup(living_service)

living_text = living_service.read_text(encoding="utf-8")

if "def apply_combat_aftermath(" not in living_text:
    living_text += '''


def apply_combat_aftermath(guild_id: int) -> LivingState:
    """Apply fatigue and excitement immediately after combat."""
    current = ensure_living_state(guild_id)

    hunger = clamp(current.hunger - 4)
    happiness = clamp(current.happiness + 4)
    energy = clamp(current.energy - 12)
    cleanliness = clamp(current.cleanliness - 3)

    mood = calculate_mood(
        hunger=hunger,
        happiness=happiness,
        energy=energy,
        cleanliness=cleanliness,
        bond=current.bond,
    )

    with db_session() as connection:
        connection.execute(
            """
            UPDATE dragon_living_v5
            SET hunger = ?,
                happiness = ?,
                energy = ?,
                cleanliness = ?,
                mood = ?,
                current_activity = 'catching its breath',
                updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                hunger,
                happiness,
                energy,
                cleanliness,
                mood.value,
                guild_id,
            ),
        )

    return get_living_state(guild_id)


def finish_combat_recovery(guild_id: int) -> LivingState:
    """Return the dragon to its normal post-combat activity."""
    current = ensure_living_state(guild_id)

    energy = clamp(current.energy + 5)

    mood = calculate_mood(
        hunger=current.hunger,
        happiness=current.happiness,
        energy=energy,
        cleanliness=current.cleanliness,
        bond=current.bond,
    )

    with db_session() as connection:
        connection.execute(
            """
            UPDATE dragon_living_v5
            SET energy = ?,
                mood = ?,
                current_activity = 'watching the guild',
                updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                energy,
                mood.value,
                guild_id,
            ),
        )

    return get_living_state(guild_id)
'''

    living_service.write_text(living_text, encoding="utf-8")
    print("Updated systems/living/service.py")


# ------------------------------------------------------------------
# Combat state: victory now enters Recovering for 60 seconds
# ------------------------------------------------------------------

combat_service = ROOT / "systems" / "combat" / "service.py"

replace_once(
    combat_service,
    "import json\nimport random\n",
    "import json\nimport random\nfrom datetime import timedelta\n",
)

combat_text = combat_service.read_text(encoding="utf-8")

if "from systems.living.service import apply_combat_aftermath" not in combat_text:
    replace_once(
        combat_service,
        "from systems.relationships.service import record_relationship_action\n",
        "from systems.relationships.service import record_relationship_action\n"
        "from systems.living.service import apply_combat_aftermath\n",
    )

replace_once(
    combat_service,
    '''        reset_to_idle(
            guild_id,
            reason="combat_victory",
        )
''',
    '''        apply_combat_aftermath(guild_id)

        set_state(
            guild_id,
            DragonState.RECOVERING,
            duration=timedelta(seconds=60),
            payload={
                "reason": "combat_victory",
                "combat_id": int(combat["id"]),
            },
            force=True,
        )
''',
)


# ------------------------------------------------------------------
# Main panel resolves timed states automatically
# ------------------------------------------------------------------

main_panel = ROOT / "ui" / "main_panel.py"

replace_once(
    main_panel,
    "from systems.state.service import ensure_state\n",
    "from systems.state.service import resolve_expired_state\n",
)

replace_once(
    main_panel,
    "    state = ensure_state(guild_id)\n",
    "    state = resolve_expired_state(guild_id)\n",
)


# ------------------------------------------------------------------
# Combat UI: prettier bars, item names and automatic recovery refresh
# ------------------------------------------------------------------

combat_view = ROOT / "ui" / "views" / "combat_view.py"
combat_view_text = combat_view.read_text(encoding="utf-8")
backup(combat_view)

if "from systems.items.catalog import format_item" not in combat_view_text:
    combat_view_text = combat_view_text.replace(
        "from systems.combat.models import CombatResult\n",
        "from systems.combat.models import CombatResult\n"
        "from systems.items.catalog import format_item\n"
        "from systems.living.service import finish_combat_recovery\n",
        1,
    )

if "refresh_main_panel_in_place" not in combat_view_text:
    combat_view_text = combat_view_text.replace(
        "from ui.panel_manager import move_main_panel_to_bottom\n",
        "from ui.panel_manager import (\n"
        "    move_main_panel_to_bottom,\n"
        "    refresh_main_panel_in_place,\n"
        ")\n",
        1,
    )

old_health_bar = '''def health_bar(current: int, maximum: int, size: int = 10) -> str:
    if maximum <= 0:
        return "░" * size

    filled = round((current / maximum) * size)
    filled = max(0, min(size, filled))

    return "█" * filled + "░" * (size - filled)
'''

new_health_bar = '''def health_bar(current: int, maximum: int, size: int = 10) -> str:
    if maximum <= 0:
        return "⬛" * size

    filled = round((current / maximum) * size)
    filled = max(0, min(size, filled))

    return "🟩" * filled + "⬛" * (size - filled)
'''

if old_health_bar in combat_view_text:
    combat_view_text = combat_view_text.replace(
        old_health_bar,
        new_health_bar,
        1,
    )

combat_view_text = combat_view_text.replace(
    '''f"`{health_bar(combat['dragon_hp'], combat['dragon_max_hp'])}`\\n"''',
    '''f"{health_bar(combat['dragon_hp'], combat['dragon_max_hp'])}\\n"''',
)

combat_view_text = combat_view_text.replace(
    '''f"`{health_bar(combat['enemy_hp'], combat['enemy_max_hp'])}`\\n"''',
    '''f"{health_bar(combat['enemy_hp'], combat['enemy_max_hp'])}\\n"''',
)

combat_view_text = combat_view_text.replace(
    '''f"`{health_bar(result.dragon_hp, result.dragon_max_hp)}`\\n"''',
    '''f"{health_bar(result.dragon_hp, result.dragon_max_hp)}\\n"''',
)

combat_view_text = combat_view_text.replace(
    '''f"`{health_bar(result.enemy_hp, result.enemy_max_hp)}`\\n"''',
    '''f"{health_bar(result.enemy_hp, result.enemy_max_hp)}\\n"''',
)

old_loot = '''    loot_text = (
        "\\n".join(f"• `{item}`" for item in result.loot)
        if result.loot
        else "No item drops this time."
    )
'''

new_loot = '''    loot_text = (
        "\\n".join(
            f"• {format_item(item)}"
            for item in result.loot
        )
        if result.loot
        else "No item drops this time."
    )
'''

if old_loot not in combat_view_text:
    raise RuntimeError("Could not locate reward loot formatting block.")

combat_view_text = combat_view_text.replace(
    old_loot,
    new_loot,
    1,
)

if "async def finish_recovery_later(" not in combat_view_text:
    marker = "\ndef health_bar("

    recovery_helper = '''
async def finish_recovery_later(
    guild: discord.Guild,
    seconds: int = 60,
) -> None:
    await asyncio.sleep(seconds)

    finish_combat_recovery(guild.id)

    try:
        await refresh_main_panel_in_place(guild)
    except (
        discord.NotFound,
        discord.Forbidden,
        discord.HTTPException,
    ):
        pass


'''

    combat_view_text = combat_view_text.replace(
        marker,
        "\n" + recovery_helper + "def health_bar(",
        1,
    )

old_panel_move = '''        await move_main_panel_to_bottom(
            interaction.guild,
            interaction.channel,
        )
'''

new_panel_move = '''        await move_main_panel_to_bottom(
            interaction.guild,
            interaction.channel,
        )

        if result.status == "victory":
            asyncio.create_task(
                finish_recovery_later(
                    interaction.guild,
                    60,
                )
            )
'''

if old_panel_move not in combat_view_text:
    raise RuntimeError("Could not locate main panel move block.")

combat_view_text = combat_view_text.replace(
    old_panel_move,
    new_panel_move,
    1,
)

combat_view.write_text(combat_view_text, encoding="utf-8")
print("Updated ui/views/combat_view.py")


# ------------------------------------------------------------------
# Test
# ------------------------------------------------------------------

test_file = ROOT / "tests" / "test_v5_combat_polish.py"
test_file.write_text(
    '''from systems.items.catalog import format_item, get_item
from systems.living.service import (
    apply_combat_aftermath,
    finish_combat_recovery,
)
from systems.state.models import DragonState
from systems.state.service import get_state


def main() -> None:
    guild_id = 990007

    item = get_item("goblin_tooth")
    assert item.name == "Goblin Tooth"
    assert "🦷" in format_item("goblin_tooth")

    recovering = apply_combat_aftermath(guild_id)
    assert recovering.current_activity == "catching its breath"

    recovered = finish_combat_recovery(guild_id)
    assert recovered.current_activity == "watching the guild"

    print("Formatted item:", format_item("goblin_tooth"))
    print("Recovery activity:", recovered.current_activity)
    print("V5 combat polish test passed.")


if __name__ == "__main__":
    main()
''',
    encoding="utf-8",
)
print("Created tests/test_v5_combat_polish.py")

print(f"\\nBackup created at: {BACKUP}")
print("Combat polish patch completed.")
