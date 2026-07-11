from __future__ import annotations

from core.dispatcher.cleanup import cleanup_manager
from core.dispatcher.refresh import refresh_manager
from core.dispatcher.sender import discord_sender


class DispatcherService:

    async def dispatch(
        self,
        *,
        channel,
        notification,
        embed=None,
        view=None,
    ):

        message = await discord_sender.send(
            channel=channel,
            embed=embed,
            view=view,
        )

        if notification.delete_after_seconds:

            await cleanup_manager.delete_after(
                message,
                notification.delete_after_seconds,
            )

        if notification.refresh_panel:

            await refresh_manager.refresh_panel(
                notification.guild_id,
            )

        return message


dispatcher = DispatcherService()
