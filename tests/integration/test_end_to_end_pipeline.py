"""Integration test end-to-end: NormalizedAsset → semua 8 engines → ConfidenceResult."""

from datetime import UTC, datetime, timedelta

from src.analysis.futures_engine import FuturesEngine
from src.analysis.market_structure_engine import MarketStructureEngine
from src.analysis.sentiment_engine import SentimentEngine
from src.analysis.support_resistance_engine import SupportResistanceEngine
from src.analysis.technical_engine import TechnicalAnalysisEngine
from src.analysis.trend_engine import TrendEngine
from src.analysis.volatility_engine import VolatilityEngine
from src.analysis.volume_engine import VolumeEngine
from src.confidence.confidence_engine import ConfidenceEngine
from src.core.models.candle import Candle
from src.core.models.confidence import ConfidenceResult
from src.core.models.normalized_asset import NormalizedAsset


def make_full_asset() -> NormalizedAsset:
    """Buat NormalizedAsset lengkap dengan 60 candle uptrend + pullback."""
    candles = []
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    base_price = 45000.0

    for i in range(60):
        ts = base_time + timedelta(hours=4 * i)
        if i < 30:
            price = base_price + i * 30
        elif i < 35:
            price = base_price + 30 * 30 + (i - 30) * 40
        elif i < 45:
            price = base_price + 30 * 30 + 200 - (i - 35) * 20
        elif i < 55:
            price = base_price + 30 * 30 + 200 - 200 + (i - 45) * 15
        else:
            price = base_price + 30 * 30 + 200 - 200 + 150 - (i - 55) * 10

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
        price=base_price + 30 * 30 + 150,
        volume_24h=28000000000.0,
        volume_spike_ratio=2.5,
        market_cap=900000000000.0,
        price_change_24h=2.5,
        price_change_7d=-1.2,
        funding_rate=0.0002,
        open_interest=15000000000.0,
        long_short_ratio=1.25,
        fear_greed_value=75,
        fear_greed_classification="Greed",
        news_headlines=["Bitcoin rally continues", "Bullish breakout expected"],
        candles_4h=candles,
        candles_1h=[],
        data_quality_score=1.0,
        timestamp=datetime.now(UTC),
    )


class TestEndToEndPipeline:
    def test_full_pipeline_to_confidence(self):
        """NormalizedAsset → 8 engines → ConfidenceResult valid."""
        asset = make_full_asset()

        # Layer 1: Technical
        ta_engine = TechnicalAnalysisEngine()
        technical = ta_engine.analyze(asset)

        # Layer 2: Trend & Market Structure
        trend_engine = TrendEngine()
        trend = trend_engine.analyze(technical, asset.price)

        structure_engine = MarketStructureEngine()
        structure = structure_engine.analyze(asset.candles_4h, trend)

        # Layer 3: Market Intelligence (4 engines)
        vol_engine = VolumeEngine()
        volume = vol_engine.analyze(asset)

        fut_engine = FuturesEngine()
        futures = fut_engine.analyze(asset)

        vola_engine = VolatilityEngine()
        volatility = vola_engine.analyze(technical, asset.price)

        sr_engine = SupportResistanceEngine()
        sr = sr_engine.analyze(asset.candles_4h, asset.price)

        # Layer 4: Sentiment
        sent_engine = SentimentEngine()
        sentiment = sent_engine.analyze(asset)

        # Layer 5: Confidence
        conf_engine = ConfidenceEngine()
        result = conf_engine.calculate(
            technical=technical,
            trend=trend,
            structure=structure,
            volume=volume,
            futures=futures,
            volatility=volatility,
            sr=sr,
            sentiment=sentiment,
            price=asset.price,
        )

        assert isinstance(result, ConfidenceResult)
        assert 0.0 <= result.score <= 1.0
        assert result.level.value in ("HIGH", "MEDIUM", "LOW")
        assert len(result.positive_factors) > 0
        assert isinstance(result.warnings, list)
        assert isinstance(result.blocked_reasons, list)
        assert result.timestamp is not None
