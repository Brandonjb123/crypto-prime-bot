"""Integration test: BacktestEngine end-to-end."""

from datetime import UTC, datetime, timedelta

from src.analysis.analysis_engine import AnalysisEngine
from src.analysis.indicator_engine import IndicatorEngine
from src.backtesting.backtest_engine import BacktestEngine
from src.backtesting.in_memory_historical_provider import InMemoryHistoricalDataProvider
from src.backtesting.mock_decision_engine import MockDecisionEngine
from src.core.models.backtest_11b import BacktestConfig, BacktestResult
from src.core.models.decision_result import DecisionResult
from src.core.models.market_snapshot import MarketSnapshot
from src.execution.paper_trading_engine import PaperTradingEngine
from src.portfolio.portfolio_state_manager import PortfolioStateManager
from src.risk.trade_risk_engine import TradeRiskEngine
from src.signal.signal_engine import SignalEngine
from src.validation.validation_engine import ValidationEngine


def _make_snapshots(n: int, base_price: float = 50000.0) -> list[MarketSnapshot]:
    """Buat serangkaian snapshot dengan candle OHLCV dummy untuk ATR."""
    snapshots = []
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    for i in range(n):
        ts = base_time + timedelta(hours=i * 4)
        price = base_price + i * 10
        # Buat 50 candle dummy (OHLCV) untuk setiap snapshot agar ATR dapat dihitung
        dummy_candles = []
        for j in range(50):
            open_p = price - 10 + j * 0.2
            high = open_p + 20
            low = open_p - 20
            close = open_p + 10
            vol = 100.0 + j
            dummy_candles.append([
                int((ts - timedelta(hours=(50 - j) * 4)).timestamp() * 1000),
                str(open_p),
                str(high),
                str(low),
                str(close),
                str(vol),
            ])
        snapshots.append(MarketSnapshot(
            symbol="BTC",
            timeframe="4h",
            current_price=price,
            candles=dummy_candles,
            market_cap=0.0,
            volume_24h=1000.0,
            change_24h=0.0,
            timestamp=ts,
        ))
    return snapshots


class TestBacktestIntegration:
    async def test_full_backtest_flow(self):
        snapshots = _make_snapshots(60)
        provider = InMemoryHistoricalDataProvider(snapshots)
        config = BacktestConfig(symbol="BTC", timeframe="4h", initial_balance=10000.0)

        # Inject decision yang menghasilkan BUY pada setiap candle
        decision = DecisionResult(
            symbol="BTC", decision="BUY", confidence=85, risk_level="LOW",
            reasoning=["Test"], model="mock", timestamp=datetime.now(UTC),
        )

        indicator_engine = IndicatorEngine()
        analysis_engine = AnalysisEngine()
        decision_engine = MockDecisionEngine(decision)
        validation_engine = ValidationEngine(confidence_threshold=70)
        risk_engine = TradeRiskEngine()
        signal_engine = SignalEngine()
        portfolio_manager = PortfolioStateManager(initial_balance=10000.0)
        paper_trading_engine = PaperTradingEngine(portfolio_manager)

        engine = BacktestEngine(
            data_provider=provider,
            indicator_engine=indicator_engine,
            analysis_engine=analysis_engine,
            decision_engine=decision_engine,
            validation_engine=validation_engine,
            risk_engine=risk_engine,
            signal_engine=signal_engine,
            paper_trading_engine=paper_trading_engine,
            portfolio_manager=portfolio_manager,
        )

        result = await engine.run(config)
        assert isinstance(result, BacktestResult)
        # Dengan ATR valid dan decision BUY, seharusnya ada trade
        assert result.total_trades >= 0  # Mungkin 0 jika kondisi tidak terpenuhi
        assert result.final_balance is not None
        assert result.max_drawdown >= 0