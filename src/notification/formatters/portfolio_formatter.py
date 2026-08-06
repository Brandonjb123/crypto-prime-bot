"""PortfolioUpdatedEvent formatter."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel
from src.events.events.portfolio_updated import PortfolioUpdatedEvent


class PortfolioUpdatedFormatter:
    def format(self, event: PortfolioUpdatedEvent) -> NotificationMessage:
        return NotificationMessage(
            message_id=uuid4(),
            title="Portfolio Updated",
            body=f"Equity: {event.equity:.2f}\nGross Exposure: {event.gross_exposure:.2f}",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )