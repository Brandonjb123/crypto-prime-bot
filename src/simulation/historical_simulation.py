"""Historical Simulation Runner — menjalankan pipeline pada data candle historis."""

from datetime import UTC, datetime

from src.ai.groq_client import GroqRateLimitError
from src.core.models.market_snapshot import MarketSnapshot
from src.core.models.position import Position
from src.core.types.enums import PositionStatus, Side
from src.execution.paper_trading_engine import PaperTradingEngine
from src.lifecycle.trade_lifecycle_engine import TradeLifecycleEngine
from src.logging.logger import get_logger
from src.portfolio.portfolio_state_manager import PortfolioStateManager

logger = get_logger("historical_simulation")


class HistoricalSimulationResult:
    def __init__(self):
        self.closed_trades: list[Position] = []
        self.total_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        self.valid_decision_count = 0
        self.ai_unavailable_count = 0
        self.buy_signals = 0
        self.sell_signals = 0
        self.wait_signals = 0


class HistoricalSimulationRunner:
    def __init__(
        self,
        indicator_engine,
        analysis_engine,
        decision_engine,
        validation_engine,
        risk_engine,
        signal_engine,
        initial_balance: float = 10000.0,
    ):
        self.indicator_engine = indicator_engine
        self.analysis_engine = analysis_engine
        self.decision_engine = decision_engine
        self.validation_engine = validation_engine
        self.risk_engine = risk_engine
        self.signal_engine = signal_engine
        self.initial_balance = initial_balance
        self.lifecycle_engine = TradeLifecycleEngine()

    async def run_asset(
        self,
        symbol: str,
        raw_candles: list[list],
        timeframe: str = "4h",
    ) -> HistoricalSimulationResult:
        """Jalankan pipeline untuk satu aset dengan portfolio terisolasi."""
        result = HistoricalSimulationResult()

        portfolio = PortfolioStateManager(initial_balance=self.initial_balance)
        engine = PaperTradingEngine(portfolio_manager=portfolio)

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

            try:
                indicators = self.indicator_engine.calculate(snapshot)
                analysis = self.analysis_engine.analyze(indicators)

                decision = await self.decision_engine.decide(analysis)
                result.valid_decision_count += 1
                if decision.decision == "BUY":
                    result.buy_signals += 1
                elif decision.decision == "SELL":
                    result.sell_signals += 1
                else:
                    result.wait_signals += 1

                validated = self.validation_engine.validate(decision)
                atr = indicators.atr14 or 0.0
                trade_plan = self.risk_engine.calculate(
                    validated, snapshot.current_price, atr, self.initial_balance
                )
                signal = self.signal_engine.generate(trade_plan)
                if decision is not None:
                    signal.confidence = getattr(decision, "confidence", 0)

                if signal.status == "ACTIVE":
                    engine.execute(signal)

            except GroqRateLimitError:
                result.ai_unavailable_count += 1
                continue

            except Exception as e:
                logger.warning(f"Pipeline error at index {i} for {symbol}: {e}")

            self._evaluate_positions(engine, symbol, close_price)

        for pos in portfolio.repo.get_all():
            if pos.symbol != symbol:
                continue
            if pos.status != PositionStatus.CLOSED:
                continue

            result.closed_trades.append(pos)

            exit_price = pos.last_price if pos.last_price is not None else pos.entry_price
            if pos.side == Side.LONG:
                pnl = (exit_price - pos.entry_price) * pos.position_size
            else:
                pnl = (pos.entry_price - exit_price) * pos.position_size

            result.total_pnl += pnl
            if pnl > 0:
                result.win_count += 1
            else:
                result.loss_count += 1

        return result

    def _evaluate_positions(self, engine: PaperTradingEngine, symbol: str, current_price: float) -> None:
        """Evaluasi TP/SL untuk posisi open aset ini."""
        portfolio = engine.portfolio_manager
        for pos in portfolio.get_open_positions():
            if pos.symbol != symbol:
                continue

            action, fraction = self.lifecycle_engine.evaluate(pos, current_price)
            if action != "HOLD":
                logger.info(f"Simulation lifecycle action={action} for {pos.symbol} {pos.side}")
                engine.apply_lifecycle_action(
                    pos.position_id, action, current_price, fraction
                )