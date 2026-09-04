"""Unit tests untuk PnL Engine."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.market.pnl_engine import calculate_unrealized


def _make_position(symbol="BTC/USDT", side=Side.LONG, entry=50000.0, size=0.1):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol=symbol,
        side=side,
        status=PositionStatus.OPEN,
        entry_price=entry,
        stop_loss=48000.0,
        take_profit=55000.0,
        position_size=size,
        opened_at=datetime.now(UTC),
        closed_at=None,
        close_reason=PositionCloseReason.NONE,
    )


class TestPnLEngine:
    def test_long_pnl_positive(self):
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 51000.0)
        pos = _make_position("BTC/USDT", Side.LONG, 50000.0, 0.1)
        pnl = calculate_unrealized([pos], provider)
        assert pnl == pytest.approx(100.0)  # (51000-50000)*0.1

    def test_long_pnl_negative(self):
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 49000.0)
        pos = _make_position("BTC/USDT", Side.LONG, 50000.0, 0.1)
        pnl = calculate_unrealized([pos], provider)
        assert pnl == pytest.approx(-100.0)

    def test_short_pnl_positive(self):
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 49000.0)
        pos = _make_position("BTC/USDT", Side.SHORT, 50000.0, 0.1)
        pnl = calculate_unrealized([pos], provider)
        assert pnl == pytest.approx(100.0)  # (50000-49000)*0.1

    def test_short_pnl_negative(self):
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 51000.0)
        pos = _make_position("BTC/USDT", Side.SHORT, 50000.0, 0.1)
        pnl = calculate_unrealized([pos], provider)
        assert pnl == pytest.approx(-100.0)

    def test_mixed_positions(self):
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 51000.0)
        provider.update_price("ETH/USDT", 3000.0)
        positions = [
            _make_position("BTC/USDT", Side.LONG, 50000.0, 0.1),  # +100
            _make_position("ETH/USDT", Side.SHORT, 3200.0, 0.5),  # +100
        ]
        pnl = calculate_unrealized(positions, provider)
        assert pnl == pytest.approx(200.0)

    def test_missing_price_returns_zero(self):
        provider = InMemoryPriceProvider()
        pos = _make_position("BTC/USDT", Side.LONG, 50000.0, 0.1)
        pnl = calculate_unrealized([pos], provider)
        assert pnl == 0.0

    def test_skip_closed_positions(self):
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 51000.0)
        pos = _make_position("BTC/USDT", Side.LONG, 50000.0, 0.1)
        # Ubah status ke CLOSED
        closed_pos = Position(
            position_id=pos.position_id,
            execution_id=pos.execution_id,
            order_id=pos.order_id,
            symbol=pos.symbol,
            side=pos.side,
            status=PositionStatus.CLOSED,
            entry_price=pos.entry_price,
            stop_loss=pos.stop_loss,
            take_profit=pos.take_profit,
            position_size=pos.position_size,
            opened_at=pos.opened_at,
            closed_at=datetime.now(UTC),
            close_reason=PositionCloseReason.MANUAL,
        )
        pnl = calculate_unrealized([closed_pos], provider)
        assert pnl == 0.0

    def test_deterministic(self):
        provider1 = InMemoryPriceProvider()
        provider2 = InMemoryPriceProvider()
        provider1.update_price("BTC/USDT", 51000.0)
        provider2.update_price("BTC/USDT", 51000.0)
        pos = _make_position()
        assert calculate_unrealized([pos], provider1) == calculate_unrealized([pos], provider2)
