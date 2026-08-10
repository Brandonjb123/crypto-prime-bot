"""Unit tests untuk PortfolioStateManager."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import PositionStatus, Side
from src.portfolio.portfolio_state_manager import PortfolioStateManager


def _make_signal(**overrides):
    defaults = dict(
        signal_id=uuid4(),
        symbol="BTC",
        side="BUY",
        status="ACTIVE",
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0,
        position_size=0.01,
        risk_percent=2.0,
        confidence=85,
        risk_level="MEDIUM",
        reasoning=["test"],
        created_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    return TradingSignal(**defaults)


class TestPortfolioStateManager:
    def test_initial_balance(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        state = pm.get_state()
        assert state.account_balance == 10000.0
        assert state.equity == 10000.0
        assert state.peak_equity == 10000.0
        assert state.drawdown == 0.0

    def test_open_long_position(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal()
        pos = pm.open_position(signal)
        assert pos is not None
        assert pos.status == PositionStatus.OPEN
        assert pos.side == Side.LONG
        assert pos.entry_price == 50000.0
        assert pos.position_size == 0.01

    def test_open_short_position(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal(side="SELL")
        pos = pm.open_position(signal)
        assert pos is not None
        assert pos.side == Side.SHORT
        assert pos.entry_price == 50000.0

    def test_skipped_signal_does_not_open(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal(status="SKIPPED")
        pos = pm.open_position(signal)
        assert pos is None

    def test_invalid_signal_does_not_open(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal(status="INVALID")
        pos = pm.open_position(signal)
        assert pos is None

    def test_duplicate_signal_rejected(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal()
        pm.open_position(signal)
        pos2 = pm.open_position(signal)  # same signal_id
        assert pos2 is None

    def test_update_price_long_profit(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal()
        pos = pm.open_position(signal)
        pnl = pm.update_price(pos.position_id, 51000.0)
        # (51000 - 50000) * 0.01 = 10.0
        assert pnl == 10.0

    def test_update_price_short_profit(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal(side="SELL")
        pos = pm.open_position(signal)
        pnl = pm.update_price(pos.position_id, 49000.0)
        # (50000 - 49000) * 0.01 = 10.0
        assert pnl == 10.0

    def test_close_position_long_profit(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal()
        pos = pm.open_position(signal)
        closed = pm.close_position(pos.position_id, 52000.0)
        assert closed is not None
        assert closed.status == PositionStatus.CLOSED
        # (52000 - 50000) * 0.01 = 20.0
        assert pm.realized_pnl == 20.0

    def test_close_position_short_loss(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal(side="SELL")
        pos = pm.open_position(signal)
        pm.close_position(pos.position_id, 51000.0)
        # (50000 - 51000) * 0.01 = -10.0
        assert pm.realized_pnl == -10.0

    def test_equity_after_close(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal()
        pos = pm.open_position(signal)
        pm.close_position(pos.position_id, 52000.0)
        state = pm.get_state()
        # equity = 10000 + 20 realized = 10020
        assert state.equity == 10020.0

    def test_drawdown(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal()
        pos = pm.open_position(signal)
        pm.close_position(pos.position_id, 49000.0)  # loss 10
        state = pm.get_state()
        # equity = 10000 - 10 = 9990, peak = 10000, drawdown = 10
        assert state.drawdown == 10.0
        assert state.drawdown_percent == 0.1

    def test_new_equity_high_resets_drawdown(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        signal = _make_signal()
        pos = pm.open_position(signal)
        pm.close_position(pos.position_id, 55000.0)  # profit 50
        state = pm.get_state()
        assert state.equity == 10050.0
        assert state.peak_equity == 10050.0
        assert state.drawdown == 0.0