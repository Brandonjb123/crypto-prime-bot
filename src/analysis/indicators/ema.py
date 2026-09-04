"""EMA (Exponential Moving Average) calculator."""

from src.core.models.candle import Candle


class EMACalculator:
    """Calculate EMA untuk period tertentu."""

    def calculate(self, candles: list[Candle], period: int) -> float | None:
        """
        Hitung EMA untuk period tertentu.

        Args:
            candles: List of Candle objects, minimal length = period + 1
            period: EMA period (contoh: 20, 50)

        Returns:
            EMA value atau None jika data tidak cukup
        """
        if len(candles) < period:
            return None

        # Seed: simple average dari period candle pertama
        closes = [c.close for c in candles]
        seed = sum(closes[:period]) / period

        multiplier = 2 / (period + 1)

        # EMA = (close - prev_ema) * multiplier + prev_ema
        ema = seed
        for i in range(period, len(closes)):
            ema = (closes[i] - ema) * multiplier + ema

        return round(ema, 2)
