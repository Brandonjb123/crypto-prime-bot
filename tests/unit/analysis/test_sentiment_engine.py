"""Unit tests untuk SentimentEngine."""

from datetime import UTC, datetime

from src.analysis.sentiment_engine import SentimentEngine
from src.core.models.market_intelligence import SentimentAnalysis
from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.enums import SentimentLevel


def make_asset(fear_greed_value: int, headlines: list[str]) -> NormalizedAsset:
    """Helper: buat NormalizedAsset dengan F&G dan headlines tertentu."""
    return NormalizedAsset(
        symbol="BTC",
        price=50000.0,
        volume_24h=28000000000.0,
        volume_spike_ratio=1.0,
        market_cap=900000000000.0,
        price_change_24h=2.5,
        price_change_7d=-1.2,
        funding_rate=0.0001,
        open_interest=15000000000.0,
        long_short_ratio=1.25,
        fear_greed_value=fear_greed_value,
        fear_greed_classification="Extreme Fear" if fear_greed_value < 40 else "Greed",
        news_headlines=headlines,
        candles_4h=[],
        candles_1h=[],
        data_quality_score=1.0,
        timestamp=datetime.now(UTC),
    )


class TestSentimentEngine:
    def test_bullish_fg_and_news(self):
        """F&G tinggi + bullish headlines → GREED overall."""
        engine = SentimentEngine()
        asset = make_asset(
            fear_greed_value=75,
            headlines=["Bitcoin surge continues", "Bullish rally gains momentum"],
        )
        result = engine.analyze(asset)

        assert isinstance(result, SentimentAnalysis)
        assert result.overall == SentimentLevel.GREED
        assert result.news_score > 0
        assert result.confidence_score > 0.5  # aligned

    def test_bearish_fg_and_news(self):
        """F&G rendah + bearish headlines → FEAR overall."""
        engine = SentimentEngine()
        asset = make_asset(
            fear_greed_value=20,
            headlines=["Bitcoin crash incoming", "Regulation fear drops market"],
        )
        result = engine.analyze(asset)

        assert result.overall == SentimentLevel.FEAR
        assert result.news_score < 0
        assert result.confidence_score > 0.5  # aligned

    def test_neutral_mixed(self):
        """F&G netral + mixed headlines → NEUTRAL overall."""
        engine = SentimentEngine()
        asset = make_asset(
            fear_greed_value=50,
            headlines=["Bitcoin rally continues", "Fear of regulation grows"],
        )
        result = engine.analyze(asset)

        assert result.overall == SentimentLevel.NEUTRAL
        assert -0.5 <= result.news_score <= 0.5

    def test_empty_headlines(self):
        """Empty headlines → news_score=0.0, overall dari F&G saja."""
        engine = SentimentEngine()
        asset = make_asset(fear_greed_value=75, headlines=[])
        result = engine.analyze(asset)

        assert result.news_score == 0.0
        assert result.news_headline_count == 0
        assert result.overall == SentimentLevel.GREED  # F&G dominates

    def test_confidence_aligned_high(self):
        """F&G dan News sama-sama bullish → confidence tinggi."""
        engine = SentimentEngine()
        asset = make_asset(
            fear_greed_value=80,
            headlines=["surge", "rally", "bullish breakout"],
        )
        result = engine.analyze(asset)

        assert result.confidence_score >= 0.8

    def test_confidence_misaligned_low(self):
        """F&G bullish + News bearish → confidence rendah."""
        engine = SentimentEngine()
        asset = make_asset(
            fear_greed_value=80,
            headlines=["crash", "dump", "regulation fear"],
        )
        result = engine.analyze(asset)

        assert result.confidence_score < 0.5

    def test_fg_value_zero_fallback(self):
        """F&G = 0 (unavailable) → fallback ke news saja."""
        engine = SentimentEngine()
        asset = make_asset(
            fear_greed_value=0,
            headlines=["Bitcoin surge bullish rally"],
        )
        result = engine.analyze(asset)

        # News bullish → overall GREED meskipun F&G unavailable
        assert result.overall == SentimentLevel.GREED
        assert result.fear_greed_value == 0
        assert result.news_score > 0
