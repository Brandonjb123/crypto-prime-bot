"""Market Structure Engine — deteksi Swing High/Low, BOS, CHoCH."""

from datetime import UTC, datetime

from src.core.models.candle import Candle
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import MarketStructure, TrendDirection


class MarketStructureEngine:
    """Deteksi market structure dari price action."""

    SWING_WINDOW = 3  # N candle sebelum dan sesudah

    def analyze(
        self, candles: list[Candle], trend: TrendDirection
    ) -> MarketStructureResult:
        """
        Analisa market structure dari list candle.
        
        Args:
            candles: list[Candle] dari NormalizedAsset.candles_4h
            trend: TrendDirection dari TrendEngine
            
        Returns:
            MarketStructureResult dengan structure, swing_high, swing_low
        """
        if len(candles) < (self.SWING_WINDOW * 2 + 1):
            return MarketStructureResult(
                structure=MarketStructure.NONE,
                direction=trend,
                timestamp=datetime.now(UTC),
            )

        # Deteksi swing high dan swing low terbaru
        swing_high = self._find_swing_high(candles)
        swing_low = self._find_swing_low(candles)

        if swing_high is None or swing_low is None:
            return MarketStructureResult(
                structure=MarketStructure.NONE,
                direction=trend,
                timestamp=datetime.now(UTC),
            )

        current_close = candles[-1].close

        # BOS Bullish: close > previous swing high
        if current_close > swing_high:
            return MarketStructureResult(
                structure=MarketStructure.BOS_BULLISH,
                direction=trend,
                swing_high=swing_high,
                swing_low=swing_low,
                timestamp=datetime.now(UTC),
            )

        # BOS Bearish: close < previous swing low
        if current_close < swing_low:
            return MarketStructureResult(
                structure=MarketStructure.BOS_BEARISH,
                direction=trend,
                swing_high=swing_high,
                swing_low=swing_low,
                timestamp=datetime.now(UTC),
            )

        # CHOCH Bullish: setelah bearish, close break swing high
        if trend == TrendDirection.BULLISH and current_close > swing_high:
            return MarketStructureResult(
                structure=MarketStructure.CHOCH,
                direction=trend,
                swing_high=swing_high,
                swing_low=swing_low,
                timestamp=datetime.now(UTC),
            )

        # CHOCH Bearish: setelah bullish, close break swing low
        if trend == TrendDirection.BEARISH and current_close < swing_low:
            return MarketStructureResult(
                structure=MarketStructure.CHOCH,
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
        """Cari swing high terbaru: high tertinggi di window N-N."""
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
        """Cari swing low terbaru: low terendah di window N-N."""
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