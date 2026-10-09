"""Turso-backed NotificationOutbox Repository — read-only ops for C0.0.4A.

Enqueue happens via lifecycle repository atomic batch (not here).
C0.0.4B akan menambah claim/dispatch/retry methods.
"""

from datetime import datetime
from uuid import UUID

from loguru import logger

from src.core.models.notification_outbox import (
    NotificationOutbox,
    OutboxEventType,
    OutboxStatus,
)
from src.storage.adapters.turso_client import TursoClient
from src.storage.repositories.notification_outbox_repository import (
    NotificationOutboxRepository,
)


class TursoNotificationOutboxRepository(NotificationOutboxRepository):
    def __init__(self, client: TursoClient) -> None:
        self.client = client

    def get_pending(self, limit: int = 100) -> list[NotificationOutbox]:
        sql = """
        SELECT * FROM notification_outbox
        WHERE status = ?
        ORDER BY created_at ASC
        LIMIT ?
        """
        result = self.client.execute(
            sql, [OutboxStatus.PENDING.value, limit]
        )
        rows: list[NotificationOutbox] = []
        for row in result.rows:
            try:
                rows.append(
                    self._row_to_outbox(
                        dict(zip(result.columns, row, strict=False))
                    )
                )
            except Exception as e:
                logger.error(f"Failed to deserialize outbox row: {e}, row={row}")
        return rows

    def count_pending(self) -> int:
        sql = "SELECT COUNT(*) FROM notification_outbox WHERE status = ?"
        result = self.client.execute(sql, [OutboxStatus.PENDING.value])
        return int(result.rows[0][0]) if result.rows else 0

    def _row_to_outbox(self, row: dict) -> NotificationOutbox:
        return NotificationOutbox(
            id=int(row["id"]),
            signal_id=UUID(row["signal_id"]),
            event_type=OutboxEventType(row["event_type"]),
            telegram_id=int(row["telegram_id"]),
            status=OutboxStatus(row["status"]),
            attempts=int(row["attempts"]),
            sent_at=(
                datetime.fromisoformat(row["sent_at"])
                if row.get("sent_at")
                else None
            ),
            message_id=(
                int(row["message_id"])
                if row.get("message_id") is not None
                else None
            ),
            last_error=row.get("last_error"),
            next_retry_at=(
                datetime.fromisoformat(row["next_retry_at"])
                if row.get("next_retry_at")
                else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )