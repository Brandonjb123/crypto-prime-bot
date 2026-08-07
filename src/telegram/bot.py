"""Telegram Bot — menerima pesan, parse command, route."""

from datetime import UTC, datetime

from config.constants import TELEGRAM_ALLOWED_USERS
from src.core.models.telegram import TelegramMessage, TelegramResponse
from src.core.types.enums import TelegramCommand, TelegramResponseType
from src.telegram.command_handler import (
    help_handler,
    last_signal_handler,
    portfolio_handler,
    positions_handler,
    status_handler,
)
from src.telegram.command_router import CommandRouter


class TelegramBot:
    def __init__(self, command_router: CommandRouter | None = None) -> None:
        self.router = command_router or self._default_router()

    def handle_message(self, text: str, chat_id: str) -> TelegramResponse:
        # Security check — baca langsung dari config
        allowed = TELEGRAM_ALLOWED_USERS
        if allowed and chat_id not in allowed:
            return TelegramResponse(
                response_type=TelegramResponseType.ERROR,
                text="⛔ Unauthorized",
                timestamp=datetime.now(UTC),
            )

        command = self._parse_command(text)
        if command is None:
            return TelegramResponse(
                response_type=TelegramResponseType.UNKNOWN,
                text="Unknown command. Type /help",
                timestamp=datetime.now(UTC),
            )

        message = TelegramMessage(
            chat_id=chat_id,
            command=command,
            text=text,
            timestamp=datetime.now(UTC),
        )
        return self.router.route(message)

    def _parse_command(self, text: str) -> TelegramCommand | None:
        text = text.strip().lower()
        try:
            return TelegramCommand(text.replace("/", ""))
        except ValueError:
            return None

    def _default_router(self) -> CommandRouter:
        router = CommandRouter()
        router.register(TelegramCommand.STATUS, lambda msg: status_handler(msg))
        router.register(TelegramCommand.POSITIONS, lambda msg: positions_handler(msg))
        router.register(TelegramCommand.PORTFOLIO, lambda msg: portfolio_handler(msg))
        router.register(TelegramCommand.LAST_SIGNAL, lambda msg: last_signal_handler(msg))
        router.register(TelegramCommand.HELP, lambda msg: help_handler(msg))
        return router
