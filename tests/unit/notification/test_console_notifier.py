"""Unit tests untuk ConsoleNotifier."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.notification import NotificationMessage
from src.core.types.enums import NotificationLevel
from src.notification.console_notifier import ConsoleNotifier


class TestConsoleNotifier:
    def test_notify_info(self, capsys):
        notifier = ConsoleNotifier()
        msg = NotificationMessage(
            message_id=uuid4(),
            title="Test Info",
            body="This is a test",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(UTC),
        )
        notifier.notify(msg)
        captured = capsys.readouterr()
        assert "[INFO] Test Info" in captured.out

    def test_multiple_notify(self, capsys):
        notifier = ConsoleNotifier()
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
        captured = capsys.readouterr()
        assert captured.out.count("[INFO]") == 3
