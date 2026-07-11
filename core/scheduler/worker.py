from __future__ import annotations

import asyncio
import logging

from core.scheduler.queue import scheduler

log = logging.getLogger(__name__)


class SchedulerWorker:

    def __init__(self):
        self._running = False

    async def start(self):
        self._running = True

        log.info("Scheduler worker started")

        while self._running:

            jobs = scheduler.pending(25)

            for job in jobs:

                if not scheduler.claim(job["id"]):
                    continue

                try:

                    log.info(
                        "Executing scheduler job %s (%s)",
                        job["id"],
                        job["job_type"],
                    )

                    #
                    # Dispatcher integration will be added next sprint.
                    #

                    scheduler.complete(job["id"])

                except Exception as exc:

                    scheduler.failed(
                        job["id"],
                        str(exc),
                    )

                    log.exception(
                        "Scheduler job failed"
                    )

            await asyncio.sleep(1)

    async def stop(self):
        self._running = False


scheduler_worker = SchedulerWorker()
