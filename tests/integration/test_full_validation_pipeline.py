"""Integration test penuh: AnalysisSnapshot → ValidationResult."""

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
from src.core.models.normalized_asset import NormalizedAsset
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.validation import ValidationResult
from src.detection.setup_detector import SetupDetector
from src.validator.validator_engine import ValidatorEngine


def make_asset() -> NormalizedAsset:
    """
    Buat fixture agresif: uptrend kuat + spike resistance + pullback + recovery.
    Pasti menghasilkan BOS_BULLISH + BULLISH trend.
    """
    candles = []
    base_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    base_price = 45000.0

    # 60 candle dengan struktur jelas
    for i in range(60):
        ts = base_time + timedelta(hours=4 * i)
        if i < 20:
            # Uptrend awal
            price = base_price + i * 40
        elif i < 25:
            # Spike ke resistance
            price = base_price + 20 * 40 + (i - 20) * 60
        elif i < 30:
            # Pullback
            price = base_price + 20 * 40 + 5 * 60 - (i - 25) * 30
        elif i < 40:
            # Recovery + break swing high
            price = base_price + 20 * 40 + 5 * 60 - 5 * 30 + (i - 30) * 35
        else:
            # Lanjut naik stabil
            price = base_price + 20 * 40 + 5 * 60 - 5 * 30 + 10 * 35 + (i - 40) * 25

        candles.append(Candle(
            timestamp=ts, open=price, high=price + 50,
            low=price - 30, close=price + 30, volume=1000.0
        ))

    return NormalizedAsset(
        symbol="BTC", price=candles[-1].close,
        volume_24h=28000000000.0, volume_spike_ratio=3.0,  # SPIKE
        market_cap=900000000000.0, price_change_24h=5.5,
        price_change_7d=8.2, funding_rate=0.0002,
        open_interest=15000000000.0, long_short_ratio=1.5,
        fear_greed_value=80, fear_greed_classification="Extreme Greed",
        news_headlines=["Bitcoin breakout imminent", "Bullish momentum builds", "New highs expected"],
        candles_4h=candles, candles_1h=[],
        data_quality_score=1.0, timestamp=datetime.now(UTC),
    )


class TestFullValidationPipeline:
    def test_full_flow_to_validator(self):
        asset = make_asset()
        ta = TechnicalAnalysisEngine().analyze(asset)
        trend = TrendEngine().analyze(ta, asset.price)
        structure = MarketStructureEngine().analyze(asset.candles_4h, trend)
        volume = VolumeEngine().analyze(asset)
        futures = FuturesEngine().analyze(asset)
        volatility = VolatilityEngine().analyze(ta, asset.price)
        sr = SupportResistanceEngine().analyze(asset.candles_4h, asset.price)
        sentiment = SentimentEngine().analyze(asset)
        confidence = ConfidenceEngine().calculate(
            technical=ta, trend=trend, structure=structure,
            volume=volume, futures=futures, volatility=volatility,
            sr=sr, sentiment=sentiment, price=asset.price,
        )

        snapshot = AnalysisSnapshot(
            symbol=asset.symbol, price=asset.price,
            technical=ta, trend=trend, structure=structure,
            volume=volume, futures=futures, volatility=volatility,
            support_resistance=sr, sentiment=sentiment,
            confidence=confidence, timestamp=datetime.now(UTC),
        )

        setup = SetupDetector().detect(snapshot)
        result = ValidatorEngine().validate(setup, snapshot)

        assert isinstance(result, ValidationResult)
        assert result.approved is True
        assert len(result.rejection_reasons) == 0