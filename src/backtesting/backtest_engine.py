"""Backtest Engine — menjalankan strategi pada data historis secara sekuensial."""

import inspect
from datetime import datetime
from uuid import uuid4

from src.analysis.analysis_engine import AnalysisEngine
from src.analysis.indicator_engine import IndicatorEngine
from src.backtesting.historical_data_provider import HistoricalDataProvider
from src.backtesting.trading_cost_model import TradingCostModel
from src.core.models.backtest_11b import BacktestConfig, BacktestResult, EquityPoint, TradeRecord
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
        decision_engine,
        validation_engine: ValidationEngine,
        risk_engine: TradeRiskEngine,
        signal_engine: SignalEngine,
        paper_trading_engine: PaperTradingEngine,
        portfolio_manager: PortfolioStateManager,
        cost_model: TradingCostModel | None = None,
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
        self.cost_model = cost_model or TradingCostModel()
        self._equity_curve: list[EquityPoint] = []

    async def run(self, config: BacktestConfig) -> BacktestResult:
        snapshots = self.data_provider.get_data(config.symbol, config.timeframe)
        if not snapshots:
            raise ValueError("No historical data available")

        trades: list[TradeRecord] = []
        self._equity_curve = []
        self.portfolio_manager = PortfolioStateManager(initial_balance=config.initial_balance)

        # Initial equity point
        self._add_equity_point(snapshots[0].timestamp)

        for idx, snapshot in enumerate(snapshots):
            logger.info(f"Processing candle {idx+1}/{len(snapshots)} at {snapshot.timestamp}")

            # Step 1 — Hitung indicator
            indicators = self.indicator_engine.calculate(snapshot)

            # Step 2 — Analisis market
            analysis = self.analysis_engine.analyze(indicators)

            # Step 3 — AI Decision
            if inspect.iscoroutinefunction(self.decision_engine.decide):
                decision = await self.decision_engine.decide(analysis)
            else:
                decision = self.decision_engine.decide(analysis)

            # Step 4 — Validasi
            validated = self.validation_engine.validate(decision)

            # Step 5 — Risk
            entry_price = snapshot.current_price
            atr = indicators.atr14 or 0.0
            trade_plan = self.risk_engine.calculate(validated, entry_price, atr, config.initial_balance)

            # Step 6 — Signal
            signal = self.signal_engine.generate(trade_plan)

            # Step 7 — Paper Execution
            if signal.status == "ACTIVE":
                self.paper_trading_engine.execute(signal)

            # Step 8 — Cek SL/TP menggunakan high/low candle
            open_positions = self.portfolio_manager.repo.get_open()
            for pos in open_positions:
                # Cek Stop Loss (prioritas pertama)
                if pos.side == Side.LONG and snapshot.low <= pos.stop_loss:
                    self._close_position(pos, pos.stop_loss, trades, snapshot.timestamp)
                elif pos.side == Side.SHORT and snapshot.high >= pos.stop_loss:
                    self._close_position(pos, pos.stop_loss, trades, snapshot.timestamp)
                # Cek Take Profit
                elif pos.side == Side.LONG and snapshot.high >= pos.take_profit:
                    self._close_position(pos, pos.take_profit, trades, snapshot.timestamp)
                elif pos.side == Side.SHORT and snapshot.low <= pos.take_profit:
                    self._close_position(pos, pos.take_profit, trades, snapshot.timestamp)

        # Tutup semua posisi yang masih terbuka di akhir backtest
        last_price = snapshots[-1].current_price if snapshots else 0
        for pos in self.portfolio_manager.repo.get_open():
            self._close_position(pos, last_price, trades, snapshots[-1].timestamp)

        # Hitung metrik
        final_state = self.portfolio_manager.get_state()
        winning = [t for t in trades if t.net_pnl > 0]
        losing = [t for t in trades if t.net_pnl < 0]
        total_pnl = sum(t.net_pnl for t in trades)
        win_rate = len(winning) / len(trades) if trades else 0.0
        total_return = (final_state.equity - config.initial_balance) / config.initial_balance * 100

        # Drawdown dari equity curve
        max_dd = 0.0
        max_dd_pct = 0.0
        for pt in self._equity_curve:
            if pt.drawdown > max_dd:
                max_dd = pt.drawdown
                max_dd_pct = pt.drawdown_percent

        total_fees = sum(t.fees for t in trades)
        gross_profit = sum(t.gross_pnl for t in trades if t.gross_pnl > 0)
        gross_loss = abs(sum(t.gross_pnl for t in trades if t.gross_pnl < 0))

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
            max_drawdown=max_dd,
            max_drawdown_percent=max_dd_pct,
            open_positions=0,
            closed_positions=len(trades),
            trades=trades,
            equity_curve=self._equity_curve,
            total_fees=total_fees,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            start_time=snapshots[0].timestamp,
            end_time=snapshots[-1].timestamp,
        )

    def _close_position(self, pos, exit_price, trades_list, exit_timestamp: datetime):
        # Gross PnL
        if pos.side == Side.LONG:
            gross_pnl = (exit_price - pos.entry_price) * pos.position_size
        else:
            gross_pnl = (pos.entry_price - exit_price) * pos.position_size

        # Fee
        fees = self.cost_model.calculate(pos.entry_price, exit_price, pos.position_size)
        net_pnl = gross_pnl - fees

        closed = self.paper_trading_engine.close_position(pos.position_id, exit_price)
        if closed:
            trades_list.append(TradeRecord(
                trade_id=uuid4(),
                symbol=pos.symbol,
                side="LONG" if pos.side == Side.LONG else "SHORT",
                entry_price=pos.entry_price,
                exit_price=exit_price,
                position_size=pos.position_size,
                pnl=net_pnl,
                status="WIN" if net_pnl > 0 else ("LOSS" if net_pnl < 0 else "BREAKEVEN"),
                entry_timestamp=pos.opened_at,
                exit_timestamp=exit_timestamp,
                gross_pnl=gross_pnl,
                fees=fees,
                net_pnl=net_pnl,
            ))
            self._add_equity_point(exit_timestamp)

    def _add_equity_point(self, ts: datetime):
        state = self.portfolio_manager.get_state()
        equity = state.equity
        peak = self.portfolio_manager.peak_equity
        drawdown = peak - equity
        drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0.0
        self._equity_curve.append(EquityPoint(
            timestamp=ts,
            equity=equity,
            drawdown=drawdown,
            drawdown_percent=round(drawdown_pct, 2),
        ))