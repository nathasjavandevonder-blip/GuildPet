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
