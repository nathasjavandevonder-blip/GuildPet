from __future__ import annotations

from core.database import db_session


def get_stack(
    guild_id: int,
    item_key: str,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT guild_id, item_key, quantity
            FROM inventory_items_v5
            WHERE guild_id = ?
              AND item_key = ?
            """,
            (guild_id, item_key),
        ).fetchone()


def get_all_stacks(guild_id: int):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT guild_id, item_key, quantity
            FROM inventory_items_v5
            WHERE guild_id = ?
              AND quantity > 0
            ORDER BY item_key ASC
            """,
            (guild_id,),
        ).fetchall()


def add_quantity(
    guild_id: int,
    item_key: str,
    quantity: int,
) -> int:
    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO inventory_items_v5 (
                guild_id,
                item_key,
                quantity
            )
            VALUES (?, ?, ?)
            ON CONFLICT (guild_id, item_key)
            DO UPDATE SET
                quantity = quantity + excluded.quantity,
                updated_at = CURRENT_TIMESTAMP
            """,
            (guild_id, item_key, quantity),
        )

        row = connection.execute(
            """
            SELECT quantity
            FROM inventory_items_v5
            WHERE guild_id = ?
              AND item_key = ?
            """,
            (guild_id, item_key),
        ).fetchone()

    return int(row["quantity"])


def remove_quantity(
    guild_id: int,
    item_key: str,
    quantity: int,
) -> int | None:
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT quantity
            FROM inventory_items_v5
            WHERE guild_id = ?
              AND item_key = ?
            """,
            (guild_id, item_key),
        ).fetchone()

        if row is None:
            return None

        current_quantity = int(row["quantity"])

        if current_quantity < quantity:
            return None

        remaining = current_quantity - quantity

        if remaining == 0:
            connection.execute(
                """
                DELETE FROM inventory_items_v5
                WHERE guild_id = ?
                  AND item_key = ?
                """,
                (guild_id, item_key),
            )
        else:
            connection.execute(
                """
                UPDATE inventory_items_v5
                SET quantity = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE guild_id = ?
                  AND item_key = ?
                """,
                (
                    remaining,
                    guild_id,
                    item_key,
                ),
            )

    return remaining


def clear_all(guild_id: int) -> int:
    with db_session() as connection:
        result = connection.execute(
            """
            DELETE FROM inventory_items_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        )

    return int(result.rowcount)
