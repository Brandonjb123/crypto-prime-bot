"""Support & Resistance Engine — deteksi dari swing high/low."""

from datetime import UTC, datetime

from src.core.models.candle import Candle
from src.core.models.market_intelligence import SupportResistanceResult


class SupportResistanceEngine:
    """Deteksi support dan resistance terdekat dari swing points."""

    SWING_WINDOW = 3

    def analyze(self, candles: list[Candle], price: float) -> SupportResistanceResult:
        """Cari support dan resistance berdasarkan swing high/low terbaru."""
        if len(candles) < (self.SWING_WINDOW * 2 + 1):
            return SupportResistanceResult(
                nearest_support=None,
                nearest_resistance=None,
                price_position=0.5,
                confidence_score=0.3,
                timestamp=datetime.now(UTC),
            )

        # Ambil semua swing points
        swing_highs = self._get_all_swing_highs(candles)
        swing_lows = self._get_all_swing_lows(candles)

        # Nearest resistance: swing high terkecil yang > price
        resistance = min([h for h in swing_highs if h > price], default=None)
        # Nearest support: swing low terbesar yang < price
        support = max([low_val for low_val in swing_lows if low_val < price], default=None)

        if support is not None and resistance is not None:
            pos = (price - support) / (resistance - support)
            pos = max(0.0, min(1.0, pos))
            confidence = 0.8
        elif support is not None or resistance is not None:
            pos = 0.5
            confidence = 0.5
        else:
            pos = 0.5
            confidence = 0.3

        return SupportResistanceResult(
            nearest_support=support,
            nearest_resistance=resistance,
            price_position=pos,
            confidence_score=confidence,
            timestamp=datetime.now(UTC),
        )

    def _get_all_swing_highs(self, candles: list[Candle]) -> list[float]:
        """Kumpulkan semua swing highs."""
        highs = []
        for i in range(self.SWING_WINDOW, len(candles) - self.SWING_WINDOW):
            current_high = candles[i].high
            is_swing = True
            for j in range(i - self.SWING_WINDOW, i + self.SWING_WINDOW + 1):
                if j != i and candles[j].high >= current_high:
                    is_swing = False
                    break
            if is_swing:
                highs.append(current_high)
        return highs

    def _get_all_swing_lows(self, candles: list[Candle]) -> list[float]:
        """Kumpulkan semua swing lows."""
        lows = []
        for i in range(self.SWING_WINDOW, len(candles) - self.SWING_WINDOW):
            current_low = candles[i].low
            is_swing = True
            for j in range(i - self.SWING_WINDOW, i + self.SWING_WINDOW + 1):
                if j != i and candles[j].low <= current_low:
                    is_swing = False
                    break
            if is_swing:
                lows.append(current_low)
        return lows
