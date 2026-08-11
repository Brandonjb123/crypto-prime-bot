"""Performance Analytics Engine — menganalisis BacktestResult."""

from datetime import UTC, datetime

from src.core.models.backtest_11b import BacktestResult
from src.core.models.performance_report import PerformanceReport


class PerformanceAnalyticsEngine:
    def analyze(self, result: BacktestResult) -> PerformanceReport:
        trades = result.trades
        closed_trades = [t for t in trades if t.status in ("WIN", "LOSS", "BREAKEVEN")]
        winning = [t for t in closed_trades if t.pnl > 0]
        losing = [t for t in closed_trades if t.pnl < 0]

        # Basic metrics
        total_trades = len(closed_trades)
        winning_count = len(winning)
        losing_count = len(losing)
        win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0.0

        # Average win/loss
        avg_win = sum(t.pnl for t in winning) / winning_count if winning_count > 0 else 0.0
        avg_loss = abs(sum(t.pnl for t in losing)) / losing_count if losing_count > 0 else 0.0

        # Profit factor
        gross_profit = sum(t.pnl for t in winning)
        gross_loss = abs(sum(t.pnl for t in losing))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None

        # Expectancy
        if total_trades > 0:
            win_rate_decimal = winning_count / total_trades
            loss_rate_decimal = losing_count / total_trades
            expectancy = (win_rate_decimal * avg_win) - (loss_rate_decimal * avg_loss)
        else:
            expectancy = 0.0

        # Net profit
        net_profit = result.final_balance - result.initial_balance

        # Total return
        if result.initial_balance > 0:
            total_return = (net_profit / result.initial_balance) * 100
        else:
            total_return = 0.0

        # Long/short analysis
        long_trades = [t for t in closed_trades if t.side == "BUY" or t.side == "LONG"]
        short_trades = [t for t in closed_trades if t.side == "SELL" or t.side == "SHORT"]
        long_wins = [t for t in long_trades if t.pnl > 0]
        short_wins = [t for t in short_trades if t.pnl > 0]
        long_win_rate = (len(long_wins) / len(long_trades) * 100) if long_trades else 0.0
        short_win_rate = (len(short_wins) / len(short_trades) * 100) if short_trades else 0.0

        return PerformanceReport(
            initial_balance=result.initial_balance,
            final_balance=result.final_balance,
            net_profit=net_profit,
            total_return_percent=round(total_return, 2),
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            win_rate=round(win_rate, 2),
            average_win=round(avg_win, 2),
            average_loss=round(avg_loss, 2),
            profit_factor=round(profit_factor, 2) if profit_factor is not None else None,
            expectancy=round(expectancy, 2),
            max_drawdown=result.max_drawdown,
            max_drawdown_percent=result.max_drawdown_percent,
            long_trades=len(long_trades),
            short_trades=len(short_trades),
            long_wins=len(long_wins),
            short_wins=len(short_wins),
            long_win_rate=round(long_win_rate, 2),
            short_win_rate=round(short_win_rate, 2),
            timestamp=datetime.now(UTC),
        )