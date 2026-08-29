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
        self.tp1_count = 0
        self.tp2_count = 0
        self.sl_count = 0


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
        self.min_candles = 50  # minimal candle untuk indikator

    async def run_asset(
        self,
        symbol: str,
        raw_candles: list[list],
        timeframe: str = "4h",
    ) -> HistoricalSimulationResult:
        """
        Jalankan pipeline untuk satu aset.
        Entry hanya setelah candle T closes.
        Exit dievaluasi mulai T+1 menggunakan high/low candle.
        """
        result = HistoricalSimulationResult()

        portfolio = PortfolioStateManager(initial_balance=self.initial_balance)
        engine = PaperTradingEngine(portfolio_manager=portfolio)
        entry_iteration: dict = {}

        for i in range(self.min_candles, len(raw_candles)):
            high_price = float(raw_candles[i][2])
            low_price = float(raw_candles[i][3])

            # Evaluasi posisi open yang sudah boleh dievaluasi (entry < i)
            self._evaluate_positions(engine, symbol, high_price, low_price)

            # Proses sinyal & entry hanya jika posisi belum ada
            close_price = float(raw_candles[i][4])
            snapshot = MarketSnapshot(
                symbol=symbol,
                timeframe=timeframe,
                current_price=close_price,
                candles=raw_candles[: i + 1],
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
                    validated, close_price, atr, self.initial_balance
                )
                signal = self.signal_engine.generate(trade_plan)
                if decision is not None:
                    signal.confidence = getattr(decision, "confidence", 0)

                if signal.status == "ACTIVE":
                    position = engine.execute(signal)
                    if position:
                        entry_iteration[position.position_id] = i

            except GroqRateLimitError:
                result.ai_unavailable_count += 1
                continue

            except Exception as e:
                logger.warning(f"Pipeline error at index {i} for {symbol}: {e}")

        # Kumpulkan closed trades khusus aset ini
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

            # Hitung TP/SL counts
            if pos.close_reason.value == "TAKE_PROFIT":
                result.tp2_count += 1  # final TP dianggap TP2
            elif pos.close_reason.value == "STOP_LOSS":
                result.sl_count += 1

        return result

    def _evaluate_positions(self, engine: PaperTradingEngine, symbol: str, high_price: float, low_price: float) -> None:
        """
        Evaluasi posisi open menggunakan high/low candle.
        SL priority: jika SL tersentuh, SL dieksekusi lebih dulu.
        """
        portfolio = engine.portfolio_manager
        for pos in portfolio.get_open_positions():
            if pos.symbol != symbol:
                continue

            action, fraction, exit_price = self._check_touch(pos, high_price, low_price)
            if action != "HOLD":
                logger.info(f"Simulation lifecycle action={action} for {pos.symbol} {pos.side}")
                engine.apply_lifecycle_action(
                    pos.position_id, action, exit_price, fraction
                )

    def _check_touch(self, pos: Position, high_price: float, low_price: float) -> tuple[str, float, float]:
        """Tentukan aksi berdasarkan sentuhan SL/TP1/TP2 menggunakan high/low.

        Returns:
            action: "HOLD", "SL", "TP1", "TP2"
            fraction: fraksi posisi yang ditutup (1.0 untuk SL/TP2, 0.5 untuk TP1)
            exit_price: harga eksekusi (SL price atau TP price)
        """
        tp2_price = pos.tp2_price or pos.take_profit
        tp1_price = pos.tp1_price

        if pos.side == Side.LONG:
            # SL priority
            if low_price <= pos.stop_loss:
                return "SL", 1.0, pos.stop_loss
            if tp2_price and high_price >= tp2_price:
                return "TP2", 1.0, tp2_price
            if tp1_price and high_price >= tp1_price:
                return "TP1", 0.5, tp1_price
        else:  # SHORT
            if high_price >= pos.stop_loss:
                return "SL", 1.0, pos.stop_loss
            if tp2_price and low_price <= tp2_price:
                return "TP2", 1.0, tp2_price
            if tp1_price and low_price <= tp1_price:
                return "TP1", 0.5, tp1_price

        return "HOLD", 0.0, 0.0