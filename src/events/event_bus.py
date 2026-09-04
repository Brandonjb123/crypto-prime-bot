"""Event Bus — synchronous, in-memory, deterministic."""

from collections.abc import Callable

from src.events.base_event import BaseDomainEvent

Handler = Callable[[BaseDomainEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    def register(self, event_name: str, handler: Handler) -> None:
        """Register handler untuk event tertentu."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def unregister(self, event_name: str, handler: Handler) -> None:
        """Unregister handler dari event tertentu."""
        if event_name in self._handlers:
            self._handlers[event_name].remove(handler)

    def publish(self, event: BaseDomainEvent) -> None:
        """
        Dispatch event ke semua handler yang terdaftar.
        FIFO sesuai urutan registrasi.
        Tanpa subscriber → no-op (tidak error).
        Handler exception → dicatat, tidak menghentikan dispatch.
        """
        handlers = self._handlers.get(event.event_name, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Log exception — tidak boleh menghentikan dispatch
                pass
