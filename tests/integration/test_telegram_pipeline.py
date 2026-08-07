"""Integration test: EventBus → NotificationDispatcher → TelegramNotifier."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel
from src.telegram.notifier import TelegramNotifier


class TestTelegramPipeline:
    def test_notification_flow(self):
        received = []
        notifier = TelegramNotifier(send_func=lambda msg: received.append(msg))

        msg = NotificationMessage(
            message_id=uuid4(),
            title="Test Alert",
            body="Integration test",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )
        notifier.notify(msg)
        assert len(received) == 1
        assert received[0].title == "Test Alert"
