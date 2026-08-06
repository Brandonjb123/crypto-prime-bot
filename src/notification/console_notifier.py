"""Console Notifier — print notification ke terminal."""

from src.core.models.notification import NotificationMessage
from src.notification.base_notifier import BaseNotifier


class ConsoleNotifier(BaseNotifier):
    def notify(self, message: NotificationMessage) -> None:
        prefix = {
            "INFO": "[INFO]",
            "WARNING": "[WARNING]",
            "ERROR": "[ERROR]",
        }.get(message.level, "[INFO]")

        print(f"{prefix} {message.title}\n{message.body}\n")