import asyncio
from unittest.mock import MagicMock
from uuid import uuid4

from src.core.types.enums import OrderStatus
from src.execution.exchange.mock_client import MockExchangeClient
from src.execution.execution_router import ExecutionRouter
from src.execution.live_trading_engine import LiveTradingEngine
from src.execution.paper_trading_engine import PaperTradingEngine
from src.portfolio.portfolio_state_manager import PortfolioStateManager


def make_signal():
    signal = MagicMock()
    signal.signal_id = uuid4()
    signal.symbol = "BTCUSDT"
    signal.side = "LONG"
    signal.position_size = 0.01
    signal.entry_price = 50000.0
    signal.stop_loss = 49000.0
    signal.take_profit = 52000.0
    return signal


class TestLiveExecutionIntegration:
    def test_full_flow_mock_filled(self):
        portfolio = PortfolioStateManager(initial_balance=10000.0)
        paper = PaperTradingEngine(portfolio)
        mock = MockExchangeClient(behavior="fill_immediately")
        live = LiveTradingEngine(mock)

        settings = MagicMock(TRADING_MODE="LIVE", LIVE_TRADING_ENABLED=True)
        router = ExecutionRouter(paper, live, settings)

        result = asyncio.run(router.execute(make_signal()))
        assert result.status == OrderStatus.FILLED

    def test_paper_regression(self):
        portfolio = PortfolioStateManager(initial_balance=10000.0)
        paper = PaperTradingEngine(portfolio)
        mock = MockExchangeClient()
        live = LiveTradingEngine(mock)

        settings = MagicMock(TRADING_MODE="PAPER", LIVE_TRADING_ENABLED=False)
        router = ExecutionRouter(paper, live, settings)

        result = asyncio.run(router.execute(make_signal()))
        # Paper engine mengembalikan ExecutionResult (existing behavior)
        assert result is not None