"""Integration test: NormalizedAsset → SentimentAnalysis."""

from datetime import UTC, datetime

from src.analysis.sentiment_engine import SentimentEngine
from src.core.models.market_intelligence import SentimentAnalysis
from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.enums import SentimentLevel


class TestSentimentPipeline:
    def test_pipeline_sentiment_greed(self):
        """NormalizedAsset dengan data lengkap → SentimentAnalysis GREED."""
        engine = SentimentEngine()
        asset = NormalizedAsset(
            symbol="BTC",
            price=50000.0,
            volume_24h=28000000000.0,
            volume_spike_ratio=1.5,
            market_cap=900000000000.0,
            price_change_24h=2.5,
            price_change_7d=-1.2,
            funding_rate=0.0001,
            open_interest=15000000000.0,
            long_short_ratio=1.25,
            fear_greed_value=75,
            fear_greed_classification="Greed",
            news_headlines=[
                "Bitcoin surge continues as institutional adoption grows",
                "Bullish rally pushes BTC above resistance",
                "New partnership announced for crypto payment",
            ],
            candles_4h=[],
            candles_1h=[],
            data_quality_score=1.0,
            timestamp=datetime.now(UTC),
        )
        result = engine.analyze(asset)

        assert isinstance(result, SentimentAnalysis)
        assert result.overall == SentimentLevel.GREED
        assert result.fear_greed_value == 75
        assert result.news_score > 0
        assert result.news_headline_count == 3
        assert 0.0 <= result.confidence_score <= 1.0

    def test_pipeline_sentiment_fear(self):
        """NormalizedAsset dengan F&G rendah + bearish news → FEAR."""
        engine = SentimentEngine()
        asset = NormalizedAsset(
            symbol="BTC",
            price=50000.0,
            volume_24h=28000000000.0,
            volume_spike_ratio=1.5,
            market_cap=900000000000.0,
            price_change_24h=2.5,
            price_change_7d=-1.2,
            funding_rate=0.0001,
            open_interest=15000000000.0,
            long_short_ratio=1.25,
            fear_greed_value=20,
            fear_greed_classification="Extreme Fear",
            news_headlines=[
                "Bitcoin crash continues as regulation fear grows",
                "Crypto ban rumors drop market sentiment",
            ],
            candles_4h=[],
            candles_1h=[],
            data_quality_score=1.0,
            timestamp=datetime.now(UTC),
        )
        result = engine.analyze(asset)

        assert isinstance(result, SentimentAnalysis)
        assert result.overall == SentimentLevel.FEAR
        assert result.fear_greed_value == 20
        assert result.news_score < 0
        assert result.news_headline_count == 2
        assert 0.0 <= result.confidence_score <= 1.0
