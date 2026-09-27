"""Regression tests untuk Markdown safety di /history dan handle_update."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from telegram.error import BadRequest

from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.telegram.command_handler import history_handler


def _make_closed_position(
    close_reason: PositionCloseReason,
    symbol: str = "BTC/USDT",
    side: Side = Side.LONG,
    entry: float = 50000.0,
    exit_price: float = 51000.0,
    pnl: float = 100.0,
):
    """Helper: buat Position CLOSED untuk testing handler."""
    from src.core.models.position import Position

    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol=symbol,
        side=side,
        status=PositionStatus.CLOSED,
        entry_price=entry,
        stop_loss=entry * 0.95,
        take_profit=entry * 1.10,
        tp1_price=entry * 1.05,
        tp2_price=entry * 1.10,
        position_size=0.01,
        opened_at=datetime.now(UTC),
        closed_at=datetime.now(UTC),
        close_reason=close_reason,
        last_price=exit_price,
        last_updated=datetime.now(UTC),
        realized_pnl=pnl,
    )


class TestHistoryHandlerMarkdownSafety:
    def test_stop_loss_no_raw_underscore(self):
        """STOP_LOSS tidak boleh muncul sebagai STOP_LOSS mentah di output."""
        pos = _make_closed_position(PositionCloseReason.STOP_LOSS)
        resp = history_handler(None, {"closed_positions": [pos]})
        assert "_" not in resp.text
        assert "STOP LOSS" in resp.text

    def test_take_profit_no_raw_underscore(self):
        pos = _make_closed_position(PositionCloseReason.TAKE_PROFIT, pnl=200.0)
        resp = history_handler(None, {"closed_positions": [pos]})
        assert "_" not in resp.text
        assert "TAKE PROFIT" in resp.text

    def test_mixed_odd_underscore_count(self):
        """Kombinasi 3 trade dengan jumlah underscore ganjil tidak boleh break."""
        positions = [
            _make_closed_position(PositionCloseReason.STOP_LOSS),
            _make_closed_position(PositionCloseReason.MANUAL),
            _make_closed_position(PositionCloseReason.STOP_LOSS),
        ]
        resp = history_handler(None, {"closed_positions": positions})
        assert "_" not in resp.text

    def test_bold_header_still_present(self):
        """*Riwayat Trading Paper* tetap ada (bold header tidak rusak)."""
        pos = _make_closed_position(PositionCloseReason.STOP_LOSS)
        resp = history_handler(None, {"closed_positions": [pos]})
        assert resp.text.startswith("📜 *Riwayat Trading Paper*")

    def test_empty_history_no_underscore(self):
        resp = history_handler(None, {"closed_positions": []})
        assert resp.text == "📜 *Riwayat Trading Paper*\n\nBelum ada closed trade."

    def test_all_close_reasons_no_underscore(self):
        """Loop semua enum value, pastikan tidak ada '_' yang bocor."""
        for reason in PositionCloseReason:
            pos = _make_closed_position(reason)
            resp = history_handler(None, {"closed_positions": [pos]})
            assert "_" not in resp.text, f"underscore bocor untuk reason={reason}"


class TestHandleUpdateMarkdownFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_bad_request(self, monkeypatch):
        """Kalau parse_mode Markdown gagal, harus fallback ke plain text."""
        from unittest.mock import AsyncMock, MagicMock

        from src.telegram.bot import TelegramBot

        bot = TelegramBot()
        bot.set_context({})

        mock_update = MagicMock()
        mock_update.message.text = "/history"
        mock_update.message.chat.id = 123
        mock_update.effective_chat.id = 123
        mock_update.effective_user.id = 123

        # Panggilan pertama raise BadRequest, panggilan kedua (fallback) sukses
        mock_update.message.reply_text = AsyncMock(
            side_effect=[
                BadRequest("Can't parse entities"),
                None,
            ]
        )

        # Minimal context yang valid untuk history_handler
        bot.context = {"closed_positions": []}

        await bot.handle_update(mock_update, None)

        # Harus dipanggil 2x: pertama dengan parse_mode, kedua tanpa
        assert mock_update.message.reply_text.await_count == 2
        first_kwargs = mock_update.message.reply_text.await_args_list[0].kwargs
        second_kwargs = mock_update.message.reply_text.await_args_list[1].kwargs
        assert first_kwargs.get("parse_mode") == "Markdown"
        assert "parse_mode" not in second_kwargs or second_kwargs.get("parse_mode") is None