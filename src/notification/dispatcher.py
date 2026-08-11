"""Notification Dispatcher — registry-based, pilih formatter otomatis."""

from src.core.models.notification import NotificationMessage
from src.events.base_event import BaseDomainEvent
from src.notification.base_notifier import BaseNotifier


class NotificationDispatcher:
    def __init__(self, notifier: BaseNotifier) -> None:
        self.notifier = notifier
        self._registry: dict[type, object] = {}

    def register(self, event_type: type, formatter: object) -> None:
        """Register formatter untuk event type tertentu."""
        self._registry[event_type] = formatter

    def dispatch(self, event: BaseDomainEvent) -> None:
        """Pilih formatter berdasarkan type(event), kirim notifikasi."""
        formatter = self._registry.get(type(event))
        if formatter is not None:
            message = formatter.format(event)
            self.notifier.notify(message)
        # Unknown event → ignore silently (no exception)

    def dispatch_message(self, message: NotificationMessage) -> None:
        """Kirim NotificationMessage langsung ke notifier."""
        self.notifier.notify(message)    
