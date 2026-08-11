"""Integration test: BacktestResult → PerformanceAnalyticsEngine → PerformanceReport."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.analytics.performance_analytics_engine import PerformanceAnalyticsEngine
from src.core.models.backtest_11b import BacktestConfig, BacktestResult, TradeRecord
from src.core.models.performance_report import PerformanceReport


class TestAnalyticsIntegration:
    def test_full_analytics_flow(self):
        engine = PerformanceAnalyticsEngine()

        trades = [
            TradeRecord(
                trade_id=uuid4(), symbol="BTC", side="BUY",
                entry_price=50000.0, exit_price=51000.0,
                position_size=1.0, pnl=1000.0, status="WIN",
            ),
            TradeRecord(
                trade_id=uuid4(), symbol="BTC", side="SELL",
                entry_price=50000.0, exit_price=49000.0,
                position_size=1.0, pnl=1000.0, status="WIN",
            ),
            TradeRecord(
                trade_id=uuid4(), symbol="BTC", side="BUY",
                entry_price=50000.0, exit_price=49500.0,
                position_size=1.0, pnl=-500.0, status="LOSS",
            ),
        ]

        result = BacktestResult(
            config=BacktestConfig(symbol="BTC", timeframe="4h", initial_balance=10000.0),
            initial_balance=10000.0,
            final_balance=11500.0,
            total_pnl=1500.0,
            total_return_percent=15.0,
            total_trades=3,
            winning_trades=2,
            losing_trades=1,
            win_rate=66.67,
            max_drawdown=0.0,
            max_drawdown_percent=0.0,
            open_positions=0,
            closed_positions=3,
            trades=trades,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
        )

        report = engine.analyze(result)
        assert isinstance(report, PerformanceReport)
        assert report.net_profit == 1500.0
        assert report.total_trades == 3
        assert report.winning_trades == 2
        assert report.losing_trades == 1
        assert report.win_rate == pytest.approx(66.67, 0.01)
        assert report.average_win == 1000.0
        assert report.average_loss == 500.0
        assert report.profit_factor == 4.0
        assert report.expectancy == pytest.approx(500.0, 0.01)