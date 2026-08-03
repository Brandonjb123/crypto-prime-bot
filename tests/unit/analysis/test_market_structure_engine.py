"""Unit tests untuk MarketStructureEngine."""

from datetime import UTC, datetime, timedelta

from src.analysis.market_structure_engine import MarketStructureEngine
from src.core.models.candle import Candle
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import MarketStructure, TrendDirection


def make_candles(scenario: str = "with_swings") -> list[Candle]:
    """Buat candle fixture dengan swing points yang jelas."""
    candles = []
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)

    if scenario == "with_swings":
        # 24 candle: uptrend pelan, swing high di index 11, swing low di index 16
        for i in range(24):
            ts = base_time + timedelta(hours=4 * i)
            if i < 11:
                price = 100.0 + i * 5
            elif i == 11:
                price = 160.0  # swing high
            elif i < 16:
                price = 160.0 - (i - 11) * 7  # turun ke ~125
            else:
                price = 125.0 + (i - 16) * 3  # naik lagi, tidak break 160

            candles.append(Candle(
                timestamp=ts, open=price, high=price + 5,
                low=price - 5, close=price, volume=100.0
            ))

    elif scenario == "bos_bullish":
        # Break swing high: harga terakhir > swing high (160)
        for i in range(24):
            ts = base_time + timedelta(hours=4 * i)
            if i < 11:
                price = 100.0 + i * 5
            elif i == 11:
                price = 160.0  # swing high
            elif i < 16:
                price = 160.0 - (i - 11) * 7
            elif i < 22:
                price = 125.0 + (i - 16) * 3
            else:
                price = 175.0  # break swing high

            candles.append(Candle(
                timestamp=ts, open=price, high=price + 5,
                low=price - 5, close=price, volume=100.0
            ))

    elif scenario == "bos_bearish":
        # Break swing low: harga terakhir < swing low (40)
        for i in range(24):
            ts = base_time + timedelta(hours=4 * i)
            if i < 11:
                price = 100.0 - i * 5
            elif i == 11:
                price = 40.0  # swing low
            elif i < 16:
                price = 40.0 + (i - 11) * 7  # naik ke ~75
            elif i < 22:
                price = 75.0 - (i - 16) * 3  # turun lagi
            else:
                price = 25.0  # break swing low

            candles.append(Candle(
                timestamp=ts, open=price, high=price + 5,
                low=price - 5, close=price, volume=100.0
            ))

    return candles


class TestMarketStructureEngine:
    def test_bos_bullish(self):
        engine = MarketStructureEngine()
        candles = make_candles("bos_bullish")
        result = engine.analyze(candles, TrendDirection.BULLISH)

        assert isinstance(result, MarketStructureResult)
        assert result.structure == MarketStructure.BOS_BULLISH
        assert result.swing_high is not None
        assert result.swing_low is not None

    def test_bos_bearish(self):
        engine = MarketStructureEngine()
        candles = make_candles("bos_bearish")
        result = engine.analyze(candles, TrendDirection.BEARISH)

        assert isinstance(result, MarketStructureResult)
        assert result.structure == MarketStructure.BOS_BEARISH
        assert result.swing_high is not None
        assert result.swing_low is not None

    def test_no_structure(self):
        engine = MarketStructureEngine()
        candles = make_candles("with_swings")
        result = engine.analyze(candles, TrendDirection.BULLISH)

        assert result.structure == MarketStructure.NONE
        assert result.swing_high is not None
        assert result.swing_low is not None
        assert result.swing_high > result.swing_low

    def test_insufficient_candles(self):
        engine = MarketStructureEngine()
        candles = make_candles("with_swings")[:6]
        result = engine.analyze(candles, TrendDirection.BULLISH)

        assert result.structure == MarketStructure.NONE
        assert result.swing_high is None
        assert result.swing_low is None

    def test_swing_points_detected(self):
        engine = MarketStructureEngine()
        candles = make_candles("with_swings")
        result = engine.analyze(candles, TrendDirection.BULLISH)

        assert result.swing_high is not None
        assert result.swing_low is not None
        assert result.swing_high > result.swing_low