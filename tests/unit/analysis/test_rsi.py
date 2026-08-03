"""Unit tests untuk RSICalculator."""

from datetime import UTC, datetime, timedelta

from src.analysis.indicators.rsi import RSICalculator
from src.core.models.candle import Candle


def make_rsi_candles(
    n: int,
    start_price: float = 100.0,
    trend: str = "bullish",
    noise: float = 0.1,
) -> list[Candle]:
    """
    Buat candle untuk testing RSI.
    - bullish: close naik stabil
    - bearish: close turun stabil
    """
    candles = []
    price = start_price
    for i in range(n):
        ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC) + timedelta(hours=4 * i)
        if trend == "bullish":
            price += noise
        else:
            price -= noise
        open_p = price - noise * 0.5
        high = price + noise * 0.8
        low = price - noise * 0.8
        candles.append(
            Candle(
                timestamp=ts,
                open=open_p,
                high=high,
                low=low,
                close=price,
                volume=1000.0,
            )
        )
    return candles


class TestRSICalculator:
    def test_rsi_bullish_above_50(self):
        """Bullish trend → RSI > 50."""
        calc = RSICalculator()
        candles = make_rsi_candles(30, start_price=100.0, trend="bullish", noise=0.5)
        result = calc.calculate(candles, period=14)
        assert result is not None
        assert result > 50.0

    def test_rsi_bearish_below_50(self):
        """Bearish trend → RSI < 50."""
        calc = RSICalculator()
        candles = make_rsi_candles(30, start_price=200.0, trend="bearish", noise=0.5)
        result = calc.calculate(candles, period=14)
        assert result is not None
        assert result < 50.0

    def test_rsi_range_0_100(self):
        """RSI harus antara 0–100."""
        calc = RSICalculator()
        candles = make_rsi_candles(30, start_price=100.0, trend="bullish", noise=0.3)
        result = calc.calculate(candles, period=14)
        assert 0 <= result <= 100

    def test_rsi_insufficient_candles(self):
        """Kurang dari period + 1 → None."""
        calc = RSICalculator()
        candles = make_rsi_candles(10, start_price=100.0, trend="bullish")
        result = calc.calculate(candles, period=14)
        assert result is None

    def test_rsi_all_prices_equal(self):
        """Harga tidak berubah → gain/loss 0 → RSI 100."""
        calc = RSICalculator()
        candles = make_rsi_candles(30, start_price=100.0, noise=0.0)
        result = calc.calculate(candles, period=14)
        assert result == 100.0