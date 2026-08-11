from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import PositionStatus
from src.execution.paper_trading_engine import PaperTradingEngine
from src.portfolio.portfolio_state_manager import PortfolioStateManager


def _make_signal(**overrides):
    defaults = dict(
        signal_id=uuid4(), symbol="BTC", side="BUY", status="ACTIVE",
        entry_price=50000.0, stop_loss=48000.0, take_profit=55000.0,
        position_size=0.01, risk_percent=2.0, confidence=85,
        risk_level="MEDIUM", reasoning=["test"], created_at=datetime.now(UTC)
    )
    defaults.update(overrides)
    return TradingSignal(**defaults)

class TestPaperTradingEngine:
    def test_active_buy_filled(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm)
        result = engine.execute(_make_signal(side="BUY"))
        assert result.status == "FILLED"
        assert result.executed_price == 50000.0
        assert result.position_size == 0.01

    def test_active_sell_filled(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm)
        result = engine.execute(_make_signal(side="SELL"))
        assert result.status == "FILLED"

    def test_skipped_signal(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm)
        result = engine.execute(_make_signal(status="SKIPPED"))
        assert result.status == "SKIPPED"

    def test_invalid_signal(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm)
        result = engine.execute(_make_signal(status="INVALID"))
        assert result.status == "REJECTED"

    def test_duplicate_signal_rejected(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm)
        signal = _make_signal()
        engine.execute(signal)
        result2 = engine.execute(signal)
        assert result2.status == "REJECTED"

    def test_executed_price_with_slippage(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm, slippage=0.5)
        result = engine.execute(_make_signal(side="BUY", entry_price=50000.0))
        assert result.executed_price == 50000.5

    def test_position_opened_after_fill(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm)
        engine.execute(_make_signal())
        state = pm.get_state()
        assert state.open_positions == 1

    def test_close_long_profit(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm)
        signal = _make_signal(side="BUY", entry_price=50000.0, position_size=0.01)
        engine.execute(signal)
        positions = pm.repo.get_open()
        pos = positions[0]
        closed = engine.close_position(pos.position_id, 51000.0)
        assert closed is not None
        assert closed.status == PositionStatus.CLOSED
        assert pm.realized_pnl == 10.0

    def test_close_short_profit(self):
        pm = PortfolioStateManager(initial_balance=10000.0)
        engine = PaperTradingEngine(pm)
        signal = _make_signal(side="SELL", entry_price=50000.0, position_size=0.01)
        engine.execute(signal)
        positions = pm.repo.get_open()
        pos = positions[0]
        closed = engine.close_position(pos.position_id, 49000.0)
        assert closed.status == PositionStatus.CLOSED
        assert pm.realized_pnl == 10.0   # (50000 - 49000) * 0.01