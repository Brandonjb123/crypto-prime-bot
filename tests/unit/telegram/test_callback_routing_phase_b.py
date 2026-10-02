"""Phase B callback routing tests.

Verify callbacks use shared read/use-case + card formatter,
NOT command handlers.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.telegram.bot import TelegramBot
from src.telegram.keyboards import (
    HISTORY_MENU,
    MAIN_MENU,
    PORTFOLIO_MENU,
    POSITIONS_MENU,
    SIGNALS_MENU,
    TRACKRECORD_MENU,
)


def _make_bot():
    bot = TelegramBot()
    runtime = MagicMock()
    runtime.get_context.return_value = {
        "positions": [],
        "closed_positions": [],
        "portfolio_snapshot": None,
    }
    runtime.price_provider = object()  # sentinel for identity test
    bot.set_runtime_provider(runtime)

    # Signal repo fake: history() returns empty list → read_last_signal returns None
    signal_repo = MagicMock()
    signal_repo.history.return_value = []
    signal_repo.latest_by_symbol.return_value = None
    bot.set_signal_repository(signal_repo)
    return bot, runtime


def _make_callback_update(data: str):
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update


def _get_reply_markup(update):
    """Ambil reply_markup dari call terakhir edit_message_text."""
    call = update.callback_query.edit_message_text.await_args
    return call.kwargs.get("reply_markup")


class TestPortfolioCallbacks:
    @pytest.mark.asyncio
    async def test_menu_portfolio_uses_portfolio_menu(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("menu_portfolio")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is PORTFOLIO_MENU

    @pytest.mark.asyncio
    async def test_refresh_portfolio_same_view(self) -> None:
        bot, runtime = _make_bot()
        update = _make_callback_update("refresh_portfolio")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is PORTFOLIO_MENU
        assert runtime.get_context.called

    @pytest.mark.asyncio
    async def test_menu_portfolio_does_not_call_portfolio_handler(
        self, monkeypatch
    ) -> None:
        called = {"value": False}

        def _spy(msg, ctx):
            called["value"] = True
            raise AssertionError("portfolio_handler should not be called")

        monkeypatch.setattr(
            "src.telegram.bot.portfolio_handler", _spy
        )
        bot, _ = _make_bot()
        update = _make_callback_update("menu_portfolio")
        await bot.handle_callback(update, None)
        assert called["value"] is False


class TestPositionsCallbacks:
    @pytest.mark.asyncio
    async def test_menu_positions_uses_positions_menu(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("menu_positions")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is POSITIONS_MENU

    @pytest.mark.asyncio
    async def test_refresh_positions_same_view(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("refresh_positions")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is POSITIONS_MENU

    @pytest.mark.asyncio
    async def test_menu_positions_does_not_call_positions_handler(
        self, monkeypatch
    ) -> None:
        called = {"value": False}

        def _spy(msg, ctx):
            called["value"] = True
            raise AssertionError("positions_handler should not be called")

        monkeypatch.setattr(
            "src.telegram.bot.positions_handler", _spy
        )
        bot, _ = _make_bot()
        update = _make_callback_update("menu_positions")
        await bot.handle_callback(update, None)
        assert called["value"] is False


class TestHistoryCallbacks:
    @pytest.mark.asyncio
    async def test_menu_history_uses_history_menu(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("menu_history")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is HISTORY_MENU

    @pytest.mark.asyncio
    async def test_refresh_history_same_view(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("refresh_history")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is HISTORY_MENU

    @pytest.mark.asyncio
    async def test_menu_history_does_not_call_history_handler(
        self, monkeypatch
    ) -> None:
        called = {"value": False}

        def _spy(msg, ctx):
            called["value"] = True
            raise AssertionError("history_handler should not be called")

        monkeypatch.setattr(
            "src.telegram.bot.history_handler", _spy
        )
        bot, _ = _make_bot()
        update = _make_callback_update("menu_history")
        await bot.handle_callback(update, None)
        assert called["value"] is False


class TestTrackRecordCallbacks:
    @pytest.mark.asyncio
    async def test_menu_trackrecord_uses_trackrecord_menu(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("menu_trackrecord")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is TRACKRECORD_MENU

    @pytest.mark.asyncio
    async def test_refresh_trackrecord_same_view(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("refresh_trackrecord")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is TRACKRECORD_MENU

    @pytest.mark.asyncio
    async def test_menu_trackrecord_does_not_call_trackrecord_handler(
        self, monkeypatch
    ) -> None:
        called = {"value": False}

        def _spy(msg, ctx):
            called["value"] = True
            raise AssertionError("trackrecord_handler should not be called")

        monkeypatch.setattr(
            "src.telegram.bot.trackrecord_handler", _spy
        )
        bot, _ = _make_bot()
        update = _make_callback_update("menu_trackrecord")
        await bot.handle_callback(update, None)
        assert called["value"] is False


class TestSignalsCallbacks:
    @pytest.mark.asyncio
    async def test_menu_signals_uses_signals_menu(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("menu_signals")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is SIGNALS_MENU

    @pytest.mark.asyncio
    async def test_refresh_signals_uses_signals_menu(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("refresh_signals")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is SIGNALS_MENU


class TestBackNavigation:
    @pytest.mark.asyncio
    async def test_menu_back_returns_main_menu(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("menu_back")
        await bot.handle_callback(update, None)
        assert _get_reply_markup(update) is MAIN_MENU


class TestTextCallbacks:
    @pytest.mark.asyncio
    async def test_menu_help_still_works(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("menu_help")
        await bot.handle_callback(update, None)
        # reply_markup = BACK_MENU (existing behavior)
        call = update.callback_query.edit_message_text.await_args
        assert call.kwargs.get("reply_markup") is not None

    @pytest.mark.asyncio
    async def test_menu_status_still_works(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("menu_status")
        await bot.handle_callback(update, None)
        # Should not crash
        assert update.callback_query.edit_message_text.await_count == 1


class TestUnknownCallback:
    @pytest.mark.asyncio
    async def test_unknown_callback_returns_error_answer(self) -> None:
        bot, _ = _make_bot()
        update = _make_callback_update("totally_unknown_data")
        await bot.handle_callback(update, None)
        # query.answer dipanggil 2x: yang awal + error message
        assert update.callback_query.answer.await_count == 2


class TestContextLifecycle:
    @pytest.mark.asyncio
    async def test_callback_refreshes_context(self) -> None:
        bot, runtime = _make_bot()
        update = _make_callback_update("menu_portfolio")
        await bot.handle_callback(update, None)
        assert runtime.get_context.called

    @pytest.mark.asyncio
    async def test_price_provider_identity_preserved(self) -> None:
        bot, runtime = _make_bot()
        sentinel = object()
        runtime.price_provider = sentinel
        update = _make_callback_update("menu_portfolio")
        await bot.handle_callback(update, None)
        assert bot.context.get("price_provider") is sentinel