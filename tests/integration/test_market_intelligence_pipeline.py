"""Integration test: NormalizedAsset → semua 4 engine Market Intelligence."""

from datetime import UTC, datetime, timedelta

from src.analysis.futures_engine import FuturesEngine
from src.analysis.support_resistance_engine import SupportResistanceEngine
from src.analysis.technical_engine import TechnicalAnalysisEngine
from src.analysis.volatility_engine import VolatilityEngine
from src.analysis.volume_engine import VolumeEngine
from src.core.models.candle import Candle
from src.core.models.market_intelligence import (
    FuturesAnalysis,
    SupportResistanceResult,
    VolatilityAnalysis,
    VolumeAnalysis,
)
from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.enums import SentimentLevel, VolumeSignal


def make_asset(candle_count: int = 60) -> NormalizedAsset:
    """Helper: buat NormalizedAsset dengan candle uptrend + resistance jelas."""
    candles = []
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    base_price = 45000.0

    for i in range(candle_count):
        ts = base_time + timedelta(hours=4 * i)
        if i < 30:
            price = base_price + i * 30  # uptrend kuat
        elif i < 35:
            price = base_price + 30 * 30 + (i - 30) * 40  # spike ke resistance ~47000
        elif i < 45:
            price = base_price + 30 * 30 + 200 - (i - 35) * 20  # pullback
        elif i < 55:
            price = (
                base_price + 30 * 30 + 200 - 200 + (i - 45) * 15
            )  # naik lagi, tapi tidak break resistance
        else:
            price = base_price + 30 * 30 + 200 - 200 + 150 - (i - 55) * 10  # sideways turun dikit

        candles.append(
            Candle(
                timestamp=ts,
                open=price,
                high=price + 40,
                low=price - 20,
                close=price + 20,
                volume=1000.0,
            )
        )

    return NormalizedAsset(
        symbol="BTC",
        price=base_price + 30 * 30 + 150,  # ~46150, di antara support dan resistance
        volume_24h=28000000000.0,
        volume_spike_ratio=1.5,
        market_cap=900000000000.0,
        price_change_24h=2.5,
        price_change_7d=-1.2,
        funding_rate=0.0002,
        open_interest=15000000000.0,
        long_short_ratio=1.25,
        fear_greed_value=25,
        fear_greed_classification="Extreme Fear",
        news_headlines=["Bitcoin rising"],
        candles_4h=candles,
        candles_1h=[],
        data_quality_score=1.0,
        timestamp=datetime.now(UTC),
    )


class TestMarketIntelligencePipeline:
    def test_all_four_engines(self):
        """Semua 4 engine berhasil analyze NormalizedAsset."""
        asset = make_asset(60)
        ta_engine = TechnicalAnalysisEngine()
        technical = ta_engine.analyze(asset)

        # Volume
        vol_engine = VolumeEngine()
        vol_result = vol_engine.analyze(asset)
        assert isinstance(vol_result, VolumeAnalysis)
        assert vol_result.state == VolumeSignal.NORMAL
        assert 0.0 <= vol_result.confidence_score <= 1.0

        # Futures
        fut_engine = FuturesEngine()
        fut_result = fut_engine.analyze(asset)
        assert isinstance(fut_result, FuturesAnalysis)
        assert fut_result.sentiment == SentimentLevel.GREED  # funding 0.02%
        assert 0.0 <= fut_result.confidence_score <= 1.0

        # Volatility
        vola_engine = VolatilityEngine()
        vola_result = vola_engine.analyze(technical, asset.price)
        assert isinstance(vola_result, VolatilityAnalysis)
        assert vola_result.atr > 0
        assert vola_result.risk_level in ("LOW", "MEDIUM", "HIGH")
        assert 0.0 <= vola_result.confidence_score <= 1.0

        # Support & Resistance
        sr_engine = SupportResistanceEngine()
        sr_result = sr_engine.analyze(asset.candles_4h, asset.price)
        assert isinstance(sr_result, SupportResistanceResult)
        assert sr_result.nearest_resistance is not None
        assert 0.0 <= sr_result.price_position <= 1.0
        assert 0.0 <= sr_result.confidence_score <= 1.0
