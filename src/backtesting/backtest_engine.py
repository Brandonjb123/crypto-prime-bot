"""Backtest Engine — menjalankan strategi pada data historis secara sekuensial."""

import inspect
from uuid import uuid4

from src.analysis.analysis_engine import AnalysisEngine
from src.analysis.indicator_engine import IndicatorEngine
from src.backtesting.historical_data_provider import HistoricalDataProvider
from src.core.models.backtest_11b import BacktestConfig, BacktestResult, TradeRecord
from src.core.types.enums import Side
from src.execution.paper_trading_engine import PaperTradingEngine
from src.logging.logger import get_logger
from src.portfolio.portfolio_state_manager import PortfolioStateManager
from src.risk.trade_risk_engine import TradeRiskEngine
from src.signal.signal_engine import SignalEngine
from src.validation.validation_engine import ValidationEngine

logger = get_logger("backtest_engine")


class BacktestEngine:
    def __init__(
        self,
        data_provider: HistoricalDataProvider,
        indicator_engine: IndicatorEngine,
        analysis_engine: AnalysisEngine,
        decision_engine,  # Menerima MockDecisionEngine atau DecisionEngine
        validation_engine: ValidationEngine,
        risk_engine: TradeRiskEngine,
        signal_engine: SignalEngine,
        paper_trading_engine: PaperTradingEngine,
        portfolio_manager: PortfolioStateManager,
    ):
        self.data_provider = data_provider
        self.indicator_engine = indicator_engine
        self.analysis_engine = analysis_engine
        self.decision_engine = decision_engine
        self.validation_engine = validation_engine
        self.risk_engine = risk_engine
        self.signal_engine = signal_engine
        self.paper_trading_engine = paper_trading_engine
        self.portfolio_manager = portfolio_manager

    async def run(self, config: BacktestConfig) -> BacktestResult:
        snapshots = self.data_provider.get_data(config.symbol, config.timeframe)
        if not snapshots:
            raise ValueError("No historical data available")

        trades: list[TradeRecord] = []
        # Reset portfolio ke initial balance
        self.portfolio_manager = PortfolioStateManager(initial_balance=config.initial_balance)

        for idx, snapshot in enumerate(snapshots):
            logger.info(f"Processing candle {idx+1}/{len(snapshots)} at {snapshot.timestamp}")

            # Step 1 – Hitung indicator
            indicators = self.indicator_engine.calculate(snapshot)

            # Step 2 – Analisis market
            analysis = self.analysis_engine.analyze(indicators)

            # Step 3 – AI Decision (gunakan decision engine yang di-inject)
            # DecisionEngine.decide adalah coroutine, jadi kita await
            if inspect.iscoroutinefunction(self.decision_engine.decide):
                decision = await self.decision_engine.decide(analysis)
            else:
                decision = self.decision_engine.decide(analysis)

            # Step 4 – Validasi
            validated = self.validation_engine.validate(decision)

            # Step 5 – Risk
            entry_price = snapshot.current_price
            atr = indicators.atr14 or 0.0
            trade_plan = self.risk_engine.calculate(validated, entry_price, atr, config.initial_balance)

            # Step 6 – Signal
            signal = self.signal_engine.generate(trade_plan)

            # Step 7 – Paper Execution
            if signal.status == "ACTIVE":
                self.paper_trading_engine.execute(signal)

            # Step 8 – Cek SL/TP menggunakan high/low candle
            open_positions = self.portfolio_manager.repo.get_open()
            for pos in open_positions:
                # Cek Stop Loss
                if pos.side == Side.LONG and snapshot.low <= pos.stop_loss:
                    self._close_position(pos, pos.stop_loss, trades)
                elif pos.side == Side.SHORT and snapshot.high >= pos.stop_loss:
                    self._close_position(pos, pos.stop_loss, trades)
                # Cek Take Profit
                elif pos.side == Side.LONG and snapshot.high >= pos.take_profit:
                    self._close_position(pos, pos.take_profit, trades)
                elif pos.side == Side.SHORT and snapshot.low <= pos.take_profit:
                    self._close_position(pos, pos.take_profit, trades)

        # Tutup semua posisi yang masih terbuka di akhir backtest
        last_price = snapshots[-1].current_price if snapshots else 0
        for pos in self.portfolio_manager.repo.get_open():
            self._close_position(pos, last_price, trades)

        # Hitung metrik
        final_state = self.portfolio_manager.get_state()
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl < 0]
        total_pnl = sum(t.pnl for t in trades)
        win_rate = len(winning) / len(trades) if trades else 0.0
        total_return = (final_state.equity - config.initial_balance) / config.initial_balance * 100

        # Drawdown (peak-to-valley)
        peak = config.initial_balance
        max_dd = 0.0
        for t in trades:
            peak = max(peak, peak + t.pnl)
            dd = peak - (peak + t.pnl)
            max_dd = max(max_dd, dd)

        return BacktestResult(
            config=config,
            initial_balance=config.initial_balance,
            final_balance=final_state.equity,
            total_pnl=total_pnl,
            total_return_percent=round(total_return, 2),
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=round(win_rate, 4),
            max_drawdown=round(max_dd, 2),
            max_drawdown_percent=round(max_dd / config.initial_balance * 100, 2) if config.initial_balance > 0 else 0.0,
            open_positions=len(self.portfolio_manager.repo.get_open()),
            closed_positions=len(trades),
            trades=trades,
            start_time=snapshots[0].timestamp,
            end_time=snapshots[-1].timestamp,
        )

    def _close_position(self, pos, exit_price, trades_list):
        if pos.side == Side.LONG:
            pnl = (exit_price - pos.entry_price) * pos.position_size
        else:
            pnl = (pos.entry_price - exit_price) * pos.position_size

        closed = self.paper_trading_engine.close_position(pos.position_id, exit_price)
        if closed:
            trades_list.append(TradeRecord(
                trade_id=uuid4(),
                symbol=pos.symbol,
                side="LONG" if pos.side == Side.LONG else "SHORT",
                entry_price=pos.entry_price,
                exit_price=exit_price,
                position_size=pos.position_size,
                pnl=pnl,
                status="WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "BREAKEVEN"),
            ))