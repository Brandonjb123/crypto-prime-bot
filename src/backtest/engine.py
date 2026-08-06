"""Backtest Engine — menjalankan simulasi historical."""

from datetime import datetime, UTC, timedelta
from uuid import uuid4
from src.core.models.backtest import BacktestResult, HistoricalCandle, TradeRecord, TradeOutcome
from src.core.types.enums import BacktestStatus, PositionStatus, Side
from src.backtest.historical_provider import HistoricalPriceProvider
from src.backtest.candle_replay import CandleReplay
from src.backtest.metrics import calculate_metrics


class BacktestEngine:
    def __init__(
        self,
        orchestrator,
        paper_exchange,
        position_manager,
        portfolio_manager,
        lifecycle_engine=None,
    ):
        self.orchestrator = orchestrator
        self.paper_exchange = paper_exchange
        self.position_manager = position_manager
        self.portfolio_manager = portfolio_manager
        self.lifecycle_engine = lifecycle_engine
        self.price_provider = HistoricalPriceProvider()
        self.replay = CandleReplay()

    async def run(self, candles: list[HistoricalCandle], symbol: str = "BTCUSDT", timeframe: str = "4h") -> BacktestResult:
        if not candles:
            return BacktestResult(
                status=BacktestStatus.FAILED,
                symbol=symbol,
                timeframe=timeframe,
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                timestamp=datetime.now(UTC),
            )

        ordered = self.replay.replay(candles)
        trades: list[TradeRecord] = []
        self.price_provider.load(ordered)

        start_time = ordered[0].timestamp
        end_time = ordered[-1].timestamp

        for candle in ordered:
            # Update price provider ke harga close candle ini
            self.price_provider.update_price(symbol, candle.close)

            # Jalankan orchestrator untuk symbol ini
            ctx = await self.orchestrator.run(symbol, timeframe)

            # Jika ada posisi baru terbuka, catat trade
            if ctx.position and ctx.position.status == PositionStatus.OPEN:
                record = TradeRecord(
                    symbol=symbol,
                    side=ctx.position.side,
                    entry_price=ctx.position.entry_price,
                    position_size=ctx.position.position_size,
                    pnl=0.0,
                    outcome=TradeOutcome.OPEN,
                )
                trades.append(record)

            # Evaluasi posisi existing dengan lifecycle engine
            if self.lifecycle_engine:
                open_positions = self.position_manager.get_open_positions()
                for pos in open_positions:
                    updated = self.lifecycle_engine.evaluate(pos, candle.close)
                    if updated.status != PositionStatus.OPEN:
                        # Hitung PnL
                        if updated.side == Side.LONG:
                            pnl = (updated.last_price - updated.entry_price) * updated.position_size
                        else:
                            pnl = (updated.entry_price - updated.last_price) * updated.position_size

                        outcome = TradeOutcome.WIN if pnl > 0 else TradeOutcome.LOSS if pnl < 0 else TradeOutcome.BREAKEVEN

                        record = TradeRecord(
                            symbol=symbol,
                            side=updated.side,
                            entry_price=updated.entry_price,
                            exit_price=updated.last_price,
                            position_size=updated.position_size,
                            pnl=pnl,
                            outcome=outcome,
                        )
                        trades.append(record)
                        # Close position
                        self.position_manager.close_position(str(updated.position_id), updated.close_reason)

        # Hitung metrics
        metrics = calculate_metrics(trades)
        closed_trades = [t for t in trades if t.outcome != TradeOutcome.OPEN]
        wins = [t for t in closed_trades if t.outcome == TradeOutcome.WIN]
        losses = [t for t in closed_trades if t.outcome == TradeOutcome.LOSS]

        result = BacktestResult(
            status=BacktestStatus.COMPLETED,
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            total_trades=len(closed_trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=metrics["win_rate"],
            total_profit=sum(t.pnl for t in wins),
            total_loss=sum(t.pnl for t in losses),
            net_profit=metrics["net_profit"],
            max_drawdown=metrics["max_drawdown"],
            final_equity=10000.0 + metrics["net_profit"],  # asumsi initial capital
            trades=closed_trades,
            timestamp=datetime.now(UTC),
        )

        return result