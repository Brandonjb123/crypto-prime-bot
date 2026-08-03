"""RSI (Relative Strength Index) calculator — Wilder's Smoothing."""

from src.core.models.candle import Candle


class RSICalculator:
    """Calculate RSI dengan Wilder's Smoothing."""

    def calculate(self, candles: list[Candle], period: int = 14) -> float | None:
        """
        Hitung RSI untuk period tertentu.
        
        Args:
            candles: List of Candle objects, minimal length = period + 1
            period: RSI period (default 14)
            
        Returns:
            RSI value antara 0-100, atau None jika data tidak cukup
        """
        if len(candles) < period + 1:
            return None

        closes = [c.close for c in candles]

        # Perubahan harga dari candle ke candle
        changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

        # Initial avg gain/loss: simple average dari 'period' pertama
        gains = [max(c, 0) for c in changes[:period]]
        losses = [max(-c, 0) for c in changes[:period]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        # Wilder's Smoothing untuk sisa perubahan
        for i in range(period, len(changes)):
            change = changes[i]
            gain = max(change, 0)
            loss = max(-change, 0)

            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)