from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.scheduler.models import (
    JobPriority,
    SchedulerJob,
)
from core.scheduler import repository


class Scheduler:

    def schedule(
        self,
        *,
        guild_id: int,
        job_type: str,
        payload: dict | None = None,
        delay_seconds: int = 0,
        priority: JobPriority = JobPriority.NORMAL,
        repeat: bool = False,
        interval_seconds: int | None = None,
        max_attempts: int = 3,
    ) -> str:

        job = SchedulerJob(
            guild_id=guild_id,
            job_type=job_type,
            payload=payload or {},
            run_at=datetime.now(UTC)
            + timedelta(seconds=delay_seconds),
            priority=priority,
            repeat=repeat,
            interval_seconds=interval_seconds,
            max_attempts=max_attempts,
        )

        return repository.create_job(job)

    def pending(self, limit: int = 25):
        return repository.pending_jobs(limit)

    def claim(self, job_id: int) -> bool:
        return repository.claim_job(job_id)

    def complete(self, job_id: int):
        repository.complete_job(job_id)

    def cancel(self, job_id: int):
        repository.cancel_job(job_id)

    def failed(self, job_id: int, error: str):
        repository.fail_job(job_id, error)


scheduler = Scheduler()
