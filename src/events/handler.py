"""Event Handler protocol."""

from typing import Any


class EventHandler:
    def handle(self, event: Any) -> None:
        """Handle domain event."""
        ...