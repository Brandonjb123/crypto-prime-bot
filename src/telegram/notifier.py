"""Telegram Notifier — mengirim notifikasi via Telegram (console simulation)."""

from src.core.models.notification import NotificationMessage
from src.notification.base_notifier import BaseNotifier


class TelegramNotifier(BaseNotifier):
    def __init__(self, send_func=None) -> None:
        self.send_func = send_func or (lambda msg: print(f"[Telegram] {msg.title}: {msg.body}"))

    def notify(self, message: NotificationMessage) -> None:
        self.send_func(message)
