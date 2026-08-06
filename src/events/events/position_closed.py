"""PositionClosedEvent — dipublikasi saat posisi ditutup."""

from uuid import UUID

from src.core.types.enums import PositionCloseReason
from src.events.base_event import BaseDomainEvent


class PositionClosedEvent(BaseDomainEvent):
    event_name: str = "position_closed"
    position_id: UUID
    reason: PositionCloseReason
    exit_price: float | None = None