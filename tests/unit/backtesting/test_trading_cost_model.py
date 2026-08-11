from src.backtesting.trading_cost_model import TradingCostModel


def test_zero_commission():
    model = TradingCostModel(commission_rate=0.0)
    fee = model.calculate(50000.0, 51000.0, 0.01)
    assert fee == 0.0

def test_non_zero_commission():
    model = TradingCostModel(commission_rate=0.001)  # 0.1%
    fee = model.calculate(50000.0, 51000.0, 0.01)
    # entry_notional = 500, exit_notional = 510, total = 1010
    # fee = 1010 * 0.001 = 1.01
    assert fee == 1.01