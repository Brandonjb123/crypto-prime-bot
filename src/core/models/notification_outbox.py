"""Notification outbox model — C0.0.4A.

Immutable event row. Bukan menggantikan TradingSignal atau SignalLifecycle.

Schema alignment: id INTEGER AUTOINCREMENT sebagai PK. telegram_id INTEGER.
Enum status/event_type tidak punya CHECK constraint di DB (validasi di aplikasi).
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OutboxEventType(StrEnum):
    NEW_SIGNAL = "NEW_SIGNAL"
    REPLACEMENT = "REPLACEMENT"
    EXPIRY = "EXPIRY"


class OutboxStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"


class NotificationOutbox(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    signal_id: UUID
    event_type: OutboxEventType
    telegram_id: int
    status: OutboxStatus
    attempts: int
    sent_at: datetime | None = None
    message_id: int | None = None
    last_error: str | None = None
    next_retry_at: datetime | None = None
    created_at: datetime
    updated_at: datetime