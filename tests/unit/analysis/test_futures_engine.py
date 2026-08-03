"""Unit tests untuk FuturesEngine."""

from datetime import UTC, datetime

from src.analysis.futures_engine import FuturesEngine
from src.core.models.market_intelligence import FuturesAnalysis
from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.enums import SentimentLevel


def make_asset(funding_rate: float) -> NormalizedAsset:
    """Helper: buat NormalizedAsset dengan funding_rate tertentu."""
    return NormalizedAsset(
        symbol="BTC",
        price=50000.0,
        volume_24h=28000000000.0,
        volume_spike_ratio=1.0,
        market_cap=900000000000.0,
        price_change_24h=2.5,
        price_change_7d=-1.2,
        funding_rate=funding_rate,
        open_interest=15000000000.0,
        long_short_ratio=1.25,
        fear_greed_value=25,
        fear_greed_classification="Extreme Fear",
        news_headlines=[],
        candles_4h=[],
        candles_1h=[],
        data_quality_score=1.0,
        timestamp=datetime.now(UTC),
    )


class TestFuturesEngine:
    def test_greed(self):
        """funding_rate > 0.01% → GREED."""
        engine = FuturesEngine()
        asset = make_asset(0.0005)  # 0.05%
        result = engine.analyze(asset)

        assert isinstance(result, FuturesAnalysis)
        assert result.sentiment == SentimentLevel.GREED
        assert result.funding_rate == 0.0005
        assert result.confidence_score == 0.5  # min(0.0005/0.001, 1.0)

    def test_fear(self):
        """funding_rate < -0.01% → FEAR."""
        engine = FuturesEngine()
        asset = make_asset(-0.0008)  # -0.08%
        result = engine.analyze(asset)

        assert result.sentiment == SentimentLevel.FEAR
        assert result.funding_rate == -0.0008
        assert result.confidence_score == 0.8  # min(0.0008/0.001, 1.0)

    def test_neutral(self):
        """funding_rate antara -0.01% dan 0.01% → NEUTRAL."""
        engine = FuturesEngine()
        asset = make_asset(0.00005)  # 0.005%
        result = engine.analyze(asset)

        assert result.sentiment == SentimentLevel.NEUTRAL
        assert result.confidence_score == 0.05  # 0.00005/0.001

    def test_confidence_range(self):
        """Confidence score harus antara 0.0-1.0."""
        engine = FuturesEngine()
        for rate in [-0.002, -0.0005, 0.0, 0.0005, 0.002]:
            asset = make_asset(rate)
            result = engine.analyze(asset)
            assert 0.0 <= result.confidence_score <= 1.0