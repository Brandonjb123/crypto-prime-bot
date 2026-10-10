"""Direct callback tests untuk lifecycle state passing (H3.2 GAP-1).

Memverifikasi bahwa callback/handler meneruskan lifecycle_map/state
yang benar ke formatter — bukan hanya tidak crash.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.telegram.bot import TelegramBot


def _make_signal(signal_id=None, symbol="BTC", status="ACTIVE"):
    sig = MagicMock()
    sig.signal_id = signal_id or uuid4()
    sig.symbol = symbol
    sig.side = "BUY"
    sig.status = status
    sig.entry_price = 100.0
    sig.stop_loss = 95.0
    sig.take_profit = 110.0
    sig.confidence = 80
    sig.risk_level = "MEDIUM"
    sig.position_size = 1.0
    return sig


def _make_bot(signals=None, lifecycle_map=None, lifecycle_raises=False):
    bot = TelegramBot()
    runtime = MagicMock()
    runtime.get_context.return_value = {
        "positions": [],
        "closed_positions": [],
        "portfolio_snapshot": None,
    }
    runtime.price_provider = object()
    bot.set_runtime_provider(runtime)

    sig = signals if signals is not None else _make_signal()

    repo = MagicMock()
    repo.latest_by_symbol.return_value = sig
    repo.history.return_value = [sig] if sig is not None else []

    if lifecycle_raises:
        repo.get_lifecycle_states.side_effect = RuntimeError("db down")
    else:
        repo.get_lifecycle_states.return_value = lifecycle_map or {}

    bot.set_signal_repository(repo)

    # Set context dengan signal_repository — karena _view_last_signal
    # dibaca langsung dari self.context, bukan via handle_callback.
    bot.set_context(
        {
            "positions": [],
            "closed_positions": [],
            "portfolio_snapshot": None,
            "signal_repository": repo,
        }
    )
    return bot


def _make_callback_update(data: str):
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update


class TestViewSignalsPassesLifecycleMap:
    @pytest.mark.asyncio
    async def test_passes_nonempty_map_with_active_state(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(
            signals=sig,
            lifecycle_map={sig.signal_id: "ACTIVE"},
        )

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["signals"] = signals
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        update = _make_callback_update("menu_signals")
        await bot.handle_callback(update, None)

        assert captured["lifecycle_map"] is not None
        assert captured["lifecycle_map"] != {}
        assert captured["lifecycle_map"][sig.signal_id] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_passes_expired_state(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(
            signals=sig,
            lifecycle_map={sig.signal_id: "EXPIRED"},
        )

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        update = _make_callback_update("menu_signals")
        await bot.handle_callback(update, None)

        assert captured["lifecycle_map"][sig.signal_id] == "EXPIRED"

    @pytest.mark.asyncio
    async def test_legacy_state_when_no_lifecycle_row(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(signals=sig, lifecycle_map={})

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        update = _make_callback_update("menu_signals")
        await bot.handle_callback(update, None)

        assert captured["lifecycle_map"][sig.signal_id] == "LEGACY"

    @pytest.mark.asyncio
    async def test_unknown_state_on_query_failure(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(signals=sig, lifecycle_raises=True)

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        update = _make_callback_update("menu_signals")
        await bot.handle_callback(update, None)

        assert captured["lifecycle_map"][sig.signal_id] == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_refresh_signals_also_passes_lifecycle_map(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(
            signals=sig,
            lifecycle_map={sig.signal_id: "EXPIRED"},
        )

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        update = _make_callback_update("refresh_signals")
        await bot.handle_callback(update, None)

        assert captured["lifecycle_map"][sig.signal_id] == "EXPIRED"


class TestViewLastSignalPassesLifecycleState:
    def test_passes_active_state(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(
            signals=sig,
            lifecycle_map={sig.signal_id: "ACTIVE"},
        )

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signal, *, lifecycle_state="UNKNOWN"):
            captured["lifecycle_state"] = lifecycle_state
            return "CARD"

        monkeypatch.setattr(bot_module, "format_signal_card", _spy)

        bot._view_last_signal()

        assert captured["lifecycle_state"] == "ACTIVE"

    def test_passes_expired_state(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(
            signals=sig,
            lifecycle_map={sig.signal_id: "EXPIRED"},
        )

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signal, *, lifecycle_state="UNKNOWN"):
            captured["lifecycle_state"] = lifecycle_state
            return "CARD"

        monkeypatch.setattr(bot_module, "format_signal_card", _spy)

        bot._view_last_signal()

        assert captured["lifecycle_state"] == "EXPIRED"

    def test_unknown_on_query_failure(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(signals=sig, lifecycle_raises=True)

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signal, *, lifecycle_state="UNKNOWN"):
            captured["lifecycle_state"] = lifecycle_state
            return "CARD"

        monkeypatch.setattr(bot_module, "format_signal_card", _spy)

        bot._view_last_signal()

        assert captured["lifecycle_state"] == "UNKNOWN"

    def test_legacy_when_no_row(self, monkeypatch):
        sig = _make_signal(status="ACTIVE")
        bot = _make_bot(signals=sig, lifecycle_map={})

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signal, *, lifecycle_state="UNKNOWN"):
            captured["lifecycle_state"] = lifecycle_state
            return "CARD"

        monkeypatch.setattr(bot_module, "format_signal_card", _spy)

        bot._view_last_signal()

        assert captured["lifecycle_state"] == "LEGACY"