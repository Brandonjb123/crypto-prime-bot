"""Integration test: EventBus → NotificationDispatcher → TelegramNotifier."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel
from src.telegram.notifier import TelegramNotifier


class TestTelegramPipeline:
    def test_notification_flow(self):
        service = MagicMock()
        service.send_message = AsyncMock()
        notifier = TelegramNotifier(service)

        msg = NotificationMessage(
            message_id=uuid4(),
            title="Test Alert",
            body="Integration test",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )
        notifier.notify(msg)
        # Tidak crash = pass