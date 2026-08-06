"""Performance metrics calculator."""

from src.core.models.backtest import TradeRecord, TradeOutcome


def calculate_metrics(trades: list[TradeRecord]) -> dict:
    if not trades:
        return {
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "net_profit": 0.0,
            "max_drawdown": 0.0,
            "avg_trade": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }

    closed = [t for t in trades if t.outcome != TradeOutcome.OPEN]
    wins = [t for t in closed if t.outcome == TradeOutcome.WIN]
    losses = [t for t in closed if t.outcome == TradeOutcome.LOSS]

    win_rate = len(wins) / len(closed) if closed else 0.0
    total_profit = sum(t.pnl for t in wins)
    total_loss = sum(t.pnl for t in losses)
    net_profit = sum(t.pnl for t in closed)
    profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0.0

    # Drawdown sederhana: peak-to-valley
    equity_curve = []
    running = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in closed:
        running += t.pnl
        equity_curve.append(running)
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_dd:
            max_dd = dd

    best = max(t.pnl for t in closed) if closed else 0.0
    worst = min(t.pnl for t in closed) if closed else 0.0
    avg = net_profit / len(closed) if closed else 0.0

    return {
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 2),
        "net_profit": round(net_profit, 2),
        "max_drawdown": round(max_dd, 2),
        "avg_trade": round(avg, 2),
        "best_trade": round(best, 2),
        "worst_trade": round(worst, 2),
    }