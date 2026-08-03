"""ATR (Average True Range) calculator — Wilder's Smoothing."""

from src.core.models.candle import Candle


class ATRCalculator:
    """Calculate ATR dengan True Range dan Wilder's Smoothing."""

    def calculate(self, candles: list[Candle], period: int = 14) -> float | None:
        """
        Hitung ATR untuk period tertentu.
        
        Args:
            candles: List of Candle objects, minimal length = period + 1
            period: ATR period (default 14)
            
        Returns:
            ATR value positif, atau None jika data tidak cukup
        """
        if len(candles) < period + 1:
            return None

        # True Range: skip candle pertama (tidak ada prev_close)
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i - 1].close

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            true_ranges.append(tr)

        # Initial ATR: simple average dari 'period' true range pertama
        atr = sum(true_ranges[:period]) / period

        # Wilder's Smoothing untuk sisa true range
        for i in range(period, len(true_ranges)):
            atr = (atr * (period - 1) + true_ranges[i]) / period

        return round(atr, 2)