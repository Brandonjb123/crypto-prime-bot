"""Historical Simulation Runner — menjalankan pipeline pada data candle historis."""

from datetime import UTC, datetime

from src.core.models.market_snapshot import MarketSnapshot
from src.core.models.position import Position
from src.core.types.enums import PositionStatus
from src.lifecycle.trade_lifecycle_engine import TradeLifecycleEngine
from src.logging.logger import get_logger

logger = get_logger("historical_simulation")


class HistoricalSimulationResult:
    def __init__(self):
        self.closed_trades: list[Position] = []
        self.total_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0


class HistoricalSimulationRunner:
    def __init__(
        self,
        indicator_engine,
        analysis_engine,
        decision_engine,
        validation_engine,
        risk_engine,
        signal_engine,
        paper_trading_engine,
        lifecycle_engine: TradeLifecycleEngine,
        price_provider=None,
    ):
        self.indicator_engine = indicator_engine
        self.analysis_engine = analysis_engine
        self.decision_engine = decision_engine
        self.validation_engine = validation_engine
        self.risk_engine = risk_engine
        self.signal_engine = signal_engine
        self.paper_trading_engine = paper_trading_engine
        self.lifecycle_engine = lifecycle_engine
        self.price_provider = price_provider

    async def run_asset(self, symbol: str, raw_candles: list[list], timeframe: str = "4h") -> HistoricalSimulationResult:
        """Jalankan pipeline untuk satu aset sepanjang data historis."""
        result = HistoricalSimulationResult()
        portfolio = self.paper_trading_engine.portfolio_manager

        # Konversi raw klines ke list[dict] atau langsung pakai di snapshot
        for i in range(50, len(raw_candles)):
            candle_window = raw_candles[: i + 1]
            close_price = float(raw_candles[i][4])

            snapshot = MarketSnapshot(
                symbol=symbol,
                timeframe=timeframe,
                current_price=close_price,
                candles=candle_window,
                timestamp=datetime.now(UTC),
            )

            # Update price provider untuk unrealized PnL
            if self.price_provider:
                self.price_provider.update_price(symbol, close_price)

            # Jalankan pipeline mini
            try:
                # Indicators
                indicators = self.indicator_engine.calculate(snapshot)

                # Analysis
                analysis = self.analysis_engine.analyze(indicators)

                # Decision (LLM)
                decision = await self.decision_engine.decide(analysis)

                # Validation
                validated = self.validation_engine.validate(decision)

                # Risk
                atr = indicators.atr14 or 0.0
                trade_plan = self.risk_engine.calculate(
                    validated, snapshot.current_price, atr, portfolio.initial_balance
                )

                # Signal
                signal = self.signal_engine.generate(trade_plan)
                if decision is not None:
                    signal.confidence = getattr(decision, "confidence", 0)

                # Paper execution
                if signal.status == "ACTIVE":
                    self.paper_trading_engine.execute(signal)
            except Exception as e:
                logger.warning(f"Pipeline error at index {i} for {symbol}: {e}")

            # Evaluasi lifecycle untuk semua posisi open aset ini
            self._evaluate_positions(symbol, close_price)

        # Kumpulkan closed trades
        for pos in portfolio.repo.get_all():
            if pos.status != PositionStatus.OPEN:
                result.closed_trades.append(pos)
                if pos.side.value == "LONG":
                    pnl = (pos.last_price or pos.entry_price - pos.entry_price) * pos.position_size
                else:
                    pnl = (pos.entry_price - (pos.last_price or pos.entry_price)) * pos.position_size

                result.total_pnl += pnl
                if pnl > 0:
                    result.win_count += 1
                else:
                    result.loss_count += 1

        return result

    def _evaluate_positions(self, symbol: str, current_price: float) -> None:
        """Evaluasi posisi open untuk symbol ini."""
        portfolio = self.paper_trading_engine.portfolio_manager
        for pos in portfolio.get_open_positions():
            if pos.symbol != symbol:
                continue

            action, fraction = self.lifecycle_engine.evaluate(pos, current_price)
            if action != "HOLD":
                logger.info(f"Simulation lifecycle action={action} for {pos.symbol} {pos.side}")
                self.paper_trading_engine.apply_lifecycle_action(
                    pos.position_id, action, current_price, fraction
                )