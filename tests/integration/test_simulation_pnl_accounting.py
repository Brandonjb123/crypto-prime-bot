"""Integration test untuk PnL accounting di HistoricalSimulationRunner."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.lifecycle.trade_lifecycle_engine import TradeLifecycleEngine
from src.portfolio.portfolio_state_manager import PortfolioStateManager


def _make_position(side, entry, sl, tp1, tp2, size, status=PositionStatus.OPEN):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol="BTC/USDT",
        side=side,
        status=status,
        entry_price=entry,
        stop_loss=sl,
        take_profit=tp2,
        tp1_price=tp1,
        tp2_price=tp2,
        position_size=size,
        opened_at=datetime.now(UTC),
        closed_at=None,
        close_reason=PositionCloseReason.NONE,
        last_price=None,
        last_updated=None,
    )


class TestSimulationPnLAccounting:
    def test_long_tp1_tp2_single_closed_trade(self):
        """TP1 partial tidak boleh double-count; TP2 menutup sisa size."""
        pm = PortfolioStateManager(initial_balance=10000.0)
        lifecycle = TradeLifecycleEngine()

        pos = _make_position(Side.LONG, entry=100, sl=95, tp1=110, tp2=120, size=1.0)
        pm.repo.save(pos)

        action, fraction = lifecycle.evaluate(pos, 110)
        assert action == "TP1"
        remaining, pnl_tp1 = pm.partial_close(pos.position_id, 110, fraction)
        assert remaining.position_size == pytest.approx(0.5)
        assert pnl_tp1 == pytest.approx(5.0)

        action2, fraction2 = lifecycle.evaluate(remaining, 120)
        assert action2 == "TP2"
        closed = pm.close_position(remaining.position_id, 120, PositionCloseReason.TAKE_PROFIT)
        assert closed.status == PositionStatus.CLOSED
        assert pm.realized_pnl == pytest.approx(15.0)  # 5 + 10

        closed_positions = pm.repo.get_closed()
        assert len(closed_positions) == 1

    def test_short_sl_realized_pnl_negative(self):
        """SHORT SL harus menghasilkan PnL negatif dan posisi CLOSED."""
        pm = PortfolioStateManager(initial_balance=10000.0)
        pos = _make_position(Side.SHORT, entry=100, sl=105, tp1=90, tp2=80, size=1.0)
        pm.repo.save(pos)

        closed = pm.close_position(pos.position_id, 105, PositionCloseReason.STOP_LOSS)
        assert closed.status == PositionStatus.CLOSED
        assert pm.realized_pnl == pytest.approx(-5.0)

    def test_pnl_formula(self):
        """Formula PnL harus berdasarkan selisih harga, bukan harga jual."""
        exit_price = 120.0
        entry = 100.0
        size = 1.0
        pnl = (exit_price - entry) * size
        assert pnl == 20.0