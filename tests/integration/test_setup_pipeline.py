"""Integration test: AnalysisSnapshot → SetupResult — kontrak enum."""

from datetime import UTC, datetime

from src.core.models.analysis import TechnicalAnalysis
from src.core.models.confidence import ConfidenceResult
from src.core.models.market_intelligence import (
    FuturesAnalysis,
    SentimentAnalysis,
    SupportResistanceResult,
    VolatilityAnalysis,
    VolumeAnalysis,
)
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import (
    ConfidenceLevel,
    MarketStructure,
    RuleType,
    SentimentLevel,
    SetupType,
    Side,
    TrendDirection,
    VolumeSignal,
)
from src.detection.setup_detector import SetupDetector


class TestSetupPipeline:
    def test_full_snapshot_to_setup(self):
        snapshot = AnalysisSnapshot(
            symbol="BTC", price=50000.0,
            technical=TechnicalAnalysis(ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=1000.0, timestamp=datetime.now(UTC)),
            trend=TrendDirection.BULLISH,
            structure=MarketStructureResult(structure=MarketStructure.BOS_BULLISH, direction=TrendDirection.BULLISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
            volume=VolumeAnalysis(state=VolumeSignal.NORMAL, spike_ratio=1.2, confidence_score=0.5, timestamp=datetime.now(UTC)),
            futures=FuturesAnalysis(sentiment=SentimentLevel.NEUTRAL, funding_rate=0.0001, open_interest=1e10, long_short_ratio=1.2, confidence_score=0.7, timestamp=datetime.now(UTC)),
            volatility=VolatilityAnalysis(atr=1000.0, atr_normalized=2.0, risk_level="MEDIUM", confidence_score=1.0, timestamp=datetime.now(UTC)),
            support_resistance=SupportResistanceResult(nearest_support=45000.0, nearest_resistance=55000.0, price_position=0.3, confidence_score=0.8, timestamp=datetime.now(UTC)),
            sentiment=SentimentAnalysis(overall=SentimentLevel.GREED, fear_greed_value=75, fear_greed_label="Greed", news_score=0.5, news_headline_count=5, confidence_score=0.8, timestamp=datetime.now(UTC)),
            confidence=ConfidenceResult(score=0.85, level=ConfidenceLevel.HIGH, positive_factors=["Test"], negative_factors=[], warnings=[], blocked_reasons=[], timestamp=datetime.now(UTC)),
            timestamp=datetime.now(UTC),
        )

        detector = SetupDetector()
        result = detector.detect(snapshot)

        assert isinstance(result, SetupResult)
        assert result.direction == Side.LONG
        assert result.setup_type == SetupType.TREND_FOLLOWING
        assert result.is_valid_setup is True
        assert len(result.triggered_rules) > 0
        assert all(isinstance(r, RuleType) for r in result.triggered_rules)