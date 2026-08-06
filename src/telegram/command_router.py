"""Command Router — registry-based."""

from datetime import datetime, UTC
from src.core.models.telegram import TelegramMessage, TelegramResponse
from src.core.types.enums import TelegramCommand, TelegramResponseType


class CommandRouter:
    def __init__(self) -> None:
        self._handlers: dict[TelegramCommand, callable] = {}

    def register(self, command: TelegramCommand, handler: callable) -> None:
        self._handlers[command] = handler

    def route(self, message: TelegramMessage) -> TelegramResponse:
        handler = self._handlers.get(message.command)
        if handler is None:
            return TelegramResponse(
                response_type=TelegramResponseType.UNKNOWN,
                text=f"Unknown command: {message.command.value}",
                timestamp=datetime.now(UTC),
            )
        return handler(message)