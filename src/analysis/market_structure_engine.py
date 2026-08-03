"""Market Structure Engine — deteksi Swing High/Low, BOS, CHoCH."""

from datetime import UTC, datetime

from src.core.models.candle import Candle
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import MarketStructure, TrendDirection


class MarketStructureEngine:
    """Deteksi market structure dari price action."""

    SWING_WINDOW = 3  # N candle sebelum dan sesudah

    def analyze(
        self,
        candles: list[Candle],
        trend: TrendDirection,
        previous_structure: MarketStructure = MarketStructure.NONE,
    ) -> MarketStructureResult:
        """
        Analisa market structure dari list candle.
        
        Args:
            candles: list[Candle] dari NormalizedAsset.candles_4h
            trend: TrendDirection dari TrendEngine
            previous_structure: MarketStructure sebelumnya (untuk deteksi CHoCH)
        """
        if len(candles) < (self.SWING_WINDOW * 2 + 1):
            return MarketStructureResult(
                structure=MarketStructure.NONE,
                direction=trend,
                timestamp=datetime.now(UTC),
            )

        swing_high = self._find_swing_high(candles)
        swing_low = self._find_swing_low(candles)

        if swing_high is None or swing_low is None:
            return MarketStructureResult(
                structure=MarketStructure.NONE,
                direction=trend,
                timestamp=datetime.now(UTC),
            )

        current_close = candles[-1].close

        # CHoCH Bullish: setelah bearish (BOS_BEARISH), close break swing high
        if (
            previous_structure == MarketStructure.BOS_BEARISH
            and trend == TrendDirection.BULLISH
            and current_close > swing_high
        ):
            return MarketStructureResult(
                structure=MarketStructure.CHOCH,
                direction=trend,
                swing_high=swing_high,
                swing_low=swing_low,
                timestamp=datetime.now(UTC),
            )

        # CHoCH Bearish: setelah bullish (BOS_BULLISH), close break swing low
        if (
            previous_structure == MarketStructure.BOS_BULLISH
            and trend == TrendDirection.BEARISH
            and current_close < swing_low
        ):
            return MarketStructureResult(
                structure=MarketStructure.CHOCH,
                direction=trend,
                swing_high=swing_high,
                swing_low=swing_low,
                timestamp=datetime.now(UTC),
            )

        # BOS Bullish
        if current_close > swing_high:
            return MarketStructureResult(
                structure=MarketStructure.BOS_BULLISH,
                direction=trend,
                swing_high=swing_high,
                swing_low=swing_low,
                timestamp=datetime.now(UTC),
            )

        # BOS Bearish
        if current_close < swing_low:
            return MarketStructureResult(
                structure=MarketStructure.BOS_BEARISH,
                direction=trend,
                swing_high=swing_high,
                swing_low=swing_low,
                timestamp=datetime.now(UTC),
            )

        return MarketStructureResult(
            structure=MarketStructure.NONE,
            direction=trend,
            swing_high=swing_high,
            swing_low=swing_low,
            timestamp=datetime.now(UTC),
        )

    def _find_swing_high(self, candles: list[Candle]) -> float | None:
        n = self.SWING_WINDOW
        for i in range(len(candles) - 1 - n, n - 1, -1):
            current_high = candles[i].high
            is_swing = True
            for j in range(i - n, i + n + 1):
                if j != i and candles[j].high >= current_high:
                    is_swing = False
                    break
            if is_swing:
                return current_high
        return None

    def _find_swing_low(self, candles: list[Candle]) -> float | None:
        n = self.SWING_WINDOW
        for i in range(len(candles) - 1 - n, n - 1, -1):
            current_low = candles[i].low
            is_swing = True
            for j in range(i - n, i + n + 1):
                if j != i and candles[j].low <= current_low:
                    is_swing = False
                    break
            if is_swing:
                return current_low
        return None