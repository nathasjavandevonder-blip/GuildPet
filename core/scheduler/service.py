from __future__ import annotations

import asyncio

from core.scheduler.worker import scheduler_worker

_scheduler_task = None


async def start_scheduler():

    global _scheduler_task

    if _scheduler_task is None:

        _scheduler_task = asyncio.create_task(
            scheduler_worker.start()
        )


async def stop_scheduler():

    global _scheduler_task

    if _scheduler_task is None:
        return

    await scheduler_worker.stop()

    await _scheduler_task

    _scheduler_task = None
