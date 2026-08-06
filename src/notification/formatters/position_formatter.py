"""PositionOpenedEvent & PositionClosedEvent formatter."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel
from src.events.events.position_closed import PositionClosedEvent
from src.events.events.position_opened import PositionOpenedEvent


class PositionOpenedFormatter:
    def format(self, event: PositionOpenedEvent) -> NotificationMessage:
        return NotificationMessage(
            message_id=uuid4(),
            title="Position Opened",
            body=f"{event.symbol} {event.side.value}\nEntry: {event.entry_price:.2f}",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )


class PositionClosedFormatter:
    def format(self, event: PositionClosedEvent) -> NotificationMessage:
        return NotificationMessage(
            message_id=uuid4(),
            title="Position Closed",
            body=f"{event.position_id}\nReason: {event.reason.value}",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )