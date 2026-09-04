"""Integration test: Portfolio lifecycle (open → update → close)."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import PositionStatus
from src.portfolio.portfolio_state_manager import PortfolioStateManager


def _make_signal(**overrides):
    defaults = dict(
        signal_id=uuid4(),
        symbol="ETH",
        side="BUY",
        status="ACTIVE",
        entry_price=3000.0,
        stop_loss=2800.0,
        take_profit=3500.0,
        position_size=0.1,
        risk_percent=2.0,
        confidence=80,
        risk_level="MEDIUM",
        reasoning=["test"],
        created_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    return TradingSignal(**defaults)


class TestPortfolioLifecycle:
    def test_full_lifecycle(self):
        pm = PortfolioStateManager(initial_balance=5000.0)

        # OPEN
        signal = _make_signal()
        pos = pm.open_position(signal)
        assert pos is not None
        assert pos.status == PositionStatus.OPEN

        # UPDATE price
        pnl = pm.update_price(pos.position_id, 3100.0)
        assert pnl == 10.0  # (3100 - 3000) * 0.1

        # CLOSE
        closed = pm.close_position(pos.position_id, 3200.0)
        assert closed is not None
        assert closed.status == PositionStatus.CLOSED

        # Verify final state
        state = pm.get_state()
        # realized = (3200 - 3000) * 0.1 = 20.0
        assert state.realized_pnl == 20.0
        assert state.equity == 5020.0
        assert state.open_positions == 0
        assert state.closed_positions == 1
        assert state.drawdown == 0.0