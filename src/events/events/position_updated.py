"""PositionUpdatedEvent — dipublikasi saat posisi berubah setelah sync."""

from uuid import UUID
from src.events.base_event import BaseDomainEvent
from src.core.types.enums import PositionStatus


class PositionUpdatedEvent(BaseDomainEvent):
    event_name: str = "position_updated"
    position_id: UUID
    old_status: PositionStatus
    new_status: PositionStatus
    reason: str