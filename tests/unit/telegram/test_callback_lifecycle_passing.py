"""Direct callback tests untuk lifecycle state passing (H3.2 R2)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.core.models.lifecycle_lookup import (
    LifecycleLookupResult,
    LifecycleRecord,
)
from src.telegram.bot import TelegramBot
from src.telegram.lifecycle_display import LIFECYCLE_EPOCH_UTC

FUTURE = datetime.now(UTC) + timedelta(hours=1)
PRE_EPOCH = LIFECYCLE_EPOCH_UTC - timedelta(days=1)


def _make_signal(status="ACTIVE", created_at=None):
    sig = MagicMock()
    sig.signal_id = uuid4()
    sig.symbol = "BTC"
    sig.side = "BUY"
    sig.status = status
    sig.entry_price = 100.0
    sig.stop_loss = 95.0
    sig.take_profit = 110.0
    sig.confidence = 80
    sig.risk_level = "MEDIUM"
    sig.position_size = 1.0
    sig.created_at = created_at or datetime.now(UTC)
    return sig


def _make_lifecycle_repo(records=None, failed=None, raises=False):
    repo = MagicMock()
    if raises:
        repo.get_lifecycle_lookup.side_effect = RuntimeError("db down")
        return repo
    records = records or {}
    failed = failed or set()

    def _lookup(signal_ids):
        found = {sid: records[sid] for sid in signal_ids if sid in records}
        fail = {sid for sid in signal_ids if sid in failed}
        absent = {sid for sid in signal_ids if sid not in found and sid not in fail}
        return LifecycleLookupResult(found=found, absent=absent, failed=fail)

    repo.get_lifecycle_lookup.side_effect = _lookup
    return repo


def _make_bot(signal=None, lifecycle_records=None, lifecycle_raises=False):
    bot = TelegramBot()
    runtime = MagicMock()
    runtime.get_context.return_value = {
        "positions": [],
        "closed_positions": [],
        "portfolio_snapshot": None,
    }
    runtime.price_provider = object()
    bot.set_runtime_provider(runtime)

    sig = signal if signal is not None else _make_signal()

    sig_repo = MagicMock()
    sig_repo.latest_by_symbol.return_value = sig
    sig_repo.history.return_value = [sig] if sig is not None else []

    lc_repo = _make_lifecycle_repo(
        records=lifecycle_records or {}, raises=lifecycle_raises
    )

    bot.set_signal_repository(sig_repo)
    bot.set_signal_lifecycle_repository(lc_repo)
    bot.set_context(
        {
            "positions": [],
            "closed_positions": [],
            "portfolio_snapshot": None,
            "signal_repository": sig_repo,
            "signal_lifecycle_repository": lc_repo,
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
    async def test_passes_active_state(self, monkeypatch):
        sig = _make_signal()
        bot = _make_bot(
            signal=sig,
            lifecycle_records={
                sig.signal_id: LifecycleRecord(sig.signal_id, "ACTIVE", FUTURE)
            },
        )

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        await bot.handle_callback(_make_callback_update("menu_signals"), None)
        assert captured["lifecycle_map"][sig.signal_id] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_passes_expired_state(self, monkeypatch):
        sig = _make_signal()
        bot = _make_bot(
            signal=sig,
            lifecycle_records={
                sig.signal_id: LifecycleRecord(sig.signal_id, "EXPIRED", None)
            },
        )

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        await bot.handle_callback(_make_callback_update("menu_signals"), None)
        assert captured["lifecycle_map"][sig.signal_id] == "EXPIRED"

    @pytest.mark.asyncio
    async def test_legacy_state_when_pre_epoch_no_row(self, monkeypatch):
        sig = _make_signal(created_at=PRE_EPOCH)
        bot = _make_bot(signal=sig, lifecycle_records={})

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        await bot.handle_callback(_make_callback_update("menu_signals"), None)
        assert captured["lifecycle_map"][sig.signal_id] == "LEGACY"

    @pytest.mark.asyncio
    async def test_unknown_on_query_failure(self, monkeypatch):
        sig = _make_signal()
        bot = _make_bot(signal=sig, lifecycle_raises=True)

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        await bot.handle_callback(_make_callback_update("menu_signals"), None)
        assert captured["lifecycle_map"][sig.signal_id] == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_refresh_signals_also_passes_lifecycle_map(self, monkeypatch):
        sig = _make_signal()
        bot = _make_bot(
            signal=sig,
            lifecycle_records={
                sig.signal_id: LifecycleRecord(sig.signal_id, "EXPIRED", None)
            },
        )

        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signals, *, lifecycle_map=None):
            captured["lifecycle_map"] = lifecycle_map
            return "SUMMARY"

        monkeypatch.setattr(bot_module, "format_signals_summary", _spy)

        await bot.handle_callback(_make_callback_update("refresh_signals"), None)
        assert captured["lifecycle_map"][sig.signal_id] == "EXPIRED"


class TestViewLastSignalPassesLifecycleState:
    def _run(self, monkeypatch, bot):
        import src.telegram.bot as bot_module

        captured = {}

        def _spy(signal, *, lifecycle_state="UNKNOWN"):
            captured["lifecycle_state"] = lifecycle_state
            return "CARD"

        monkeypatch.setattr(bot_module, "format_signal_card", _spy)
        bot._view_last_signal()
        return captured

    def test_active(self, monkeypatch):
        sig = _make_signal()
        bot = _make_bot(
            signal=sig,
            lifecycle_records={
                sig.signal_id: LifecycleRecord(sig.signal_id, "ACTIVE", FUTURE)
            },
        )
        assert self._run(monkeypatch, bot)["lifecycle_state"] == "ACTIVE"

    def test_expired(self, monkeypatch):
        sig = _make_signal()
        bot = _make_bot(
            signal=sig,
            lifecycle_records={
                sig.signal_id: LifecycleRecord(sig.signal_id, "EXPIRED", None)
            },
        )
        assert self._run(monkeypatch, bot)["lifecycle_state"] == "EXPIRED"

    def test_unknown_on_query_failure(self, monkeypatch):
        sig = _make_signal()
        bot = _make_bot(signal=sig, lifecycle_raises=True)
        assert self._run(monkeypatch, bot)["lifecycle_state"] == "UNKNOWN"

    def test_legacy_pre_epoch_no_row(self, monkeypatch):
        sig = _make_signal(created_at=PRE_EPOCH)
        bot = _make_bot(signal=sig, lifecycle_records={})
        assert self._run(monkeypatch, bot)["lifecycle_state"] == "LEGACY"


class TestViewLastSignalSkippedInvalidBypass:
    """R9: callback last-signal SKIPPED/INVALID must not trigger lookup."""

    def _build_bot(self, sig):
        bot = TelegramBot()
        runtime = MagicMock()
        runtime.get_context.return_value = {
            "positions": [],
            "closed_positions": [],
            "portfolio_snapshot": None,
        }
        runtime.price_provider = object()
        bot.set_runtime_provider(runtime)

        sig_repo = MagicMock()
        sig_repo.latest_by_symbol.return_value = sig
        sig_repo.history.return_value = [sig]

        probe = MagicMock()

        def _must_not_call(signal_ids):
            raise AssertionError("lifecycle lookup must not be called")

        probe.get_lifecycle_lookup.side_effect = _must_not_call

        bot.set_signal_repository(sig_repo)
        bot.set_signal_lifecycle_repository(probe)
        bot.set_context(
            {
                "positions": [],
                "closed_positions": [],
                "portfolio_snapshot": None,
                "signal_repository": sig_repo,
                "signal_lifecycle_repository": probe,
            }
        )
        return bot, probe

    def test_skipped_bypasses_lookup(self):
        sig = _make_signal(status="SKIPPED")
        bot, probe = self._build_bot(sig)
        text, _ = bot._view_last_signal()
        assert probe.get_lifecycle_lookup.call_count == 0
        assert "lifecycle state unavailable" not in text
        assert "STALE" not in text
        assert "LEGACY" not in text

    def test_invalid_bypasses_lookup(self):
        sig = _make_signal(status="INVALID")
        bot, probe = self._build_bot(sig)
        text, _ = bot._view_last_signal()
        assert probe.get_lifecycle_lookup.call_count == 0
        assert "lifecycle state unavailable" not in text
        assert "STALE" not in text
        assert "LEGACY" not in text