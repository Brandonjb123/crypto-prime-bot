from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, UTC
from uuid import uuid4
from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel
from src.telegram.notifier import TelegramNotifier


class TestTelegramNotifier:
    def test_send_message(self):
        service = MagicMock()
        service.send_message = AsyncMock()
        notifier = TelegramNotifier(service)

        msg = NotificationMessage(
            message_id=uuid4(),
            title="Test", body="Hello",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )
        notifier.notify(msg)
        # Tidak crash = pass

    def test_multiple_messages(self):
        service = MagicMock()
        service.send_message = AsyncMock()
        notifier = TelegramNotifier(service)

        for i in range(3):
            notifier.notify(NotificationMessage(
                message_id=uuid4(),
                title=f"Test {i}", body="body",
                level=NotificationLevel.INFO,
                timestamp=datetime.now(UTC),
            ))
        # Tidak crash = pass