from datetime import UTC, datetime

from core.database import db_session
from core.dispatcher import (
    NotificationPriority,
    NotificationStatus,
    notification_queue,
)


def clean_test_data(guild_id: int) -> None:
    with db_session() as connection:
        connection.execute(
            """
            DELETE FROM notification_history_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        )

        connection.execute(
            """
            DELETE FROM notification_dead_letters_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        )

        connection.execute(
            """
            DELETE FROM notification_queue_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        )


def main() -> None:
    guild_id = 990010
    clean_test_data(guild_id)

    low_id = notification_queue.enqueue(
        guild_id=guild_id,
        notification_type="test.low",
        title="Low Priority",
        description="Low priority test.",
        priority=NotificationPriority.LOW,
    )

    high_id = notification_queue.enqueue(
        guild_id=guild_id,
        notification_type="test.high",
        title="High Priority",
        description="High priority test.",
        priority=NotificationPriority.HIGH,
        delete_after_seconds=30,
        refresh_panel=True,
    )

    assert notification_queue.pending_count(guild_id) == 2

    claimed = notification_queue.claim("test-worker")

    assert claimed is not None
    assert claimed.notification_id == high_id
    assert claimed.status == NotificationStatus.PROCESSING
    assert claimed.attempts == 1
    assert claimed.refresh_panel is True
    assert claimed.delete_after_seconds == 30

    notification_queue.delivered(
        claimed,
        discord_message_id=123456,
    )

    delivered = notification_queue.get(high_id)

    assert delivered is not None
    assert delivered.status == NotificationStatus.DELIVERED

    second = notification_queue.claim("test-worker")

    assert second is not None
    assert second.notification_id == low_id

    result = notification_queue.failed(
        second,
        error=RuntimeError("Test failure"),
    )

    assert result == "retry"

    retried = notification_queue.get(low_id)

    assert retried is not None
    assert retried.status == NotificationStatus.RETRY

    print("First claimed:", claimed.title)
    print("Second result:", result)
    print(
        "Remaining pending:",
        notification_queue.pending_count(guild_id),
    )
    print("V5 dispatcher core test passed.")


if __name__ == "__main__":
    main()
