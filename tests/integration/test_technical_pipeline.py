"""Integration test: NormalizedAsset → TechnicalAnalysis."""

from datetime import UTC, datetime, timedelta

from src.analysis.technical_engine import TechnicalAnalysisEngine
from src.core.models.analysis import TechnicalAnalysis
from src.core.models.candle import Candle
from src.core.models.normalized_asset import NormalizedAsset


def make_asset(candle_count: int) -> NormalizedAsset:
    """Helper: buat NormalizedAsset dengan n candle uptrend."""
    candles = []
    for i in range(candle_count):
        ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC) + timedelta(hours=4 * i)
        close = 45000.0 + i * 20.0
        candles.append(
            Candle(
                timestamp=ts,
                open=close - 10.0,
                high=close + 15.0,
                low=close - 15.0,
                close=close,
                volume=1000.0,
            )
        )
    return NormalizedAsset(
        symbol="BTC",
        price=45000.0 + candle_count * 20.0,
        volume_24h=28000000000.0,
        volume_spike_ratio=1.0,
        market_cap=900000000000.0,
        price_change_24h=2.5,
        price_change_7d=-1.2,
        funding_rate=0.0001,
        open_interest=15000000000.0,
        long_short_ratio=1.25,
        fear_greed_value=25,
        fear_greed_classification="Extreme Fear",
        news_headlines=["Bitcoin on the rise"],
        candles_4h=candles,
        candles_1h=[],
        data_quality_score=1.0,
        timestamp=datetime.now(UTC),
    )


class TestTechnicalPipeline:
    def test_pipeline_normalized_to_technical(self):
        """NormalizedAsset (60 candles) → TechnicalAnalysis valid."""
        engine = TechnicalAnalysisEngine()
        asset = make_asset(60)
        result = engine.analyze(asset)

        assert isinstance(result, TechnicalAnalysis)
        assert result.ema20 is not None
        assert result.ema50 is not None
        assert result.rsi14 is not None
        assert result.atr14 is not None
        assert 0 <= result.rsi14 <= 100
        assert result.atr14 > 0

    def test_pipeline_insufficient_candles(self):
        """NormalizedAsset (30 candles) → semua field None."""
        engine = TechnicalAnalysisEngine()
        asset = make_asset(30)
        result = engine.analyze(asset)

        assert result.ema20 is None
        assert result.ema50 is None
        assert result.rsi14 is None
        assert result.atr14 is None