from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel
from src.telegram.notifier import TelegramNotifier


class TestTelegramNotifier:
    def test_send_message(self):
        received = []
        notifier = TelegramNotifier(send_func=lambda msg: received.append(msg))
        msg = NotificationMessage(
            message_id=uuid4(),
            title="Test",
            body="Hello",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )
        notifier.notify(msg)
        assert len(received) == 1
        assert received[0].title == "Test"

    def test_multiple_messages(self):
        received = []
        notifier = TelegramNotifier(send_func=lambda msg: received.append(msg))
        for i in range(3):
            notifier.notify(
                NotificationMessage(
                    message_id=uuid4(),
                    title=f"Test {i}",
                    body="body",
                    level=NotificationLevel.INFO,
                    timestamp=datetime.now(UTC),
                )
            )
        assert len(received) == 3
