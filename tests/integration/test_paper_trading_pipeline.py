from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import PositionStatus
from src.execution.paper_trading_engine import PaperTradingEngine
from src.portfolio.portfolio_state_manager import PortfolioStateManager


def _make_signal(**overrides):
    defaults = dict(
        signal_id=uuid4(), symbol="ETH", side="BUY", status="ACTIVE",
        entry_price=3000.0, stop_loss=2800.0, take_profit=3500.0,
        position_size=0.1, risk_percent=2.0, confidence=80,
        risk_level="MEDIUM", reasoning=["test"], created_at=datetime.now(UTC)
    )
    defaults.update(overrides)
    return TradingSignal(**defaults)

class TestPaperTradingPipeline:
    def test_full_paper_trading_flow(self):
        pm = PortfolioStateManager(initial_balance=5000.0)
        engine = PaperTradingEngine(pm)
        signal = _make_signal()
        result = engine.execute(signal)
        assert result.status == "FILLED"

        positions = pm.repo.get_open()
        assert len(positions) == 1
        pos = positions[0]
        assert pos.symbol == "ETH"
        assert pos.entry_price == 3000.0
        assert pos.position_size == 0.1

        closed = engine.close_position(pos.position_id, 3200.0)
        assert closed.status == PositionStatus.CLOSED
        state = pm.get_state()
        assert state.realized_pnl == 20.0
        assert state.equity == 5020.0