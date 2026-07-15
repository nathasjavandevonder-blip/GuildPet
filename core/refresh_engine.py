from __future__ import annotations

import asyncio
import weakref

import discord


class DashboardRefreshEngine:
    """Serializes refreshes per guild to prevent overlapping message edits."""

    def __init__(self) -> None:
        self._locks: weakref.WeakValueDictionary[int, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )

    def _lock_for(self, guild_id: int) -> asyncio.Lock:
        lock = self._locks.get(guild_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[guild_id] = lock
        return lock

    async def refresh(self, guild: discord.Guild):
        from ui.panel_manager import _refresh_main_panel_unlocked

        async with self._lock_for(guild.id):
            return await _refresh_main_panel_unlocked(guild)


refresh_engine = DashboardRefreshEngine()
