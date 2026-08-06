"""PositionOpenedEvent — dipublikasi saat posisi baru dibuka."""

from uuid import UUID

from src.core.types.enums import Side
from src.events.base_event import BaseDomainEvent


class PositionOpenedEvent(BaseDomainEvent):
    event_name: str = "position_opened"
    position_id: UUID
    symbol: str
    side: Side
    entry_price: float
    position_size: float