"""Telegram Bot — menerima pesan, parse command, handle callback."""

from datetime import UTC, datetime

from loguru import logger

from config.constants import TELEGRAM_ALLOWED_USERS
from src.application.scheduler import DEFAULT_SYMBOLS
from src.core.models.telegram import TelegramMessage
from src.core.types.enums import TelegramCommand, TelegramResponseType
from src.telegram.command_handler import (
    checkout_handler,
    help_handler,
    history_handler,
    last_signal_handler,
    portfolio_handler,
    positions_handler,
    privacy_handler,
    risk_handler,
    signals_handler,
    start_handler,
    status_handler,
    subscribe_handler,
    subscription_status_handler,
    terms_handler,
    trackrecord_handler,
)
from src.telegram.command_router import CommandRouter
from src.telegram.formatter import (
    format_history_card,
    format_portfolio_card,
    format_positions_card,
    format_signal_card,
    format_signals_summary,
    format_trackrecord_card,
)
from src.telegram.keyboards import (
    BACK_MENU,
    HISTORY_MENU,
    MAIN_MENU,
    PORTFOLIO_MENU,
    POSITIONS_MENU,
    SIGNALS_MENU,
    TRACKRECORD_MENU,
)
from src.telegram.use_cases import (
    read_history,
    read_last_signal,
    read_latest_signals,
    read_portfolio,
    read_positions_with_metrics,
    read_trackrecord,
)
from telegram import InlineKeyboardMarkup, Update
from telegram.error import BadRequest
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

        if hasattr(self, "runtime_provider") and self.runtime_provider:
            self.context = self.runtime_provider.get_context()
            # Expose existing price provider (same instance) to context
            if hasattr(self.runtime_provider, "price_provider"):
                self.context["price_provider"] = self.runtime_provider.price_provider

        if hasattr(self, "signal_repository") and self.signal_repository:
            self.context["signal_repository"] = self.signal_repository    

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
            try:
                await update.message.reply_text(f"❌ {response.text}")
            except BadRequest as e:
                logger.warning(f"Markdown parse failed on error response, falling back: {e}")
                await update.message.reply_text(f"❌ {response.text}")
        else:
            try:
                await update.message.reply_text(response.text, parse_mode="Markdown")
            except BadRequest as e:
                logger.warning(
                    f"Markdown parse failed (command={command}), "
                    f"falling back to plain text: {e}"
                )
                await update.message.reply_text(response.text)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        data = query.data

        # Refresh context (Step 2 behavior, unchanged)
        if hasattr(self, "runtime_provider") and self.runtime_provider:
            self.context = self.runtime_provider.get_context()
            if hasattr(self.runtime_provider, "price_provider"):
                self.context["price_provider"] = self.runtime_provider.price_provider

        if hasattr(self, "signal_repository") and self.signal_repository:
            self.context["signal_repository"] = self.signal_repository

        # Root navigation
        if data == "menu_back":
            resp = start_handler(None, self.context)
            await query.edit_message_text(
                resp.text,
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
            return

        # Card views — read/use-case + card formatter + dedicated keyboard
        view_map = {
            "menu_portfolio": self._view_portfolio,
            "refresh_portfolio": self._view_portfolio,
            "menu_positions": self._view_positions,
            "refresh_positions": self._view_positions,
            "menu_history": self._view_history,
            "refresh_history": self._view_history,
            "menu_trackrecord": self._view_trackrecord,
            "refresh_trackrecord": self._view_trackrecord,
            "menu_signals": self._view_signals,
            "refresh_signals": self._view_last_signal,
        }
        view = view_map.get(data)
        if view is not None:
            text, keyboard = view()
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            return

        # Text-only callbacks — reuse existing handlers
        text_handler_map = {
            "menu_help": help_handler,
            "menu_status": subscription_status_handler,
            "menu_subscribe": subscribe_handler,
        }
        text_handler = text_handler_map.get(data)
        if text_handler is not None:
            resp = text_handler(None, self.context)
            await query.edit_message_text(
                resp.text,
                parse_mode="Markdown",
                reply_markup=BACK_MENU,
            )
            return

        await query.answer("❌ Tombol tidak dikenali.")

    # ---------- Phase B card view functions ----------

    def _view_portfolio(self) -> tuple[str, InlineKeyboardMarkup]:
        snapshot = read_portfolio(self.context)
        return format_portfolio_card(snapshot), PORTFOLIO_MENU

    def _view_positions(self) -> tuple[str, InlineKeyboardMarkup]:
        metrics_list = read_positions_with_metrics(self.context)
        if not metrics_list:
            return format_positions_card([]), POSITIONS_MENU
        positions = [m["position"] for m in metrics_list]
        metrics_map = {m["position"].position_id: m for m in metrics_list}
        return (
            format_positions_card(positions, metrics_map=metrics_map),
            POSITIONS_MENU,
        )

    def _view_history(self) -> tuple[str, InlineKeyboardMarkup]:
        closed = read_history(self.context)
        return format_history_card(closed), HISTORY_MENU

    def _view_trackrecord(self) -> tuple[str, InlineKeyboardMarkup]:
        summary = read_trackrecord(self.context)
        return format_trackrecord_card(summary), TRACKRECORD_MENU

    def _view_signals(self) -> tuple[str, InlineKeyboardMarkup]:
        signals = read_latest_signals(self.context, DEFAULT_SYMBOLS)
        return format_signals_summary(signals), SIGNALS_MENU

    def _view_last_signal(self) -> tuple[str, InlineKeyboardMarkup]:
        sig = read_last_signal(self.context)
        return format_signal_card(sig), SIGNALS_MENU

    def _parse_command(self, text: str) -> TelegramCommand | None:
        text = text.strip().lower()
        # Alias /lastsignal -> /last_signal (enum menggunakan underscore)
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
        router.register(TelegramCommand.SIGNALS, lambda msg, ctx=None: signals_handler(msg, ctx))
        router.register(TelegramCommand.HISTORY, lambda msg, ctx=None: history_handler(msg, ctx))
        router.register(TelegramCommand.TRACKRECORD, lambda msg, ctx=None: trackrecord_handler(msg, ctx))
        router.register(TelegramCommand.SUBSCRIBE, lambda msg, ctx=None: subscribe_handler(msg, ctx))
        router.register(TelegramCommand.CHECKOUT, lambda msg, ctx=None: checkout_handler(msg, ctx))
        router.register(TelegramCommand.TERMS, lambda msg, ctx=None: terms_handler(msg, ctx))
        router.register(TelegramCommand.PRIVACY, lambda msg, ctx=None: privacy_handler(msg, ctx))
        router.register(TelegramCommand.RISK, lambda msg, ctx=None: risk_handler(msg, ctx))
        router.register(TelegramCommand.SUBSCRIPTION_STATUS, lambda msg, ctx=None: subscription_status_handler(msg, ctx))
        router.register(TelegramCommand.HELP, lambda msg, ctx=None: help_handler(msg, ctx))
        return router

    def set_runtime_provider(self, provider):
        self.runtime_provider = provider

    def set_signal_repository(self, signal_repository) -> None:
        self.signal_repository = signal_repository    