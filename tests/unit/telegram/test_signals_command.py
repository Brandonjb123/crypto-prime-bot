"""Regression tests untuk /signals dan /lastsignal semantics."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.application.scheduler import DEFAULT_SYMBOLS
from src.core.models.trading_signal import TradingSignal
from src.storage.adapters.in_memory_signal_repository import InMemorySignalRepository
from src.telegram.command_handler import last_signal_handler, signals_handler


def _make_signal(symbol="BTC", side="BUY", status="ACTIVE", offset_seconds=0):
    return TradingSignal(
        signal_id=uuid4(),
        symbol=symbol,
        side=side,
        status=status,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        take_profit_1=51000.0,
        take_profit_2=52000.0,
        position_size=0.01,
        risk_percent=1.0,
        confidence=80,
        risk_level="MEDIUM",
        reasoning=["test"],
        created_at=datetime.now(UTC) + timedelta(seconds=offset_seconds),
    )


class TestSignalsHandlerSemantics:
    def test_empty_repository(self):
        repo = InMemorySignalRepository()
        resp = signals_handler(None, {"signal_repository": repo})
        assert "Belum ada sinyal" in resp.text

    def test_no_repository_in_context(self):
        resp = signals_handler(None, {})
        assert "Belum ada sinyal" in resp.text

    def test_returns_latest_per_symbol(self):
        repo = InMemorySignalRepository()
        repo.append(_make_signal(symbol="BTC", offset_seconds=0))
        repo.append(_make_signal(symbol="ETH", offset_seconds=10))
        repo.append(_make_signal(symbol="SOL", offset_seconds=20))

        resp = signals_handler(None, {"signal_repository": repo})

        assert "BTC" in resp.text
        assert "ETH" in resp.text
        assert "SOL" in resp.text

    def test_older_signal_replaced_in_view_but_kept_in_history(self):
        repo = InMemorySignalRepository()
        btc_old = _make_signal(symbol="BTC", side="BUY", offset_seconds=0)
        btc_new = _make_signal(symbol="BTC", side="SELL", offset_seconds=100)
        repo.append(btc_old)
        repo.append(btc_new)

        resp = signals_handler(None, {"signal_repository": repo})

        # View: hanya latest (SELL)
        assert "SELL" in resp.text
        # History: keduanya tetap ada
        history = repo.history(symbol="BTC")
        assert len(history) == 2

    def test_only_tracked_symbols_shown(self):
        repo = InMemorySignalRepository()
        repo.append(_make_signal(symbol="BTC", offset_seconds=0))
        repo.append(_make_signal(symbol="UNTRACKED_COIN", offset_seconds=10))

        resp = signals_handler(None, {"signal_repository": repo})

        assert "BTC" in resp.text
        assert "UNTRACKED_COIN" not in resp.text

    def test_matches_default_symbols_universe(self):
        """Sanity check: DEFAULT_SYMBOLS di-import dari scheduler, bukan hardcode."""
        assert isinstance(DEFAULT_SYMBOLS, list)
        assert len(DEFAULT_SYMBOLS) >= 9
        assert "BTC" in DEFAULT_SYMBOLS


class TestLastSignalHandlerSemantics:
    def test_returns_single_newest_global(self):
        repo = InMemorySignalRepository()
        repo.append(_make_signal(symbol="BTC", offset_seconds=0))
        repo.append(_make_signal(symbol="ETH", offset_seconds=100))  # terbaru
        repo.append(_make_signal(symbol="SOL", offset_seconds=50))

        resp = last_signal_handler(None, {"signal_repository": repo})

        # Terbaru = ETH
        assert "ETH" in resp.text
        # Tidak semua symbol di-show
        assert "BTC" not in resp.text or "SOL" not in resp.text

    def test_empty_repository(self):
        repo = InMemorySignalRepository()
        resp = last_signal_handler(None, {"signal_repository": repo})
        assert "Belum ada sinyal" in resp.text