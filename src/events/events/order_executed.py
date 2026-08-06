"""OrderExecutedEvent — dipublikasi saat order FILLED."""

from uuid import UUID

from src.core.types.enums import OrderStatus, Side
from src.events.base_event import BaseDomainEvent


class OrderExecutedEvent(BaseDomainEvent):
    event_name: str = "order_executed"
    execution_id: UUID
    order_id: UUID
    status: OrderStatus
    symbol: str
    side: Side