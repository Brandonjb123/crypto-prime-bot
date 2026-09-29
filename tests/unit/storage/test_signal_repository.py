"""Regression tests untuk InMemorySignalRepository."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.core.models.trading_signal import TradingSignal
from src.storage.adapters.in_memory_signal_repository import InMemorySignalRepository


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


class TestSignalRepository:
    def test_append_buy(self):
        repo = InMemorySignalRepository()
        sig = _make_signal(side="BUY")
        repo.append(sig)
        assert repo.latest_by_symbol("BTC") == sig

    def test_append_sell(self):
        repo = InMemorySignalRepository()
        sig = _make_signal(side="SELL")
        repo.append(sig)
        assert repo.latest_by_symbol("BTC").side == "SELL"

    def test_append_wait(self):
        repo = InMemorySignalRepository()
        sig = _make_signal(side="WAIT", status="SKIPPED")
        repo.append(sig)
        assert repo.latest_by_symbol("BTC").status == "SKIPPED"

    def test_append_invalid(self):
        repo = InMemorySignalRepository()
        sig = _make_signal(side="BUY", status="INVALID")
        repo.append(sig)
        assert repo.latest_by_symbol("BTC").status == "INVALID"

    def test_latest_by_symbol_returns_latest(self):
        repo = InMemorySignalRepository()
        sig1 = _make_signal(symbol="BTC", offset_seconds=0)
        sig2 = _make_signal(symbol="BTC", offset_seconds=10)
        repo.append(sig1)
        repo.append(sig2)
        assert repo.latest_by_symbol("BTC") == sig2

    def test_latest_by_symbol_none_if_empty(self):
        repo = InMemorySignalRepository()
        assert repo.latest_by_symbol("BTC") is None

    def test_history_returns_all(self):
        repo = InMemorySignalRepository()
        repo.append(_make_signal(symbol="BTC", offset_seconds=0))
        repo.append(_make_signal(symbol="ETH", offset_seconds=10))
        assert len(repo.history()) == 2

    def test_history_filter_by_symbol(self):
        repo = InMemorySignalRepository()
        repo.append(_make_signal(symbol="BTC", offset_seconds=0))
        repo.append(_make_signal(symbol="ETH", offset_seconds=10))
        repo.append(_make_signal(symbol="BTC", offset_seconds=20))
        btc_history = repo.history(symbol="BTC")
        assert len(btc_history) == 2
        assert all(s.symbol == "BTC" for s in btc_history)

    def test_history_filter_by_since(self):
        repo = InMemorySignalRepository()
        t0 = datetime.now(UTC)
        repo.append(_make_signal(offset_seconds=-100))
        repo.append(_make_signal(offset_seconds=100))
        recent = repo.history(since=t0)
        assert len(recent) == 1

    def test_history_sorted_desc(self):
        repo = InMemorySignalRepository()
        sig_old = _make_signal(offset_seconds=0)
        sig_new = _make_signal(offset_seconds=100)
        repo.append(sig_old)
        repo.append(sig_new)
        history = repo.history()
        assert history[0].created_at > history[1].created_at