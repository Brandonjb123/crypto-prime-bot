"""Telegram Bot — menerima pesan, parse command, route."""

from datetime import UTC, datetime

from config.constants import TELEGRAM_ALLOWED_USERS
from src.core.models.telegram import TelegramMessage
from src.core.types.enums import TelegramCommand, TelegramResponseType
from src.telegram.command_handler import (
    help_handler,
    last_signal_handler,
    portfolio_handler,
    positions_handler,
    status_handler,
)
from src.telegram.command_router import CommandRouter
from telegram import Update
from telegram.ext import ContextTypes


class TelegramBot:
    def __init__(self, command_router: CommandRouter | None = None) -> None:
        self.router = command_router or self._default_router()

    async def handle_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming Telegram update."""
        if not update.message or not update.message.text:
            return

        chat_id = str(update.effective_chat.id)
        text = update.message.text.strip()

        # Security
        allowed = TELEGRAM_ALLOWED_USERS
        if allowed and chat_id not in allowed:
            await update.message.reply_text("⛔ Unauthorized")
            return

        command = self._parse_command(text)
        if command is None:
            await update.message.reply_text("Unknown command. Type /help")
            return

        message = TelegramMessage(
            chat_id=chat_id,
            command=command,
            text=text,
            timestamp=datetime.now(UTC),
        )
        response = self.router.route(message)

        if response.response_type == TelegramResponseType.ERROR:
            await update.message.reply_text(f"❌ {response.text}")
        else:
            await update.message.reply_text(response.text)

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