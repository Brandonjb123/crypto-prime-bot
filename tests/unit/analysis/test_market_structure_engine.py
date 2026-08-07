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

            candles.append(
                Candle(
                    timestamp=ts,
                    open=price,
                    high=price + 5,
                    low=price - 5,
                    close=price,
                    volume=100.0,
                )
            )

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

            candles.append(
                Candle(
                    timestamp=ts,
                    open=price,
                    high=price + 5,
                    low=price - 5,
                    close=price,
                    volume=100.0,
                )
            )

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

            candles.append(
                Candle(
                    timestamp=ts,
                    open=price,
                    high=price + 5,
                    low=price - 5,
                    close=price,
                    volume=100.0,
                )
            )

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

    def test_choch_bullish(self):
        """Bearish break dulu, lalu reversal break swing high → CHOCH."""
        engine = MarketStructureEngine()
        # 24 candle: downtrend, break swing low, lalu reversal break swing high
        base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        candles = []
        for i in range(24):
            ts = base_time + timedelta(hours=4 * i)
            if i < 10:
                price = 100.0 - i * 5  # turun
            elif i == 10:
                price = 45.0  # swing low
            elif i < 14:
                price = 50.0 + (i - 10) * 5  # naik pelan
            elif i < 18:
                price = 70.0 - (i - 14) * 3  # turun lagi, break swing low?
            elif i == 18:
                price = 30.0  # break swing low jelas
            elif i < 22:
                price = 40.0 + (i - 18) * 10  # reversal naik cepat
            else:
                price = 120.0  # break swing high (sebelumnya swing high ~95)

            candles.append(
                Candle(
                    timestamp=ts,
                    open=price,
                    high=price + 5,
                    low=price - 5,
                    close=price,
                    volume=100.0,
                )
            )

        # Simulasi: sebelumnya terjadi BOS_BEARISH (dari candle i=18), lalu reversal
        result = engine.analyze(
            candles,
            trend=TrendDirection.BULLISH,
            previous_structure=MarketStructure.BOS_BEARISH,
        )

        assert result.structure == MarketStructure.CHOCH
        assert result.direction == TrendDirection.BULLISH

    def test_choch_bearish(self):
        """Bullish break dulu, lalu reversal break swing low → CHOCH."""
        engine = MarketStructureEngine()
        base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        candles = []
        for i in range(24):
            ts = base_time + timedelta(hours=4 * i)
            if i < 10:
                price = 50.0 + i * 5  # naik
            elif i == 10:
                price = 100.0  # swing high
            elif i < 14:
                price = 90.0 - (i - 10) * 5  # turun pelan
            elif i < 18:
                price = 80.0 + (i - 14) * 3  # naik lagi, break swing high?
            elif i == 18:
                price = 120.0  # break swing high
            elif i < 22:
                price = 100.0 - (i - 18) * 15  # reversal turun cepat
            else:
                price = 30.0  # break swing low (sebelumnya swing low ~45)

            candles.append(
                Candle(
                    timestamp=ts,
                    open=price,
                    high=price + 5,
                    low=price - 5,
                    close=price,
                    volume=100.0,
                )
            )

        result = engine.analyze(
            candles,
            trend=TrendDirection.BEARISH,
            previous_structure=MarketStructure.BOS_BULLISH,
        )

        assert result.structure == MarketStructure.CHOCH
        assert result.direction == TrendDirection.BEARISH
