from __future__ import annotations

import json
from datetime import UTC, datetime

from core.database import db_session
from core.scheduler.models import SchedulerJob


def create_job(job: SchedulerJob) -> str:
    with db_session() as con:
        con.execute(
            """
            INSERT INTO scheduler_jobs_v5(
                job_uuid,
                guild_id,
                job_type,
                payload_json,
                run_at,
                interval_seconds,
                repeat,
                priority,
                max_attempts
            )
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                job.job_uuid,
                job.guild_id,
                job.job_type,
                json.dumps(job.payload),
                job.run_at.isoformat(),
                job.interval_seconds,
                int(job.repeat),
                int(job.priority),
                job.max_attempts,
            ),
        )

    return job.job_uuid


def pending_jobs(limit: int = 25):
    with db_session() as con:
        return con.execute(
            """
            SELECT *
            FROM scheduler_jobs_v5
            WHERE status='pending'
              AND run_at<=?
            ORDER BY priority DESC,id ASC
            LIMIT ?
            """,
            (
                datetime.now(UTC).isoformat(),
                limit,
            ),
        ).fetchall()


def claim_job(job_id: int) -> bool:
    with db_session() as con:
        cur = con.execute(
            """
            UPDATE scheduler_jobs_v5
            SET status='running',
                attempts=attempts+1,
                locked_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
              AND status='pending'
            """,
            (job_id,),
        )

    return cur.rowcount == 1


def complete_job(job_id: int):
    with db_session() as con:
        con.execute(
            """
            UPDATE scheduler_jobs_v5
            SET status='completed',
                finished_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (job_id,),
        )


def cancel_job(job_id: int):
    with db_session() as con:
        con.execute(
            """
            UPDATE scheduler_jobs_v5
            SET status='cancelled',
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (job_id,),
        )


def fail_job(job_id: int, error: str):
    with db_session() as con:
        con.execute(
            """
            UPDATE scheduler_jobs_v5
            SET status='failed',
                last_error=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                error[:2000],
                job_id,
            ),
        )
