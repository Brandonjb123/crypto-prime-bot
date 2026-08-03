"""Market Structure Engine — deteksi Swing High/Low, BOS, CHoCH."""

from datetime import UTC, datetime

from src.analysis.swing_detection import find_swing_high, find_swing_low
from src.core.models.candle import Candle
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import MarketStructure, TrendDirection


class MarketStructureEngine:
    """Deteksi market structure dari price action."""

    SWING_WINDOW = 3

    def analyze(
        self,
        candles: list[Candle],
        trend: TrendDirection,
        previous_structure: MarketStructure = MarketStructure.NONE,
    ) -> MarketStructureResult:
        if len(candles) < (self.SWING_WINDOW * 2 + 1):
            return MarketStructureResult(
                structure=MarketStructure.NONE,
                direction=trend,
                timestamp=datetime.now(UTC),
            )

        swing_high = find_swing_high(candles, self.SWING_WINDOW)
        swing_low = find_swing_low(candles, self.SWING_WINDOW)

        if swing_high is None or swing_low is None:
            return MarketStructureResult(
                structure=MarketStructure.NONE,
                direction=trend,
                timestamp=datetime.now(UTC),
            )

        current_close = candles[-1].close

        # CHoCH Bullish
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

        # CHoCH Bearish
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