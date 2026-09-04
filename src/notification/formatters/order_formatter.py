"""OrderExecutedEvent formatter."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel
from src.events.events.order_executed import OrderExecutedEvent


class OrderExecutedFormatter:
    def format(self, event: OrderExecutedEvent) -> NotificationMessage:
        return NotificationMessage(
            message_id=uuid4(),
            title="Order Executed",
            body=f"{event.symbol} {event.side.value} — {event.status.value}",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )
