"""Unit tests untuk ATRCalculator."""

from datetime import UTC, datetime, timedelta

from src.analysis.indicators.atr import ATRCalculator
from src.core.models.candle import Candle


def make_candles(
    n: int,
    start_price: float = 100.0,
    volatility: float = 0.02,
) -> list[Candle]:
    """
    Buat candle untuk testing ATR.
    volatility: 0.02 = 2% range high-low dari close.
    """
    candles = []
    price = start_price
    for i in range(n):
        ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC) + timedelta(hours=4 * i)
        high = price * (1 + volatility)
        low = price * (1 - volatility)
        open_p = price
        close = price * (1 + volatility * 0.5)  # sedikit naik
        candles.append(
            Candle(
                timestamp=ts,
                open=open_p,
                high=high,
                low=low,
                close=close,
                volume=1000.0,
            )
        )
        price = close  # prev_close untuk candle berikutnya
    return candles


class TestATRCalculator:
    def test_atr_high_volatility(self):
        """Volatilitas tinggi → ATR besar."""
        calc = ATRCalculator()
        candles = make_candles(30, start_price=100.0, volatility=0.05)  # 5%
        result = calc.calculate(candles, period=14)
        assert result is not None
        assert result > 0.5  # ATR harus signifikan

    def test_atr_low_volatility(self):
        """Volatilitas rendah → ATR kecil."""
        calc = ATRCalculator()
        candles = make_candles(30, start_price=100.0, volatility=0.001)  # 0.1%
        result = calc.calculate(candles, period=14)
        assert result is not None
        assert result < 0.5

    def test_atr_high_gt_low(self):
        """ATR volatilitas tinggi > ATR volatilitas rendah."""
        calc = ATRCalculator()
        high_vol = make_candles(30, start_price=100.0, volatility=0.05)
        low_vol = make_candles(30, start_price=100.0, volatility=0.001)
        atr_high = calc.calculate(high_vol, period=14)
        atr_low = calc.calculate(low_vol, period=14)
        assert atr_high > atr_low

    def test_atr_insufficient_candles(self):
        """Kurang dari period + 1 → None."""
        calc = ATRCalculator()
        candles = make_candles(10, start_price=100.0, volatility=0.02)
        result = calc.calculate(candles, period=14)
        assert result is None

    def test_atr_positive(self):
        """ATR harus positif."""
        calc = ATRCalculator()
        candles = make_candles(30, start_price=100.0, volatility=0.02)
        result = calc.calculate(candles, period=14)
        assert result > 0
