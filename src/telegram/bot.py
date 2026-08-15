"""Telegram Bot — menerima pesan, parse command, handle callback."""

from datetime import UTC, datetime

from config.constants import TELEGRAM_ALLOWED_USERS
from src.core.models.telegram import TelegramMessage
from src.core.types.enums import TelegramCommand, TelegramResponseType
from src.telegram.command_handler import (
    help_handler,
    last_signal_handler,
    portfolio_handler,
    positions_handler,
    start_handler,
    status_handler,
)
from src.telegram.command_router import CommandRouter
from src.telegram.keyboards import BACK_MENU, MAIN_MENU
from telegram import Update
from telegram.ext import ContextTypes


class TelegramBot:
    def __init__(self, command_router: CommandRouter | None = None) -> None:
        self.router = command_router or self._default_router()
        self.context = {}

    def set_context(self, context: dict) -> None:
        self.context = context

    async def handle_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return

        chat_id = str(update.effective_chat.id)
        text = update.message.text.strip()

        allowed = TELEGRAM_ALLOWED_USERS
        if allowed and chat_id not in allowed:
            await update.message.reply_text("⛔ Unauthorized")
            return

        command = self._parse_command(text)
        if command is None:
            await update.message.reply_text("Unknown command. Type /help")
            return

        if command == TelegramCommand.START:
            response = start_handler(None, self.context)
            await update.message.reply_text(
                response.text,
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
            return

        message = TelegramMessage(
            chat_id=chat_id,
            command=command,
            text=text,
            timestamp=datetime.now(UTC),
        )
        response = self.router.route(message, self.context)

        if response.response_type == TelegramResponseType.ERROR:
            await update.message.reply_text(f"❌ {response.text}")
        else:
            await update.message.reply_text(response.text, parse_mode="Markdown")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "menu_back":
            from src.telegram.command_handler import start_handler
            resp = start_handler(None, self.context)
            await query.edit_message_text(
                resp.text,
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
            return

        # Map callback ke response text
        handler_map = {
            "menu_market": "market_handler",
            "menu_signals": "last_signal_handler",
            "menu_portfolio": "portfolio_handler",
            "menu_positions": "positions_handler",
            "menu_performance": "performance_handler",
            "menu_status": "status_handler",
            "menu_help": "help_handler",
        }

        handler_name = handler_map.get(data)
        if handler_name:
            # Panggil handler yang sesuai
            if handler_name == "market_handler":
                from src.telegram.command_handler import market_handler
                resp = market_handler(None, self.context)
            elif handler_name == "last_signal_handler":
                from src.telegram.command_handler import last_signal_handler
                resp = last_signal_handler(None, self.context)
            elif handler_name == "portfolio_handler":
                from src.telegram.command_handler import portfolio_handler
                resp = portfolio_handler(None, self.context)
            elif handler_name == "positions_handler":
                from src.telegram.command_handler import positions_handler
                resp = positions_handler(None, self.context)
            elif handler_name == "performance_handler":
                from src.telegram.command_handler import performance_handler
                resp = performance_handler(None, self.context)
            elif handler_name == "status_handler":
                from src.telegram.command_handler import status_handler
                resp = status_handler(None, self.context)
            elif handler_name == "help_handler":
                from src.telegram.command_handler import help_handler
                resp = help_handler(None, self.context)

            await query.edit_message_text(
                resp.text,
                parse_mode="Markdown",
                reply_markup=BACK_MENU,
            )

    def _parse_command(self, text: str) -> TelegramCommand | None:
        text = text.strip().lower()
        # Alias: /lastsignal → /last_signal (enum menggunakan underscore)
        if text == "/lastsignal":
            text = "/last_signal"
        try:
            return TelegramCommand(text.replace("/", ""))
        except ValueError:
            return None

    def _default_router(self) -> CommandRouter:
        router = CommandRouter()
        router.register(TelegramCommand.STATUS, lambda msg, ctx=None: status_handler(msg, ctx))
        router.register(TelegramCommand.POSITIONS, lambda msg, ctx=None: positions_handler(msg, ctx))
        router.register(TelegramCommand.PORTFOLIO, lambda msg, ctx=None: portfolio_handler(msg, ctx))
        router.register(TelegramCommand.LAST_SIGNAL, lambda msg, ctx=None: last_signal_handler(msg, ctx))
        router.register(TelegramCommand.HELP, lambda msg, ctx=None: help_handler(msg, ctx))
        return router