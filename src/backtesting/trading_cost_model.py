"""Trading Cost Model — menghitung fee trading."""


class TradingCostModel:
    def __init__(self, commission_rate: float = 0.0):
        self.commission_rate = commission_rate

    def calculate(self, entry_price: float, exit_price: float, position_size: float) -> float:
        """Hitung total fee (entry + exit) berdasarkan notional value."""
        entry_notional = entry_price * position_size
        exit_notional = exit_price * position_size
        entry_fee = entry_notional * self.commission_rate
        exit_fee = exit_notional * self.commission_rate
        return entry_fee + exit_fee