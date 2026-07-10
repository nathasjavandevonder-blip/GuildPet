from pathlib import Path

FILES = {
    "migrations/v5_004_adventures_chronicle.py": r'''
from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS adventure_runs_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                starter_user_id INTEGER,
                starter_username TEXT,
                adventure_key TEXT NOT NULL,
                current_node TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                total_xp INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                loot_json TEXT NOT NULL DEFAULT '[]',
                story_log_json TEXT NOT NULL DEFAULT '[]',
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS adventure_choices_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adventure_run_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                node_key TEXT NOT NULL,
                choice_key TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (adventure_run_id)
                    REFERENCES adventure_runs_v5(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS player_wallet_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                tokens INTEGER NOT NULL DEFAULT 0,
                adventure_xp INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS player_items_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                item_key TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id, item_key)
            );

            CREATE TABLE IF NOT EXISTS guild_chronicle_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                entry_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                importance INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_adventure_runs_guild
            ON adventure_runs_v5 (guild_id, status);

            CREATE INDEX IF NOT EXISTS idx_adventure_choices_run
            ON adventure_choices_v5 (adventure_run_id);

            CREATE INDEX IF NOT EXISTS idx_chronicle_guild
            ON guild_chronicle_v5 (guild_id, created_at DESC);
            """
        )
''',

    "data/adventures/whispering_forest.json": r'''
{
  "key": "whispering_forest",
  "name": "Whispering Forest",
  "emoji": "🌲",
  "description": "A mysterious forest filled with old paths and hidden treasures.",
  "start_node": "forest_entrance",
  "nodes": {
    "forest_entrance": {
      "text": "The dragon arrives at a fork in the forest path.",
      "choices": [
        {
          "key": "follow_lights",
          "label": "Follow the lights",
          "emoji": "✨",
          "next_node": "fairy_glade",
          "xp": 8,
          "tokens": 5
        },
        {
          "key": "dark_path",
          "label": "Take the dark path",
          "emoji": "🌑",
          "next_node": "ancient_tree",
          "xp": 10,
          "tokens": 4
        },
        {
          "key": "river_path",
          "label": "Follow the river",
          "emoji": "🌊",
          "next_node": "river_crossing",
          "xp": 6,
          "tokens": 7
        }
      ]
    },
    "fairy_glade": {
      "text": "Tiny lights surround the dragon inside a peaceful glade.",
      "choices": [
        {
          "key": "accept_blessing",
          "label": "Accept the blessing",
          "emoji": "🧚",
          "next_node": "forest_return",
          "xp": 18,
          "tokens": 12,
          "loot": ["fairy_dust"]
        },
        {
          "key": "search_glade",
          "label": "Search the glade",
          "emoji": "🔎",
          "next_node": "hidden_chest",
          "xp": 12,
          "tokens": 9
        }
      ]
    },
    "ancient_tree": {
      "text": "An ancient tree opens its eyes and asks the dragon a riddle.",
      "choices": [
        {
          "key": "answer_riddle",
          "label": "Answer the riddle",
          "emoji": "📜",
          "next_node": "hidden_chest",
          "xp": 22,
          "tokens": 14
        },
        {
          "key": "show_respect",
          "label": "Bow respectfully",
          "emoji": "🐉",
          "next_node": "forest_return",
          "xp": 15,
          "tokens": 10,
          "loot": ["ancient_leaf"]
        }
      ]
    },
    "river_crossing": {
      "text": "The bridge is broken, but something shines beneath the water.",
      "choices": [
        {
          "key": "dive",
          "label": "Dive for it",
          "emoji": "💧",
          "next_node": "hidden_chest",
          "xp": 16,
          "tokens": 11,
          "loot": ["river_crystal"]
        },
        {
          "key": "repair_bridge",
          "label": "Repair the bridge",
          "emoji": "🪵",
          "next_node": "forest_return",
          "xp": 20,
          "tokens": 8
        }
      ]
    },
    "hidden_chest": {
      "text": "The dragon discovers a chest covered in glowing vines.",
      "choices": [
        {
          "key": "open_chest",
          "label": "Open the chest",
          "emoji": "🗝️",
          "next_node": "forest_return",
          "xp": 25,
          "tokens": 25,
          "loot": ["forest_relic", "dragon_snack"]
        },
        {
          "key": "leave_chest",
          "label": "Leave it untouched",
          "emoji": "🌿",
          "next_node": "forest_return",
          "xp": 12,
          "tokens": 6
        }
      ]
    },
    "forest_return": {
      "text": "The dragon finds the road home and returns safely to the guild.",
      "complete": true
    }
  }
}
''',

    "data/adventures/crystal_cave.json": r'''
{
  "key": "crystal_cave",
  "name": "Crystal Cave",
  "emoji": "💎",
  "description": "A glittering cave where every choice echoes through the tunnels.",
  "start_node": "cave_entrance",
  "nodes": {
    "cave_entrance": {
      "text": "Three tunnels stretch into the crystal mountain.",
      "choices": [
        {
          "key": "blue_tunnel",
          "label": "Blue tunnel",
          "emoji": "🔵",
          "next_node": "crystal_lake",
          "xp": 8,
          "tokens": 7
        },
        {
          "key": "red_tunnel",
          "label": "Red tunnel",
          "emoji": "🔴",
          "next_node": "warm_chamber",
          "xp": 10,
          "tokens": 6
        },
        {
          "key": "gold_tunnel",
          "label": "Golden tunnel",
          "emoji": "🟡",
          "next_node": "treasure_echo",
          "xp": 7,
          "tokens": 12
        }
      ]
    },
    "crystal_lake": {
      "text": "A silent underground lake reflects thousands of crystals.",
      "choices": [
        {
          "key": "collect_crystal",
          "label": "Collect a crystal",
          "emoji": "💎",
          "next_node": "cave_exit",
          "xp": 20,
          "tokens": 15,
          "loot": ["blue_crystal"]
        },
        {
          "key": "drink_water",
          "label": "Drink the water",
          "emoji": "🥤",
          "next_node": "cave_exit",
          "xp": 15,
          "tokens": 10
        }
      ]
    },
    "warm_chamber": {
      "text": "Warm air rises from cracks in the stone.",
      "choices": [
        {
          "key": "inspect_cracks",
          "label": "Inspect the cracks",
          "emoji": "🔥",
          "next_node": "cave_exit",
          "xp": 24,
          "tokens": 13,
          "loot": ["ember_stone"]
        },
        {
          "key": "rest",
          "label": "Rest nearby",
          "emoji": "😴",
          "next_node": "cave_exit",
          "xp": 12,
          "tokens": 8
        }
      ]
    },
    "treasure_echo": {
      "text": "The dragon hears coins moving somewhere in the darkness.",
      "choices": [
        {
          "key": "follow_echo",
          "label": "Follow the echo",
          "emoji": "🪙",
          "next_node": "cave_exit",
          "xp": 18,
          "tokens": 30,
          "loot": ["golden_scale"]
        },
        {
          "key": "return_safely",
          "label": "Return safely",
          "emoji": "↩️",
          "next_node": "cave_exit",
          "xp": 10,
          "tokens": 10
        }
      ]
    },
    "cave_exit": {
      "text": "The dragon follows fresh air and returns to the guild.",
      "complete": true
    }
  }
}
''',

    "systems/chronicle/__init__.py": "",

    "systems/chronicle/service.py": r'''
from __future__ import annotations

import json
from typing import Any

from core.database import db_session


def add_chronicle_entry(
    guild_id: int,
    *,
    entry_type: str,
    title: str,
    description: str,
    importance: int = 1,
    metadata: dict[str, Any] | None = None,
) -> int:
    with db_session() as connection:
        cursor = connection.execute(
            """
            INSERT INTO guild_chronicle_v5 (
                guild_id,
                entry_type,
                title,
                description,
                importance,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                entry_type,
                title,
                description,
                importance,
                json.dumps(metadata or {}, separators=(",", ":")),
            ),
        )

        return int(cursor.lastrowid)


def get_chronicle(
    guild_id: int,
    *,
    limit: int = 20,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM guild_chronicle_v5
            WHERE guild_id = ?
            ORDER BY importance DESC, id DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ).fetchall()
''',

    "systems/adventures/models.py": r'''
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
''',

    "systems/adventures/catalog.py": r'''
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
''',

    "systems/adventures/service.py": r'''
from __future__ import annotations

import json

from core.database import db_session
from systems.achievements.service import add_progress
from systems.adventures.catalog import get_adventure
from systems.adventures.models import AdventureResult
from systems.chronicle.service import add_chronicle_entry
from systems.living.personality import dominant_personality
from systems.relationships.service import record_relationship_action
from systems.state.models import DragonState
from systems.state.service import reset_to_idle, set_state


class AdventureNotFound(LookupError):
    pass


class AdventureFinished(ValueError):
    pass


class InvalidAdventureChoice(ValueError):
    pass


def _decode_list(value: str | None) -> list:
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def start_adventure(
    guild_id: int,
    *,
    user_id: int,
    username: str,
    adventure_key: str,
) -> AdventureResult:
    existing = get_active_adventure(guild_id)

    if existing is not None:
        raise ValueError("The dragon is already on an adventure.")

    definition = get_adventure(adventure_key)
    node = definition.nodes[definition.start_node]

    personality = dominant_personality(guild_id)
    opening = (
        f"{definition.emoji} The dragon entered **{definition.name}**. "
        f"Its {personality} nature may influence the journey."
    )

    with db_session() as connection:
        cursor = connection.execute(
            """
            INSERT INTO adventure_runs_v5 (
                guild_id,
                starter_user_id,
                starter_username,
                adventure_key,
                current_node,
                story_log_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                user_id,
                username,
                adventure_key,
                definition.start_node,
                json.dumps([opening, node.text]),
            ),
        )
        run_id = int(cursor.lastrowid)

    set_state(
        guild_id,
        DragonState.ADVENTURE,
        payload={
            "adventure_run_id": run_id,
            "adventure_key": adventure_key,
        },
        force=True,
    )

    add_chronicle_entry(
        guild_id,
        entry_type="adventure_started",
        title=f"Adventure: {definition.name}",
        description=f"{username} sent the dragon to {definition.name}.",
        metadata={"run_id": run_id},
    )

    return get_adventure_result(run_id)


def get_active_adventure(guild_id: int):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM adventure_runs_v5
            WHERE guild_id = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            (guild_id,),
        ).fetchone()


def get_adventure_result(run_id: int) -> AdventureResult:
    with db_session() as connection:
        row = connection.execute(
            "SELECT * FROM adventure_runs_v5 WHERE id = ?",
            (run_id,),
        ).fetchone()

    if row is None:
        raise AdventureNotFound(f"Adventure run {run_id} was not found.")

    definition = get_adventure(row["adventure_key"])
    node = definition.nodes[row["current_node"]]

    return AdventureResult(
        run_id=int(row["id"]),
        adventure_name=definition.name,
        node_text=node.text,
        status=str(row["status"]),
        current_node=str(row["current_node"]),
        total_xp=int(row["total_xp"]),
        total_tokens=int(row["total_tokens"]),
        loot=tuple(_decode_list(row["loot_json"])),
        choices=node.choices,
        story_log=tuple(_decode_list(row["story_log_json"])),
    )


def choose_adventure_path(
    guild_id: int,
    *,
    user_id: int,
    username: str,
    choice_key: str,
) -> AdventureResult:
    run = get_active_adventure(guild_id)

    if run is None:
        raise AdventureNotFound("There is no active adventure.")

    definition = get_adventure(run["adventure_key"])
    current_node = definition.nodes[run["current_node"]]

    choice = next(
        (
            option
            for option in current_node.choices
            if option.key == choice_key
        ),
        None,
    )

    if choice is None:
        raise InvalidAdventureChoice(choice_key)

    next_node = definition.nodes[choice.next_node]
    loot = _decode_list(run["loot_json"])
    story = _decode_list(run["story_log_json"])

    loot.extend(choice.loot)
    story.append(
        f"{username} chose **{choice.label}**. {next_node.text}"
    )

    total_xp = int(run["total_xp"]) + choice.xp
    total_tokens = int(run["total_tokens"]) + choice.tokens
    status = "completed" if next_node.complete else "active"

    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO adventure_choices_v5 (
                adventure_run_id,
                user_id,
                username,
                node_key,
                choice_key
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run["id"],
                user_id,
                username,
                current_node.key,
                choice.key,
            ),
        )

        connection.execute(
            """
            UPDATE adventure_runs_v5
            SET current_node = ?,
                status = ?,
                total_xp = ?,
                total_tokens = ?,
                loot_json = ?,
                story_log_json = ?,
                completed_at = CASE
                    WHEN ? = 'completed' THEN CURRENT_TIMESTAMP
                    ELSE completed_at
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                choice.next_node,
                status,
                total_xp,
                total_tokens,
                json.dumps(loot),
                json.dumps(story),
                status,
                run["id"],
            ),
        )

    record_relationship_action(
        guild_id,
        user_id,
        username,
        "adventure_choice",
    )

    if status == "completed":
        _award_adventure_rewards(
            guild_id,
            run_id=int(run["id"]),
            user_id=user_id,
            username=username,
            xp=total_xp,
            tokens=total_tokens,
            loot=loot,
            adventure_name=definition.name,
        )

    return get_adventure_result(int(run["id"]))


def _award_adventure_rewards(
    guild_id: int,
    *,
    run_id: int,
    user_id: int,
    username: str,
    xp: int,
    tokens: int,
    loot: list[str],
    adventure_name: str,
) -> None:
    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO player_wallet_v5 (
                guild_id,
                user_id,
                username,
                tokens,
                adventure_xp
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET
                username = excluded.username,
                tokens = tokens + excluded.tokens,
                adventure_xp =
                    adventure_xp + excluded.adventure_xp,
                updated_at = CURRENT_TIMESTAMP
            """,
            (guild_id, user_id, username, tokens, xp),
        )

        for item_key in loot:
            connection.execute(
                """
                INSERT INTO player_items_v5 (
                    guild_id,
                    user_id,
                    item_key,
                    quantity
                )
                VALUES (?, ?, ?, 1)
                ON CONFLICT (guild_id, user_id, item_key)
                DO UPDATE SET
                    quantity = quantity + 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (guild_id, user_id, item_key),
            )

    add_progress(guild_id, user_id, "adventures_completed", 1)

    add_chronicle_entry(
        guild_id,
        entry_type="adventure_completed",
        title=f"Completed: {adventure_name}",
        description=(
            f"{username} helped the dragon return with "
            f"{xp} XP, {tokens} tokens and {len(loot)} item(s)."
        ),
        importance=2,
        metadata={"run_id": run_id, "loot": loot},
    )

    reset_to_idle(guild_id, reason="adventure_completed")


def adventure_history(guild_id: int, limit: int = 10):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM adventure_runs_v5
            WHERE guild_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ).fetchall()
''',

    "ui/views/adventure_view.py": r'''
from __future__ import annotations

import discord

from systems.adventures.service import (
    AdventureFinished,
    AdventureNotFound,
    InvalidAdventureChoice,
    choose_adventure_path,
    get_active_adventure,
    get_adventure_result,
)


def build_adventure_embed(guild_id: int) -> discord.Embed:
    run = get_active_adventure(guild_id)

    if run is None:
        return discord.Embed(
            title="🗺️ Adventure Complete",
            description="The dragon has returned home.",
            color=discord.Color.green(),
        )

    result = get_adventure_result(int(run["id"]))

    embed = discord.Embed(
        title=f"🗺️ {result.adventure_name}",
        description=result.node_text,
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="Current rewards",
        value=(
            f"⭐ **{result.total_xp} XP**\n"
            f"🪙 **{result.total_tokens} Tokens**\n"
            f"🎒 **{len(result.loot)} Items**"
        ),
        inline=False,
    )

    embed.set_footer(text=f"Adventure run #{result.run_id}")
    return embed


class AdventureChoiceButton(discord.ui.Button):
    def __init__(self, *, choice, row: int):
        super().__init__(
            label=choice.label,
            emoji=choice.emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"v5_adventure_choice:{choice.key}",
            row=row,
        )
        self.choice_key = choice.key

    async def callback(
        self,
        interaction: discord.Interaction,
    ) -> None:
        view = self.view

        if not isinstance(view, AdventureStateView):
            return

        await view.process_choice(
            interaction,
            self.choice_key,
        )


class AdventureStateView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

        run = get_active_adventure(guild_id)

        if run is None:
            return

        result = get_adventure_result(int(run["id"]))

        for index, choice in enumerate(result.choices[:5]):
            self.add_item(
                AdventureChoiceButton(
                    choice=choice,
                    row=index // 5,
                )
            )

    async def process_choice(
        self,
        interaction: discord.Interaction,
        choice_key: str,
    ) -> None:
        try:
            result = choose_adventure_path(
                interaction.guild_id,
                user_id=interaction.user.id,
                username=interaction.user.display_name,
                choice_key=choice_key,
            )
        except (
            AdventureNotFound,
            AdventureFinished,
            InvalidAdventureChoice,
        ) as exc:
            await interaction.response.send_message(
                f"Adventure action failed: {exc}",
                ephemeral=True,
                delete_after=30,
            )
            return

        if result.status == "completed":
            loot_text = (
                ", ".join(result.loot)
                if result.loot
                else "No items"
            )

            embed = discord.Embed(
                title="🏆 Adventure Complete",
                description=(
                    f"The dragon returned from "
                    f"**{result.adventure_name}**.\n\n"
                    f"⭐ **{result.total_xp} XP**\n"
                    f"🪙 **{result.total_tokens} Tokens**\n"
                    f"🎒 **{loot_text}**\n\n"
                    "Rewards were added automatically."
                ),
                color=discord.Color.green(),
            )

            from ui.view_manager import build_view

            await interaction.response.edit_message(
                embed=embed,
                view=build_view(interaction.guild_id),
            )
            return

        await interaction.response.edit_message(
            embed=build_adventure_embed(interaction.guild_id),
            view=AdventureStateView(interaction.guild_id),
        )
''',

    "ui/views/achievement_view.py": r'''
from __future__ import annotations

import discord

from systems.achievements.service import (
    completion_summary,
    get_progress,
    get_showcase,
    set_showcase,
)


def progress_bar(current: int, target: int, size: int = 10) -> str:
    if target <= 0:
        return "█" * size

    filled = round(min(current / target, 1) * size)
    return "█" * filled + "░" * (size - filled)


def build_achievement_embed(
    guild_id: int,
    user_id: int,
    display_name: str,
) -> discord.Embed:
    progress = get_progress(guild_id, user_id)
    completed, total, percentage = completion_summary(
        guild_id,
        user_id,
    )
    showcase = get_showcase(guild_id, user_id)

    embed = discord.Embed(
        title=f"🏆 {display_name}'s Achievement Hall",
        description=(
            f"**Completion:** {completed}/{total} ({percentage}%)\n"
            f"**Showcase:** "
            f"{showcase.icon + ' ' + showcase.name if showcase else 'None selected'}"
        ),
        color=discord.Color.gold(),
    )

    visible = [
        entry
        for entry in progress
        if not entry.definition.hidden or entry.unlocked
    ]

    for entry in visible[:15]:
        status = "✅" if entry.unlocked else "⬜"
        definition = entry.definition

        embed.add_field(
            name=(
                f"{status} {definition.icon} "
                f"{definition.name}"
            ),
            value=(
                f"`{progress_bar(entry.current, definition.target)}` "
                f"{entry.current}/{definition.target}\n"
                f"{definition.description}"
            ),
            inline=False,
        )

    return embed


class ShowcaseSelect(discord.ui.Select):
    def __init__(self, guild_id: int, user_id: int):
        unlocked = [
            entry
            for entry in get_progress(guild_id, user_id)
            if entry.unlocked
        ]

        options = [
            discord.SelectOption(
                label=entry.definition.name[:100],
                value=entry.definition.key,
                emoji=entry.definition.icon,
                description=entry.definition.rarity.title(),
            )
            for entry in unlocked[:25]
        ]

        if not options:
            options = [
                discord.SelectOption(
                    label="No achievements unlocked",
                    value="none",
                    emoji="🔒",
                )
            ]

        super().__init__(
            placeholder="Choose one showcase achievement",
            options=options,
            custom_id="v5_achievement_showcase_select",
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ) -> None:
        achievement_key = self.values[0]

        if achievement_key == "none":
            await interaction.response.send_message(
                "You have not unlocked an achievement yet.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if not set_showcase(
            interaction.guild_id,
            interaction.user.id,
            achievement_key,
        ):
            await interaction.response.send_message(
                "That achievement cannot be selected.",
                ephemeral=True,
                delete_after=30,
            )
            return

        await interaction.response.edit_message(
            embed=build_achievement_embed(
                interaction.guild_id,
                interaction.user.id,
                interaction.user.display_name,
            ),
            view=AchievementHallView(
                interaction.guild_id,
                interaction.user.id,
            ),
        )


class AchievementHallView(discord.ui.View):
    def __init__(self, guild_id: int, user_id: int):
        super().__init__(timeout=300)
        self.add_item(ShowcaseSelect(guild_id, user_id))
''',

    "tests/test_v5_alpha_pack.py": r'''
from systems.adventures.service import (
    choose_adventure_path,
    get_active_adventure,
    start_adventure,
)
from systems.achievements.service import (
    add_progress,
    completion_summary,
    get_showcase,
    set_showcase,
)
from systems.chronicle.service import get_chronicle
from systems.state.models import DragonState
from systems.state.service import get_state


def main() -> None:
    guild_id = 990005
    user_id = 880005
    username = "Alpha Tester"

    add_progress(guild_id, user_id, "feeds", 25)
    assert set_showcase(
        guild_id,
        user_id,
        "dragon_chef_25",
    )
    assert get_showcase(guild_id, user_id) is not None

    result = start_adventure(
        guild_id,
        user_id=user_id,
        username=username,
        adventure_key="whispering_forest",
    )

    print("Started:", result.adventure_name)
    print("Node:", result.current_node)
    print("Choices:", [choice.key for choice in result.choices])

    safety = 0

    while get_active_adventure(guild_id) is not None:
        run = get_active_adventure(guild_id)
        result = choose_adventure_path(
            guild_id,
            user_id=user_id,
            username=username,
            choice_key=result.choices[0].key,
        )

        safety += 1
        print(
            "Step:",
            result.current_node,
            result.status,
            result.total_xp,
            result.total_tokens,
            result.loot,
        )

        if result.status == "completed":
            break

        if safety > 10:
            raise RuntimeError("Adventure did not finish.")

    assert result.status == "completed"
    assert get_state(guild_id).state == DragonState.IDLE

    chronicle = get_chronicle(guild_id)
    print("Chronicle entries:", len(chronicle))
    print("Completion:", completion_summary(guild_id, user_id))
    print("V5 Alpha pack test passed.")


if __name__ == "__main__":
    main()
''',
}

for filename, content in FILES.items():
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")
    print(f"Created {filename}")

print(f"\nCreated {len(FILES)} V5 Alpha files.")
