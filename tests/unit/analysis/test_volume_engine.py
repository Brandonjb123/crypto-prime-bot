"""Unit tests untuk VolumeEngine."""

from datetime import UTC, datetime

from src.analysis.volume_engine import VolumeEngine
from src.core.models.market_intelligence import VolumeAnalysis
from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.enums import VolumeSignal


def make_asset(volume_spike_ratio: float) -> NormalizedAsset:
    """Helper: buat NormalizedAsset dengan volume_spike_ratio tertentu."""
    return NormalizedAsset(
        symbol="BTC",
        price=50000.0,
        volume_24h=28000000000.0,
        volume_spike_ratio=volume_spike_ratio,
        market_cap=900000000000.0,
        price_change_24h=2.5,
        price_change_7d=-1.2,
        funding_rate=0.0001,
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


class TestVolumeEngine:
    def test_spike(self):
        """spike_ratio >= 2.0 → SPIKE."""
        engine = VolumeEngine()
        asset = make_asset(2.5)
        result = engine.analyze(asset)

        assert isinstance(result, VolumeAnalysis)
        assert result.state == VolumeSignal.SPIKE
        assert result.spike_ratio == 2.5
        assert result.confidence_score == 1.0  # min(2.5/2.0, 1.0) = 1.0

    def test_normal(self):
        """spike_ratio antara 1.0-2.0 → NORMAL."""
        engine = VolumeEngine()
        asset = make_asset(1.5)
        result = engine.analyze(asset)

        assert result.state == VolumeSignal.NORMAL
        assert result.confidence_score == 0.75  # 1.5/2.0

    def test_weak(self):
        """spike_ratio < 1.0 → WEAK."""
        engine = VolumeEngine()
        asset = make_asset(0.5)
        result = engine.analyze(asset)

        assert result.state == VolumeSignal.WEAK
        assert result.confidence_score == 0.25  # 0.5/2.0

    def test_confidence_range(self):
        """Confidence score harus antara 0.0-1.0."""
        engine = VolumeEngine()
        for ratio in [0.1, 0.5, 1.0, 1.5, 2.0, 3.0]:
            asset = make_asset(ratio)
            result = engine.analyze(asset)
            assert 0.0 <= result.confidence_score <= 1.0