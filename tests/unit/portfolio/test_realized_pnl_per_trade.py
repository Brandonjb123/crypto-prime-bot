from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.models.trading_signal import TradingSignal
from src.portfolio.portfolio_state_manager import PortfolioStateManager


def _make_signal(symbol="BTC", entry=50000.0, size=0.01):
    return TradingSignal(
        signal_id=uuid4(),
        symbol=symbol,
        side="BUY",
        status="ACTIVE",
        entry_price=entry,
        stop_loss=entry - 1000,
        take_profit=entry + 2000,
        position_size=size,
        created_at=datetime.now(UTC),
    )


def test_trade_without_partial_tp_realized_pnl():
    pm = PortfolioStateManager(initial_balance=10000.0)
    sig = _make_signal()
    pos = pm.open_position(sig)

    # Close langsung di profit
    closed = pm.close_position(pos.position_id, exit_price=51000.0)
    assert closed is not None
    assert closed.realized_pnl == pytest.approx((51000 - 50000) * 0.01)


def test_trade_with_partial_tp_and_final_close_realized_pnl():
    pm = PortfolioStateManager(initial_balance=10000.0)
    sig = _make_signal()
    pos = pm.open_position(sig)

    # Partial TP 50% di 50500 -> profit = (50500-50000)*0.005
    pnl_partial = (50500 - 50000) * (0.01 * 0.5)
    remaining_pos, _ = pm.partial_close(pos.position_id, exit_price=50500, fraction=0.5)

    # Final close sisa di 50200 -> profit = (50200-50000)*0.005
    pnl_final = (50200 - 50000) * (0.01 * 0.5)
    closed = pm.close_position(remaining_pos.position_id, exit_price=50200)

    expected_total = pnl_partial + pnl_final
    assert closed is not None
    assert closed.realized_pnl == pytest.approx(expected_total)


def test_portfolio_aggregate_realized_pnl_unchanged():
    pm = PortfolioStateManager(initial_balance=10000.0)
    sig = _make_signal()
    pos = pm.open_position(sig)

    # Partial + final
    pm.partial_close(pos.position_id, exit_price=50500, fraction=0.5)
    # Ambil posisi baru dari repo untuk close final
    for p in pm.repo.get_open():
        if p.position_id == pos.position_id:
            pm.close_position(p.position_id, exit_price=50200)
            break

    state = pm.get_state()
    assert state.realized_pnl == pytest.approx(3.5)