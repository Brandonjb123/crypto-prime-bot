"""NotificationOutbox repository interface — dedicated persistence boundary."""

from abc import ABC, abstractmethod

from src.core.models.notification_outbox import NotificationOutbox


class NotificationOutboxRepository(ABC):
    @abstractmethod
    def get_pending(self, limit: int = 100) -> list[NotificationOutbox]:
        """Return PENDING outbox rows, oldest first. For dispatcher (C0.0.4B)."""
        ...

    @abstractmethod
    def count_pending(self) -> int:
        """Count PENDING rows. For observability."""
        ...