"""Regression tests untuk PortfolioStateManager accounting."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.portfolio.portfolio_state_manager import PortfolioStateManager


def _make_closed_position(rpnl: float):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol="BTC",
        side=Side.LONG,
        status=PositionStatus.CLOSED,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        position_size=0.01,
        opened_at=datetime.now(UTC),
        closed_at=datetime.now(UTC),
        close_reason=PositionCloseReason.MANUAL,
        last_price=51000.0,
        last_updated=datetime.now(UTC),
        realized_pnl=rpnl,
    )


def test_positive_realized_pnl():
    pm = PortfolioStateManager(initial_balance=10000.0)
    pm.repo.save(_make_closed_position(rpnl=200.0))
    pm.set_unrealized_pnl(50.0)

    state = pm.get_state()
    assert state.realized_pnl == 200.0
    assert state.equity == 10250.0
    assert state.drawdown == 0.0


def test_negative_realized_pnl():
    pm = PortfolioStateManager(initial_balance=10000.0)
    pm.repo.save(_make_closed_position(rpnl=-200.0))
    pm.set_unrealized_pnl(-50.0)

    state = pm.get_state()
    assert state.realized_pnl == -200.0
    assert state.equity == 9750.0
    assert state.drawdown == 250.0


def test_no_stale_equity_after_realized_loss():
    pm = PortfolioStateManager(initial_balance=10000.0)
    pm.repo.save(_make_closed_position(rpnl=-100.0))
    pm.set_unrealized_pnl(-20.0)

    state = pm.get_state()
    assert state.realized_pnl == -100.0
    assert state.equity == 9880.0
    assert state.drawdown == 120.0