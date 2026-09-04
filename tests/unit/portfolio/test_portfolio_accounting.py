"""Regression tests untuk PortfolioStateManager accounting."""

from src.portfolio.portfolio_state_manager import PortfolioStateManager


def test_positive_realized_pnl():
    pm = PortfolioStateManager(initial_balance=10000.0)
    pm.realized_pnl = 200.0
    pm.set_unrealized_pnl(50.0)

    state = pm.get_state()
    assert state.equity == 10250.0
    assert state.drawdown == 0.0
    assert state.peak_equity == 10250.0


def test_negative_realized_pnl():
    pm = PortfolioStateManager(initial_balance=10000.0)
    pm.realized_pnl = -200.0
    pm.set_unrealized_pnl(-50.0)

    state = pm.get_state()
    assert state.equity == 9750.0
    assert state.drawdown == 250.0


def test_open_positions_included():
    pm = PortfolioStateManager(initial_balance=10000.0)
    pm.set_unrealized_pnl(30.0)

    state = pm.get_state()
    assert state.equity == 10030.0
    assert state.drawdown == 0.0


def test_no_stale_equity_after_realized_loss():
    pm = PortfolioStateManager(initial_balance=10000.0)
    pm.realized_pnl = -100.0
    pm.set_unrealized_pnl(-20.0)

    state = pm.get_state()
    assert state.equity == 9880.0
    assert state.drawdown == 120.0