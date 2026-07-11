from __future__ import annotations

import asyncio
import contextlib


class CleanupManager:

    async def delete_after(
        self,
        message,
        seconds: int,
    ) -> None:

        async def _worker():

            await asyncio.sleep(seconds)

            with contextlib.suppress(Exception):
                await message.delete()

        asyncio.create_task(_worker())


cleanup_manager = CleanupManager()
