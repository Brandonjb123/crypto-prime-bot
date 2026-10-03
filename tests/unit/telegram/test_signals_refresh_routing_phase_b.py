"""Regression test — refresh_signals harus render summary, bukan single card."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.telegram.bot import TelegramBot
from src.telegram.keyboards import SIGNALS_MENU


def _make_bot():
    bot = TelegramBot()
    runtime = MagicMock()
    runtime.get_context.return_value = {
        "positions": [],
        "closed_positions": [],
        "portfolio_snapshot": None,
    }
    runtime.price_provider = object()
    bot.set_runtime_provider(runtime)

    signal_repo = MagicMock()
    signal_repo.latest_by_symbol.return_value = None
    signal_repo.history.return_value = []
    bot.set_signal_repository(signal_repo)
    return bot


def _make_callback_update(data: str):
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update


class TestSignalsRefreshRouting:
    @pytest.mark.asyncio
    async def test_menu_signals_uses_summary_view(self, monkeypatch) -> None:
        called = {"summary": False, "card": False}

        import src.telegram.bot as bot_module

        def _spy_summary(signals):
            called["summary"] = True
            return "SUMMARY"

        def _spy_card(signal):
            called["card"] = True
            return "CARD"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy_summary)
        monkeypatch.setattr(bot_module, "format_signal_card", _spy_card)

        bot = _make_bot()
        update = _make_callback_update("menu_signals")
        await bot.handle_callback(update, None)

        assert called["summary"] is True
        assert called["card"] is False

    @pytest.mark.asyncio
    async def test_refresh_signals_uses_summary_view_not_card(
        self, monkeypatch
    ) -> None:
        """refresh_signals harus refresh view yang sama (summary), bukan card."""
        called = {"summary": False, "card": False}

        import src.telegram.bot as bot_module

        def _spy_summary(signals):
            called["summary"] = True
            return "SUMMARY"

        def _spy_card(signal):
            called["card"] = True
            return "CARD"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy_summary)
        monkeypatch.setattr(bot_module, "format_signal_card", _spy_card)

        bot = _make_bot()
        update = _make_callback_update("refresh_signals")
        await bot.handle_callback(update, None)

        assert called["summary"] is True
        assert called["card"] is False

    @pytest.mark.asyncio
    async def test_menu_signals_uses_signals_menu_keyboard(self) -> None:
        bot = _make_bot()
        update = _make_callback_update("menu_signals")
        await bot.handle_callback(update, None)
        call = update.callback_query.edit_message_text.await_args
        assert call.kwargs.get("reply_markup") is SIGNALS_MENU

    @pytest.mark.asyncio
    async def test_refresh_signals_uses_signals_menu_keyboard(self) -> None:
        bot = _make_bot()
        update = _make_callback_update("refresh_signals")
        await bot.handle_callback(update, None)
        call = update.callback_query.edit_message_text.await_args
        assert call.kwargs.get("reply_markup") is SIGNALS_MENU

    @pytest.mark.asyncio
    async def test_refresh_signals_does_not_recurse(self) -> None:
        """Callback tidak boleh rekursif ke command handler."""
        bot = _make_bot()
        update = _make_callback_update("refresh_signals")
        await bot.handle_callback(update, None)
        # No crash, no recursion
        assert update.callback_query.edit_message_text.await_count == 1