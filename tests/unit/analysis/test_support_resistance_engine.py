"""Unit tests untuk SupportResistanceEngine."""

from datetime import UTC, datetime, timedelta

from src.analysis.support_resistance_engine import SupportResistanceEngine
from src.core.models.candle import Candle
from src.core.models.market_intelligence import SupportResistanceResult


def make_candles(scenario: str = "with_swings") -> list[Candle]:
    """Helper: buat candle dengan swing points jelas."""
    candles = []
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)

    if scenario == "with_swings":
        # 24 candle: swing high 180, swing low 80
        for i in range(24):
            ts = base_time + timedelta(hours=4 * i)
            if i < 6:
                price = 100.0 + i * 5  # naik ke 130
            elif i < 8:
                price = 130.0 + (i - 6) * 15  # naik ke 160
            elif i == 8:
                price = 180.0  # swing high
            elif i < 12:
                price = 180.0 - (i - 8) * 20  # turun ke 100
            elif i == 12:
                price = 80.0  # swing low
            elif i < 18:
                price = 80.0 + (i - 12) * 10  # naik ke 140
            else:
                price = 140.0 - (i - 18) * 5  # turun pelan ke 110

            candles.append(Candle(
                timestamp=ts, open=price, high=price + 5,
                low=price - 5, close=price, volume=100.0
            ))

    return candles


class TestSupportResistanceEngine:
    def test_support_resistance_detected(self):
        """Swing points jelas → support & resistance terisi."""
        engine = SupportResistanceEngine()
        candles = make_candles("with_swings")
        result = engine.analyze(candles, price=130.0)

        assert isinstance(result, SupportResistanceResult)
        assert result.nearest_support is not None
        assert result.nearest_resistance is not None
        assert result.nearest_support < 130.0 < result.nearest_resistance
        assert 0.0 <= result.price_position <= 1.0
        assert result.confidence_score == 0.8

    def test_price_position_range(self):
        """price_position antara 0.0-1.0, harga di antara support & resistance."""
        engine = SupportResistanceEngine()
        candles = make_candles("with_swings")

        # Harga dekat support (tapi masih di atas support)
        result_low = engine.analyze(candles, price=85.0)
        assert result_low.nearest_support is not None
        assert result_low.nearest_resistance is not None
        assert 0.0 <= result_low.price_position <= 1.0
        assert result_low.price_position < 0.5  # lebih dekat ke support

        # Harga dekat resistance
        result_high = engine.analyze(candles, price=175.0)
        assert result_high.nearest_support is not None
        assert result_high.nearest_resistance is not None
        assert result_high.price_position > 0.5  # lebih dekat ke resistance

    def test_insufficient_candles(self):
        """< 7 candle → None values, confidence rendah."""
        engine = SupportResistanceEngine()
        candles = make_candles("with_swings")[:5]
        result = engine.analyze(candles, price=130.0)

        assert result.nearest_support is None
        assert result.nearest_resistance is None
        assert result.price_position == 0.5
        assert result.confidence_score == 0.3