"""Integration test: Historical Candle → Backtest Engine → BacktestResult."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.backtest.engine import BacktestEngine
from src.core.models.backtest import HistoricalCandle
from src.exchange.adapters.paper import PaperExchangeAdapter
from src.lifecycle.trade_lifecycle_engine import TradeLifecycleEngine
from src.portfolio.portfolio_manager import PortfolioManager
from src.position.position_manager import PositionManager


class TestBacktestPipeline:
    async def test_full_backtest_flow(self):
        orchestrator = MagicMock()
        orchestrator.run = AsyncMock(return_value=MagicMock(position=None))

        engine = BacktestEngine(
            orchestrator=orchestrator,
            paper_exchange=PaperExchangeAdapter(),
            position_manager=PositionManager(),
            portfolio_manager=PortfolioManager(),
            lifecycle_engine=TradeLifecycleEngine(),
        )

        base = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        candles = [
            HistoricalCandle(
                timestamp=base + timedelta(hours=i * 4),
                symbol="BTCUSDT", timeframe="4h",
                open=100.0, high=105.0, low=95.0, close=100.0 + i,
                volume=1000.0
            )
            for i in range(50)
        ]

        result = await engine.run(candles)
        assert result.status == "COMPLETED"
        assert result.total_trades >= 0