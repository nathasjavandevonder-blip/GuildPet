from pathlib import Path

FILES = {
    "migrations/v5_005_combat_rewards.py": r'''
from core.database import db_session


def upgrade() -> None:
    with db_session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS player_combat_progress_v5 (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                combat_xp INTEGER NOT NULL DEFAULT 0,
                victories INTEGER NOT NULL DEFAULT 0,
                defeats INTEGER NOT NULL DEFAULT 0,
                retreats INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS combat_rewards_v5 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                combat_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                tokens INTEGER NOT NULL DEFAULT 0,
                loot_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (combat_id)
                    REFERENCES combat_sessions(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_combat_rewards_session
            ON combat_rewards_v5 (combat_id);

            CREATE INDEX IF NOT EXISTS idx_combat_progress_guild
            ON player_combat_progress_v5 (
                guild_id,
                victories DESC,
                combat_xp DESC
            );
            """
        )
''',

    "systems/combat/models.py": r'''
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
''',

    "systems/combat/catalog.py": r'''
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
''',

    "data/enemies/training_goblin.json": r'''
{
  "key": "training_goblin",
  "name": "Training Goblin",
  "emoji": "👺",
  "max_hp": 70,
  "attack_min": 5,
  "attack_max": 11,
  "armor": 1,
  "fire_weakness": 1.35,
  "xp_reward": 20,
  "token_reward": 30,
  "loot_table": [
    {
      "item_key": "goblin_tooth",
      "chance": 0.65,
      "min_quantity": 1,
      "max_quantity": 1
    },
    {
      "item_key": "training_badge",
      "chance": 0.20,
      "min_quantity": 1,
      "max_quantity": 1
    },
    {
      "item_key": "small_healing_herb",
      "chance": 0.35,
      "min_quantity": 1,
      "max_quantity": 2
    }
  ]
}
''',

    "systems/combat/service.py": r'''
from __future__ import annotations

import json
import random

from core.database import db_session
from systems.achievements.service import add_progress
from systems.chronicle.service import add_chronicle_entry
from systems.combat.catalog import get_enemy
from systems.combat.models import CombatResult
from systems.relationships.service import record_relationship_action
from systems.state.models import DragonState
from systems.state.service import reset_to_idle, set_state


class CombatNotFound(LookupError):
    pass


class CombatFinished(ValueError):
    pass


def start_combat(
    guild_id: int,
    *,
    enemy_key: str = "training_goblin",
    dragon_max_hp: int = 100,
    channel_id: int | None = None,
    message_id: int | None = None,
) -> int:
    if get_active_combat(guild_id) is not None:
        raise ValueError("The dragon is already in combat.")

    enemy = get_enemy(enemy_key)

    with db_session() as connection:
        cursor = connection.execute(
            """
            INSERT INTO combat_sessions (
                guild_id,
                channel_id,
                message_id,
                dragon_hp,
                dragon_max_hp,
                enemy_key,
                enemy_hp,
                enemy_max_hp,
                turn_number,
                status,
                combat_data,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active', '{}',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """,
            (
                guild_id,
                channel_id,
                message_id,
                dragon_max_hp,
                dragon_max_hp,
                enemy.key,
                enemy.max_hp,
                enemy.max_hp,
            ),
        )
        combat_id = int(cursor.lastrowid)

    set_state(
        guild_id,
        DragonState.COMBAT,
        payload={"combat_id": combat_id},
        force=True,
    )

    return combat_id


def get_active_combat(guild_id: int):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM combat_sessions
            WHERE guild_id = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            (guild_id,),
        ).fetchone()


def get_combat(combat_id: int):
    with db_session() as connection:
        return connection.execute(
            "SELECT * FROM combat_sessions WHERE id = ?",
            (combat_id,),
        ).fetchone()


def get_recent_actions(
    combat_id: int,
    *,
    limit: int = 4,
):
    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM combat_actions_v5
            WHERE combat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (combat_id, limit),
        ).fetchall()

    return list(reversed(rows))


def _enemy_attack(enemy, guarded: bool) -> tuple[int, str]:
    damage = random.randint(
        enemy.attack_min,
        enemy.attack_max,
    )

    if guarded:
        damage = max(1, damage // 2)
        return damage, (
            f"{enemy.emoji} **{enemy.name}** attacks, "
            f"but Guard reduces the damage to **{damage}**."
        )

    return damage, (
        f"{enemy.emoji} **{enemy.name}** attacks for "
        f"**{damage} damage**."
    )


def _roll_loot(enemy) -> list[str]:
    loot: list[str] = []

    for entry in enemy.loot_table:
        chance = float(entry.get("chance", 0))

        if random.random() > chance:
            continue

        minimum = int(entry.get("min_quantity", 1))
        maximum = int(entry.get("max_quantity", minimum))
        quantity = random.randint(minimum, maximum)
        item_key = str(entry["item_key"])

        loot.extend([item_key] * quantity)

    return loot


def _award_victory(
    *,
    combat_id: int,
    guild_id: int,
    user_id: int,
    username: str,
    enemy,
    dragon_hp: int,
) -> tuple[list[str], list[str]]:
    loot = _roll_loot(enemy)
    unlocked: list[str] = []

    unlocked.extend(
        add_progress(
            guild_id,
            user_id,
            "combat_wins",
            1,
        )
    )

    if dragon_hp <= 5:
        unlocked.extend(
            add_progress(
                guild_id,
                user_id,
                "low_hp_victories",
                1,
            )
        )

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
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET
                username = excluded.username,
                tokens = tokens + excluded.tokens,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                guild_id,
                user_id,
                username,
                enemy.token_reward,
            ),
        )

        connection.execute(
            """
            INSERT INTO player_combat_progress_v5 (
                guild_id,
                user_id,
                username,
                combat_xp,
                victories
            )
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET
                username = excluded.username,
                combat_xp = combat_xp + excluded.combat_xp,
                victories = victories + 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                guild_id,
                user_id,
                username,
                enemy.xp_reward,
            ),
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
                (
                    guild_id,
                    user_id,
                    item_key,
                ),
            )

        connection.execute(
            """
            INSERT INTO combat_rewards_v5 (
                combat_id,
                guild_id,
                user_id,
                username,
                xp,
                tokens,
                loot_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                combat_id,
                guild_id,
                user_id,
                username,
                enemy.xp_reward,
                enemy.token_reward,
                json.dumps(loot),
            ),
        )

        connection.execute(
            """
            UPDATE combat_sessions
            SET combat_data = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                json.dumps(
                    {
                        "winner_user_id": user_id,
                        "winner_username": username,
                        "xp_reward": enemy.xp_reward,
                        "token_reward": enemy.token_reward,
                        "loot": loot,
                        "achievements": list(dict.fromkeys(unlocked)),
                    }
                ),
                combat_id,
            ),
        )

    record_relationship_action(
        guild_id,
        user_id,
        username,
        "combat",
    )

    add_chronicle_entry(
        guild_id,
        entry_type="combat_victory",
        title=f"Victory over {enemy.name}",
        description=(
            f"{username} guided the dragon to victory and earned "
            f"{enemy.xp_reward} XP and {enemy.token_reward} tokens."
        ),
        importance=2,
        metadata={
            "combat_id": combat_id,
            "enemy_key": enemy.key,
            "loot": loot,
        },
    )

    return loot, list(dict.fromkeys(unlocked))


def perform_action(
    guild_id: int,
    *,
    user_id: int,
    username: str,
    action_key: str,
) -> CombatResult:
    combat = get_active_combat(guild_id)

    if combat is None:
        raise CombatNotFound("No active combat found.")

    enemy = get_enemy(combat["enemy_key"])

    dragon_hp = int(combat["dragon_hp"])
    enemy_hp = int(combat["enemy_hp"])
    turn = int(combat["turn_number"])

    guarded = action_key == "guard"
    damage = 0
    loot: list[str] = []
    unlocked: list[str] = []
    xp_reward = 0
    token_reward = 0

    if action_key == "attack":
        damage = max(
            1,
            random.randint(9, 16) - enemy.armor,
        )
        action_text = (
            f"🦴 **{username}** orders a bite attack for "
            f"**{damage} damage**."
        )

    elif action_key == "fire_breath":
        base_damage = random.randint(12, 20)
        damage = max(
            1,
            int(base_damage * enemy.fire_weakness) - enemy.armor,
        )
        action_text = (
            f"🔥 **{username}** uses Fire Breath for "
            f"**{damage} damage**."
        )

    elif action_key == "guard":
        action_text = (
            f"🛡️ **{username}** tells the dragon to guard."
        )

    elif action_key == "retreat":
        with db_session() as connection:
            connection.execute(
                """
                UPDATE combat_sessions
                SET status = 'retreated',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (combat["id"],),
            )

            connection.execute(
                """
                INSERT INTO player_combat_progress_v5 (
                    guild_id,
                    user_id,
                    username,
                    retreats
                )
                VALUES (?, ?, ?, 1)
                ON CONFLICT (guild_id, user_id)
                DO UPDATE SET
                    username = excluded.username,
                    retreats = retreats + 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (guild_id, user_id, username),
            )

        description = (
            f"🏃 **{username}** helped the dragon retreat safely."
        )

        _save_action(
            combat_id=int(combat["id"]),
            user_id=user_id,
            username=username,
            action_key=action_key,
            damage=0,
            description=description,
            turn=turn,
        )

        reset_to_idle(
            guild_id,
            reason="combat_retreat",
        )

        return CombatResult(
            combat_id=int(combat["id"]),
            enemy_key=enemy.key,
            enemy_name=enemy.name,
            enemy_emoji=enemy.emoji,
            description=description,
            dragon_hp=dragon_hp,
            dragon_max_hp=int(combat["dragon_max_hp"]),
            enemy_hp=enemy_hp,
            enemy_max_hp=int(combat["enemy_max_hp"]),
            status="retreated",
            turn_number=turn,
        )

    else:
        raise ValueError(f"Unknown combat action: {action_key}")

    enemy_hp = max(enemy_hp - damage, 0)
    log_lines = [action_text]

    if enemy_hp <= 0:
        status = "victory"
        log_lines.append(
            f"🏆 **{enemy.name} was defeated!**"
        )

        with db_session() as connection:
            connection.execute(
                """
                UPDATE combat_sessions
                SET enemy_hp = 0,
                    status = 'victory',
                    turn_number = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    turn,
                    combat["id"],
                ),
            )

        loot, unlocked = _award_victory(
            combat_id=int(combat["id"]),
            guild_id=guild_id,
            user_id=user_id,
            username=username,
            enemy=enemy,
            dragon_hp=dragon_hp,
        )

        xp_reward = enemy.xp_reward
        token_reward = enemy.token_reward

        reset_to_idle(
            guild_id,
            reason="combat_victory",
        )

    else:
        enemy_damage, enemy_text = _enemy_attack(
            enemy,
            guarded,
        )
        dragon_hp = max(dragon_hp - enemy_damage, 0)
        log_lines.append(enemy_text)

        if dragon_hp <= 0:
            status = "defeat"
            log_lines.append(
                "💔 The dragon was defeated and must recover."
            )

            with db_session() as connection:
                connection.execute(
                    """
                    INSERT INTO player_combat_progress_v5 (
                        guild_id,
                        user_id,
                        username,
                        defeats
                    )
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT (guild_id, user_id)
                    DO UPDATE SET
                        username = excluded.username,
                        defeats = defeats + 1,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        guild_id,
                        user_id,
                        username,
                    ),
                )

            set_state(
                guild_id,
                DragonState.RECOVERING,
                payload={
                    "reason": "combat_defeat",
                    "combat_id": combat["id"],
                },
                force=True,
            )
        else:
            status = "active"

        with db_session() as connection:
            connection.execute(
                """
                UPDATE combat_sessions
                SET dragon_hp = ?,
                    enemy_hp = ?,
                    status = ?,
                    turn_number = turn_number + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    dragon_hp,
                    enemy_hp,
                    status,
                    combat["id"],
                ),
            )

    description = "\n".join(log_lines)

    _save_action(
        combat_id=int(combat["id"]),
        user_id=user_id,
        username=username,
        action_key=action_key,
        damage=damage,
        description=description,
        turn=turn,
    )

    return CombatResult(
        combat_id=int(combat["id"]),
        enemy_key=enemy.key,
        enemy_name=enemy.name,
        enemy_emoji=enemy.emoji,
        description=description,
        dragon_hp=dragon_hp,
        dragon_max_hp=int(combat["dragon_max_hp"]),
        enemy_hp=enemy_hp,
        enemy_max_hp=int(combat["enemy_max_hp"]),
        status=status,
        turn_number=turn,
        xp_reward=xp_reward,
        token_reward=token_reward,
        loot=tuple(loot),
        unlocked_achievements=tuple(unlocked),
    )


def _save_action(
    *,
    combat_id: int,
    user_id: int,
    username: str,
    action_key: str,
    damage: int,
    description: str,
    turn: int,
) -> None:
    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO combat_participants_v5 (
                combat_id,
                user_id,
                username,
                contribution,
                last_action,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (combat_id, user_id)
            DO UPDATE SET
                username = excluded.username,
                contribution =
                    contribution + excluded.contribution,
                last_action = excluded.last_action,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                combat_id,
                user_id,
                username,
                damage,
                action_key,
            ),
        )

        connection.execute(
            """
            INSERT INTO combat_actions_v5 (
                combat_id,
                user_id,
                action_key,
                damage,
                description,
                turn_number
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                combat_id,
                user_id,
                action_key,
                damage,
                description,
                turn,
            ),
        )
''',

    "ui/views/combat_view.py": r'''
from __future__ import annotations

import discord

from systems.combat.catalog import get_enemy
from systems.combat.models import CombatResult
from systems.combat.service import (
    CombatFinished,
    CombatNotFound,
    get_active_combat,
    get_combat,
    get_recent_actions,
    perform_action,
)


def health_bar(current: int, maximum: int, size: int = 10) -> str:
    if maximum <= 0:
        return "░" * size

    filled = round((current / maximum) * size)
    filled = max(0, min(size, filled))

    return "█" * filled + "░" * (size - filled)


def _battle_log(combat_id: int) -> str:
    rows = get_recent_actions(
        combat_id,
        limit=4,
    )

    if not rows:
        return "The battle has just begun."

    sections = []

    for row in rows:
        sections.append(
            f"**Round {row['turn_number']}**\n"
            f"{row['description']}"
        )

    return "\n\n".join(sections)[-1900:]


def build_combat_embed(
    guild_id: int,
    description: str | None = None,
) -> discord.Embed:
    combat = get_active_combat(guild_id)

    if combat is None:
        return discord.Embed(
            title="⚔️ Combat Ended",
            description=description or "There is no active combat.",
        )

    enemy = get_enemy(combat["enemy_key"])

    embed = discord.Embed(
        title=f"⚔️ {enemy.emoji} {enemy.name}",
        description=description or "Choose the dragon's next action.",
        color=discord.Color.red(),
    )

    embed.add_field(
        name="🐉 Dragon HP",
        value=(
            f"`{health_bar(combat['dragon_hp'], combat['dragon_max_hp'])}`\n"
            f"**{combat['dragon_hp']} / {combat['dragon_max_hp']}**"
        ),
        inline=True,
    )

    embed.add_field(
        name=f"{enemy.emoji} Enemy HP",
        value=(
            f"`{health_bar(combat['enemy_hp'], combat['enemy_max_hp'])}`\n"
            f"**{combat['enemy_hp']} / {combat['enemy_max_hp']}**"
        ),
        inline=True,
    )

    embed.add_field(
        name="📜 Battle Log",
        value=_battle_log(int(combat["id"])),
        inline=False,
    )

    embed.set_footer(
        text=f"Turn {combat['turn_number']}"
    )

    return embed


def build_finished_combat_embed(
    result: CombatResult,
) -> discord.Embed:
    if result.status == "victory":
        title = "🏆 Victory!"
        color = discord.Color.green()
    elif result.status == "defeat":
        title = "💔 Defeat"
        color = discord.Color.red()
    else:
        title = "🏃 Combat Ended"
        color = discord.Color.orange()

    embed = discord.Embed(
        title=title,
        description=result.description,
        color=color,
    )

    embed.add_field(
        name="🐉 Dragon HP",
        value=(
            f"`{health_bar(result.dragon_hp, result.dragon_max_hp)}`\n"
            f"**{result.dragon_hp} / {result.dragon_max_hp}**"
        ),
        inline=True,
    )

    embed.add_field(
        name=f"{result.enemy_emoji} Enemy HP",
        value=(
            f"`{health_bar(result.enemy_hp, result.enemy_max_hp)}`\n"
            f"**{result.enemy_hp} / {result.enemy_max_hp}**"
        ),
        inline=True,
    )

    embed.add_field(
        name="📜 Final Battle Log",
        value=_battle_log(result.combat_id),
        inline=False,
    )

    embed.set_footer(
        text="Combat finished — controls disabled"
    )
    return embed


def build_reward_embed(
    result: CombatResult,
) -> discord.Embed:
    loot_text = (
        "\n".join(f"• `{item}`" for item in result.loot)
        if result.loot
        else "No item drops this time."
    )

    embed = discord.Embed(
        title="🎁 Combat Rewards",
        description=(
            f"⭐ **{result.xp_reward} Combat XP**\n"
            f"🪙 **{result.token_reward} Tokens**\n\n"
            f"**Loot**\n{loot_text}"
        ),
        color=discord.Color.gold(),
    )

    if result.unlocked_achievements:
        embed.add_field(
            name="🏆 Achievements Unlocked",
            value="\n".join(
                f"• `{key}`"
                for key in result.unlocked_achievements
            ),
            inline=False,
        )

    embed.set_footer(
        text="This reward message disappears after 5 minutes."
    )
    return embed


class FinishedCombatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        buttons = (
            ("Attack", "🦴", discord.ButtonStyle.primary),
            ("Fire Breath", "🔥", discord.ButtonStyle.danger),
            ("Guard", "🛡️", discord.ButtonStyle.secondary),
            ("Retreat", "🏃", discord.ButtonStyle.secondary),
        )

        for index, (label, emoji, style) in enumerate(buttons):
            self.add_item(
                discord.ui.Button(
                    label=label,
                    emoji=emoji,
                    style=style,
                    disabled=True,
                    custom_id=f"v5_combat_finished_{index}",
                )
            )


class CombatStateView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    async def process_action(
        self,
        interaction: discord.Interaction,
        action_key: str,
    ) -> None:
        try:
            result = perform_action(
                interaction.guild_id,
                user_id=interaction.user.id,
                username=interaction.user.display_name,
                action_key=action_key,
            )
        except CombatNotFound:
            await interaction.response.send_message(
                "This combat is no longer active.",
                ephemeral=True,
                delete_after=30,
            )
            return
        except CombatFinished:
            await interaction.response.send_message(
                "This combat has already finished.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if result.status == "active":
            await interaction.response.edit_message(
                embed=build_combat_embed(
                    interaction.guild_id,
                    result.description,
                ),
                view=CombatStateView(interaction.guild_id),
            )
            return

        await interaction.response.edit_message(
            embed=build_finished_combat_embed(result),
            view=FinishedCombatView(),
        )

        if result.status == "victory":
            await interaction.followup.send(
                embed=build_reward_embed(result),
                delete_after=300,
            )

    @discord.ui.button(
        label="Attack",
        emoji="🦴",
        style=discord.ButtonStyle.primary,
        custom_id="v5_combat_attack",
    )
    async def attack(self, interaction, button):
        await self.process_action(interaction, "attack")

    @discord.ui.button(
        label="Fire Breath",
        emoji="🔥",
        style=discord.ButtonStyle.danger,
        custom_id="v5_combat_fire",
    )
    async def fire_breath(self, interaction, button):
        await self.process_action(interaction, "fire_breath")

    @discord.ui.button(
        label="Guard",
        emoji="🛡️",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_combat_guard",
    )
    async def guard(self, interaction, button):
        await self.process_action(interaction, "guard")

    @discord.ui.button(
        label="Retreat",
        emoji="🏃",
        style=discord.ButtonStyle.secondary,
        custom_id="v5_combat_retreat",
    )
    async def retreat(self, interaction, button):
        await self.process_action(interaction, "retreat")
''',

    "tests/test_v5_combat2.py": r'''
from core.database import db_session
from systems.combat.service import (
    get_active_combat,
    get_combat,
    get_recent_actions,
    perform_action,
    start_combat,
)


def clean_test_data(guild_id: int) -> None:
    with db_session() as connection:
        combat_rows = connection.execute(
            "SELECT id FROM combat_sessions WHERE guild_id = ?",
            (guild_id,),
        ).fetchall()

        combat_ids = [int(row["id"]) for row in combat_rows]

        for combat_id in combat_ids:
            connection.execute(
                "DELETE FROM combat_rewards_v5 WHERE combat_id = ?",
                (combat_id,),
            )
            connection.execute(
                "DELETE FROM combat_actions_v5 WHERE combat_id = ?",
                (combat_id,),
            )
            connection.execute(
                "DELETE FROM combat_participants_v5 WHERE combat_id = ?",
                (combat_id,),
            )

        connection.execute(
            "DELETE FROM combat_sessions WHERE guild_id = ?",
            (guild_id,),
        )


def main() -> None:
    guild_id = 990006
    user_id = 880006

    clean_test_data(guild_id)

    combat_id = start_combat(
        guild_id,
        enemy_key="training_goblin",
    )

    result = None

    for round_number in range(1, 15):
        result = perform_action(
            guild_id,
            user_id=user_id,
            username="Combat Tester",
            action_key="fire_breath",
        )

        print(
            "Round",
            round_number,
            result.status,
            result.dragon_hp,
            result.enemy_hp,
        )

        if result.status != "active":
            break

    assert result is not None
    assert result.status == "victory"
    assert get_active_combat(guild_id) is None
    assert get_combat(combat_id)["status"] == "victory"
    assert len(get_recent_actions(combat_id)) >= 1
    assert result.xp_reward > 0
    assert result.token_reward > 0

    print("Loot:", result.loot)
    print("Achievements:", result.unlocked_achievements)
    print("V5 Combat 2.0 test passed.")


if __name__ == "__main__":
    main()
''',
}

for filename, content in FILES.items():
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8")
    print(f"Created {filename}")

print(f"\nCreated {len(FILES)} Combat 2.0 files.")
