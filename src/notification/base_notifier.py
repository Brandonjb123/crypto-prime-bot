"""Base Notifier interface."""

from abc import ABC, abstractmethod

from src.core.models.notification import NotificationMessage


class BaseNotifier(ABC):
    @abstractmethod
    def notify(self, message: NotificationMessage) -> None:
        """Kirim notifikasi."""
        ...