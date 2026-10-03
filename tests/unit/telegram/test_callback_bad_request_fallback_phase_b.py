"""Test handle_callback BadRequest fallback — konsisten dengan handle_update."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.error import BadRequest

from src.telegram.bot import TelegramBot


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


class TestCallbackBadRequestFallback:
    @pytest.mark.asyncio
    async def test_callback_falls_back_on_bad_request(self) -> None:
        """Kalau edit_message_text dengan Markdown raise BadRequest,
        harus retry tanpa parse_mode."""
        bot = _make_bot()
        update = _make_callback_update("menu_portfolio")

        # Panggilan pertama raise, panggilan kedua (fallback) sukses
        update.callback_query.edit_message_text = AsyncMock(
            side_effect=[
                BadRequest("Can't parse entities"),
                None,
            ]
        )

        await bot.handle_callback(update, None)

        # Harus dipanggil 2x
        assert update.callback_query.edit_message_text.await_count == 2

        # Call pertama: parse_mode="Markdown"
        first = update.callback_query.edit_message_text.await_args_list[0]
        assert first.kwargs.get("parse_mode") == "Markdown"

        # Call kedua: tanpa parse_mode
        second = update.callback_query.edit_message_text.await_args_list[1]
        assert second.kwargs.get("parse_mode") is None

    @pytest.mark.asyncio
    async def test_callback_menu_back_falls_back_on_bad_request(self) -> None:
        bot = _make_bot()
        update = _make_callback_update("menu_back")

        update.callback_query.edit_message_text = AsyncMock(
            side_effect=[
                BadRequest("Can't parse entities"),
                None,
            ]
        )

        await bot.handle_callback(update, None)
        assert update.callback_query.edit_message_text.await_count == 2

    @pytest.mark.asyncio
    async def test_callback_text_handler_falls_back_on_bad_request(self) -> None:
        bot = _make_bot()
        update = _make_callback_update("menu_help")

        update.callback_query.edit_message_text = AsyncMock(
            side_effect=[
                BadRequest("Can't parse entities"),
                None,
            ]
        )

        await bot.handle_callback(update, None)
        assert update.callback_query.edit_message_text.await_count == 2