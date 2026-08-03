"""Unit tests untuk EMACalculator."""

from datetime import UTC, datetime, timedelta

from src.analysis.indicators.ema import EMACalculator
from src.core.models.candle import Candle


def make_candles(prices: list[float], start_hour: int = 0) -> list[Candle]:
    """Helper: buat candle dari list harga close."""
    candles = []
    for i, close in enumerate(prices):
        ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC) + timedelta(hours=start_hour + 4 * i)
        candles.append(
            Candle(
                timestamp=ts,
                open=close * 0.99,
                high=close * 1.01,
                low=close * 0.98,
                close=close,
                volume=1000.0,
            )
        )
    return candles


def make_trend_candles(n: int, start: float, step: float) -> list[Candle]:
    """Helper: buat n candle dengan close naik/turun sebesar step."""
    candles = []
    for i in range(n):
        ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC) + timedelta(hours=4 * i)
        close = start + i * step
        candles.append(
            Candle(
                timestamp=ts,
                open=close - step * 0.3,
                high=close + abs(step) * 0.2,
                low=close - abs(step) * 0.2,
                close=close,
                volume=1000.0,
            )
        )
    return candles


class TestEMACalculator:
    def test_ema20_sufficient_candles(self):
        calc = EMACalculator()
        candles = make_candles([100.0 + i * 0.1 for i in range(25)])
        result = calc.calculate(candles, period=20)
        assert isinstance(result, float)
        assert result > 100.0

    def test_ema50_sufficient_candles(self):
        calc = EMACalculator()
        candles = make_candles([100.0 + i * 0.05 for i in range(55)])
        result = calc.calculate(candles, period=50)
        assert isinstance(result, float)
        assert result > 100.0

    def test_ema20_insufficient_candles(self):
        calc = EMACalculator()
        candles = make_candles([100.0] * 15)
        result = calc.calculate(candles, period=20)
        assert result is None

    def test_bullish_ema20_gt_ema50(self):
        """Bullish trend: EMA20 > EMA50."""
        calc = EMACalculator()
        candles = make_trend_candles(60, 100.0, 0.5)  # Harga naik 0.5 per candle
        ema20 = calc.calculate(candles, period=20)
        ema50 = calc.calculate(candles, period=50)
        assert ema20 > ema50

    def test_bearish_ema20_lt_ema50(self):
        """Bearish trend: EMA20 < EMA50."""
        calc = EMACalculator()
        candles = make_trend_candles(60, 200.0, -0.5)  # Harga turun 0.5 per candle
        ema20 = calc.calculate(candles, period=20)
        ema50 = calc.calculate(candles, period=50)
        assert ema20 < ema50