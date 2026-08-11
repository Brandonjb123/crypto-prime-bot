"""Unit tests for PerformanceAnalyticsEngine."""

from datetime import UTC, datetime
from uuid import uuid4

from src.analytics.performance_analytics_engine import PerformanceAnalyticsEngine
from src.core.models.backtest_11b import BacktestConfig, BacktestResult, TradeRecord
from src.core.models.performance_report import PerformanceReport


def _make_trade(pnl: float, side: str = "BUY") -> TradeRecord:
    status = "WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "BREAKEVEN")
    return TradeRecord(
        trade_id=uuid4(),
        symbol="BTC",
        side=side,
        entry_price=50000.0,
        exit_price=50000.0 + pnl,
        position_size=1.0,
        pnl=pnl,
        status=status,
    )


def _make_result(
    initial_balance: float = 10000.0,
    final_balance: float = 10000.0,
    trades: list[TradeRecord] | None = None,
    max_drawdown: float = 0.0,
    max_drawdown_percent: float = 0.0,
) -> BacktestResult:
    return BacktestResult(
        config=BacktestConfig(symbol="BTC", timeframe="4h", initial_balance=initial_balance),
        initial_balance=initial_balance,
        final_balance=final_balance,
        total_pnl=final_balance - initial_balance,
        total_return_percent=((final_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0,
        total_trades=len(trades or []),
        winning_trades=sum(1 for t in (trades or []) if t.pnl > 0),
        losing_trades=sum(1 for t in (trades or []) if t.pnl < 0),
        win_rate=(sum(1 for t in (trades or []) if t.pnl > 0) / len(trades or [1]) * 100) if trades else 0.0,
        max_drawdown=max_drawdown,
        max_drawdown_percent=max_drawdown_percent,
        open_positions=0,
        closed_positions=len(trades or []),
        trades=trades or [],
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
    )


class TestPerformanceAnalyticsEngine:
    def test_basic_profitable_result(self):
        engine = PerformanceAnalyticsEngine()
        trades = [
            _make_trade(200),
            _make_trade(300),
            _make_trade(-100),
            _make_trade(-100),
        ]
        result = _make_result(
            initial_balance=10000.0,
            final_balance=10300.0,
            trades=trades,
        )
        report = engine.analyze(result)

        assert isinstance(report, PerformanceReport)
        assert report.net_profit == 300.0
        assert report.total_trades == 4
        assert report.winning_trades == 2
        assert report.losing_trades == 2
        assert report.win_rate == 50.0
        assert report.average_win == 250.0
        assert report.average_loss == 100.0
        assert report.profit_factor == 2.5
        assert report.expectancy == 75.0  # (0.5*250) - (0.5*100)
        assert report.total_return_percent == 3.0

    def test_zero_trades(self):
        engine = PerformanceAnalyticsEngine()
        result = _make_result(trades=[])
        report = engine.analyze(result)

        assert report.total_trades == 0
        assert report.win_rate == 0.0
        assert report.average_win == 0.0
        assert report.average_loss == 0.0
        assert report.profit_factor is None
        assert report.expectancy == 0.0

    def test_all_wins(self):
        engine = PerformanceAnalyticsEngine()
        trades = [_make_trade(100), _make_trade(200)]
        result = _make_result(
            initial_balance=10000.0,
            final_balance=10300.0,
            trades=trades,
        )
        report = engine.analyze(result)

        assert report.winning_trades == 2
        assert report.losing_trades == 0
        assert report.win_rate == 100.0
        assert report.average_loss == 0.0
        assert report.profit_factor is None  # No losses
        assert report.expectancy == 150.0  # (1.0*150) - (0*0)

    def test_all_losses(self):
        engine = PerformanceAnalyticsEngine()
        trades = [_make_trade(-100), _make_trade(-200)]
        result = _make_result(
            initial_balance=10000.0,
            final_balance=9700.0,
            trades=trades,
        )
        report = engine.analyze(result)

        assert report.winning_trades == 0
        assert report.losing_trades == 2
        assert report.win_rate == 0.0
        assert report.average_win == 0.0
        assert report.average_loss == 150.0
        assert report.profit_factor == 0.0  # gross_profit = 0
        assert report.expectancy == -150.0

    def test_break_even(self):
        engine = PerformanceAnalyticsEngine()
        trades = [_make_trade(0, side="BUY")]
        result = _make_result(trades=trades, final_balance=10000.0)
        report = engine.analyze(result)

        assert report.total_trades == 1
        assert report.winning_trades == 0
        assert report.losing_trades == 0
        assert report.win_rate == 0.0
        assert report.profit_factor is None

    def test_long_short_analysis(self):
        engine = PerformanceAnalyticsEngine()
        trades = [
            _make_trade(200, side="BUY"),
            _make_trade(-100, side="BUY"),
            _make_trade(150, side="SELL"),
            _make_trade(-50, side="SELL"),
        ]
        result = _make_result(
            initial_balance=10000.0,
            final_balance=10200.0,
            trades=trades,
        )
        report = engine.analyze(result)

        assert report.long_trades == 2
        assert report.short_trades == 2
        assert report.long_wins == 1
        assert report.short_wins == 1
        assert report.long_win_rate == 50.0
        assert report.short_win_rate == 50.0

    def test_deterministic(self):
        engine = PerformanceAnalyticsEngine()
        trades = [_make_trade(100), _make_trade(-50)]
        result = _make_result(
            initial_balance=10000.0,
            final_balance=10050.0,
            trades=trades,
        )
        r1 = engine.analyze(result)
        r2 = engine.analyze(result)

        assert r1.net_profit == r2.net_profit
        assert r1.win_rate == r2.win_rate
        assert r1.profit_factor == r2.profit_factor
        assert r1.expectancy == r2.expectancy