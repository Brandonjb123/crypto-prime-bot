from src.core.models.backtest import TradeRecord, TradeOutcome
from src.backtest.metrics import calculate_metrics


def make_trade(pnl, outcome=TradeOutcome.WIN):
    return TradeRecord(symbol="BTCUSDT", side="LONG", entry_price=100.0, exit_price=100.0+pnl, position_size=1.0, pnl=pnl, outcome=outcome)


class TestMetrics:
    def test_win_rate(self):
        trades = [make_trade(10.0, TradeOutcome.WIN), make_trade(-5.0, TradeOutcome.LOSS)]
        metrics = calculate_metrics(trades)
        assert metrics["win_rate"] == 0.5

    def test_net_profit(self):
        trades = [make_trade(10.0), make_trade(-5.0, TradeOutcome.LOSS)]
        metrics = calculate_metrics(trades)
        assert metrics["net_profit"] == 5.0

    def test_profit_factor(self):
        trades = [make_trade(10.0), make_trade(-5.0, TradeOutcome.LOSS)]
        metrics = calculate_metrics(trades)
        assert metrics["profit_factor"] == 2.0

    def test_max_drawdown(self):
        trades = [
            make_trade(10.0),
            make_trade(-15.0, TradeOutcome.LOSS),
            make_trade(5.0),
        ]
        metrics = calculate_metrics(trades)
        # Peak after first trade = 10, after second = -5 (drawdown 15), after third = 0 (drawdown from peak 10)
        assert metrics["max_drawdown"] == 15.0

    def test_empty_trades(self):
        metrics = calculate_metrics([])
        assert metrics["win_rate"] == 0.0
        assert metrics["net_profit"] == 0.0