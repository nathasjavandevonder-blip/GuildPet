from __future__ import annotations

import discord

from core.database import db_session
from ui.main_panel import build_main_embed
from ui.view_manager import build_view


def get_panel_record(guild_id: int):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT guild_id, channel_id, message_id
            FROM guild_main_panels_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()


def save_panel(
    guild_id: int,
    channel_id: int,
    message_id: int,
) -> None:
    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO guild_main_panels_v5 (
                guild_id,
                channel_id,
                message_id,
                updated_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (guild_id)
            DO UPDATE SET
                channel_id = excluded.channel_id,
                message_id = excluded.message_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                guild_id,
                channel_id,
                message_id,
            ),
        )


def remove_panel_record(guild_id: int) -> None:
    with db_session() as connection:
        connection.execute(
            """
            DELETE FROM guild_main_panels_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        )


async def _resolve_channel(
    guild: discord.Guild,
    channel_id: int,
):
    channel = guild.get_channel(channel_id)

    if channel is not None:
        return channel

    try:
        return await guild.fetch_channel(channel_id)
    except (
        discord.NotFound,
        discord.Forbidden,
        discord.HTTPException,
    ):
        return None


async def delete_registered_panel(
    guild: discord.Guild,
) -> None:
    record = get_panel_record(guild.id)

    if record is None:
        return

    channel = await _resolve_channel(
        guild,
        int(record["channel_id"]),
    )

    if channel is not None:
        try:
            message = await channel.fetch_message(
                int(record["message_id"])
            )
            await message.delete()
        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
            AttributeError,
        ):
            pass

    remove_panel_record(guild.id)


async def move_main_panel_to_bottom(
    guild: discord.Guild,
    channel,
) -> discord.Message:
    if channel is None:
        raise ValueError("A Discord channel is required.")

    await delete_registered_panel(guild)

    message = await channel.send(
        embed=build_main_embed(guild.id),
        view=build_view(guild.id),
    )

    save_panel(
        guild.id,
        channel.id,
        message.id,
    )

    return message


async def _refresh_main_panel_unlocked(
    guild: discord.Guild,
) -> discord.Message | None:
    record = get_panel_record(guild.id)

    if record is None:
        return None

    channel = await _resolve_channel(
        guild,
        int(record["channel_id"]),
    )

    if channel is None:
        remove_panel_record(guild.id)
        return None

    try:
        message = await channel.fetch_message(
            int(record["message_id"])
        )

        await message.edit(
            embed=build_main_embed(guild.id),
            view=build_view(guild.id),
        )

        return message

    except discord.NotFound:
        remove_panel_record(guild.id)
        return None
    except (
        discord.Forbidden,
        discord.HTTPException,
        AttributeError,
    ):
        return None


async def refresh_main_panel_in_place(
    guild: discord.Guild,
) -> discord.Message | None:
    """Refresh through the per-guild coordinator to avoid overlapping edits."""
    from core.refresh_engine import refresh_engine

    return await refresh_engine.refresh(guild)


async def restore_registered_panels(
    bot: discord.Client,
) -> None:
    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT guild_id, channel_id, message_id
            FROM guild_main_panels_v5
            """
        ).fetchall()

    restored = 0
    removed = 0

    for row in rows:
        guild_id = int(row["guild_id"])
        message_id = int(row["message_id"])

        guild = bot.get_guild(guild_id)

        if guild is None:
            continue

        try:
            bot.add_view(
                build_view(guild_id),
                message_id=message_id,
            )
            restored += 1
        except Exception as exc:
            print(
                f"Could not restore panel for guild "
                f"{guild_id}: {exc}"
            )
            removed += 1

    print(
        f"Restored {restored} registered v5 panel view(s). "
        f"Failed: {removed}."
    )
