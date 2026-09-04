"""Unit tests untuk SetupDetector orchestrator — kontrak enum."""

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
    ConfidenceWarning,
    MarketStructure,
    RuleType,
    SentimentLevel,
    SetupType,
    Side,
    TrendDirection,
    VolumeSignal,
)
from src.detection.setup_detector import SetupDetector


def _make_snapshot(**overrides) -> AnalysisSnapshot:
    defaults = dict(
        symbol="BTC",
        price=50000.0,
        technical=TechnicalAnalysis(
            ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=1000.0, timestamp=datetime.now(UTC)
        ),
        trend=TrendDirection.BULLISH,
        structure=MarketStructureResult(
            structure=MarketStructure.BOS_BULLISH,
            direction=TrendDirection.BULLISH,
            swing_high=52000.0,
            swing_low=44000.0,
            timestamp=datetime.now(UTC),
        ),
        volume=VolumeAnalysis(
            state=VolumeSignal.SPIKE,
            spike_ratio=2.5,
            confidence_score=0.8,
            timestamp=datetime.now(UTC),
        ),
        futures=FuturesAnalysis(
            sentiment=SentimentLevel.NEUTRAL,
            funding_rate=0.0001,
            open_interest=1e10,
            long_short_ratio=1.2,
            confidence_score=0.7,
            timestamp=datetime.now(UTC),
        ),
        volatility=VolatilityAnalysis(
            atr=1000.0,
            atr_normalized=2.0,
            risk_level="MEDIUM",
            confidence_score=1.0,
            timestamp=datetime.now(UTC),
        ),
        support_resistance=SupportResistanceResult(
            nearest_support=45000.0,
            nearest_resistance=55000.0,
            price_position=0.3,
            confidence_score=0.8,
            timestamp=datetime.now(UTC),
        ),
        sentiment=SentimentAnalysis(
            overall=SentimentLevel.GREED,
            fear_greed_value=75,
            fear_greed_label="Greed",
            news_score=0.5,
            news_headline_count=5,
            confidence_score=0.8,
            timestamp=datetime.now(UTC),
        ),
        confidence=ConfidenceResult(
            score=0.85,
            level=ConfidenceLevel.HIGH,
            positive_factors=["Test"],
            negative_factors=[],
            warnings=[],
            blocked_reasons=[],
            timestamp=datetime.now(UTC),
        ),
        timestamp=datetime.now(UTC),
    )
    defaults.update(overrides)
    return AnalysisSnapshot(**defaults)


class TestSetupDetector:
    def test_detect_long_setup(self):
        detector = SetupDetector()
        snapshot = _make_snapshot(
            volume=VolumeAnalysis(
                state=VolumeSignal.NORMAL,
                spike_ratio=1.2,
                confidence_score=0.5,
                timestamp=datetime.now(UTC),
            ),
        )
        result = detector.detect(snapshot)

        assert isinstance(result, SetupResult)
        assert result.direction == Side.LONG
        assert result.setup_type == SetupType.TREND_FOLLOWING
        assert result.is_valid_setup is True
        assert len(result.triggered_rules) > 0
        assert all(isinstance(r, RuleType) for r in result.triggered_rules)
        assert all(isinstance(r, RuleType) for r in result.failed_rules)

    def test_detect_short_setup(self):
        detector = SetupDetector()
        snapshot = _make_snapshot(
            trend=TrendDirection.BEARISH,
            structure=MarketStructureResult(
                structure=MarketStructure.BOS_BEARISH,
                direction=TrendDirection.BEARISH,
                swing_high=52000.0,
                swing_low=44000.0,
                timestamp=datetime.now(UTC),
            ),
            sentiment=SentimentAnalysis(
                overall=SentimentLevel.FEAR,
                fear_greed_value=20,
                fear_greed_label="Fear",
                news_score=-0.5,
                news_headline_count=5,
                confidence_score=0.8,
                timestamp=datetime.now(UTC),
            ),
            price_position=0.7,
        )
        result = detector.detect(snapshot)
        assert result.direction == Side.SHORT
        assert result.is_valid_setup is True

    def test_no_setup_when_none_triggered(self):
        detector = SetupDetector()
        snapshot = _make_snapshot(
            trend=TrendDirection.SIDEWAYS,
            structure=MarketStructureResult(
                structure=MarketStructure.NONE,
                direction=TrendDirection.SIDEWAYS,
                swing_high=None,
                swing_low=None,
                timestamp=datetime.now(UTC),
            ),
            volume=VolumeAnalysis(
                state=VolumeSignal.WEAK,
                spike_ratio=0.5,
                confidence_score=0.3,
                timestamp=datetime.now(UTC),
            ),
            confidence=ConfidenceResult(
                score=0.40,
                level=ConfidenceLevel.LOW,
                positive_factors=[],
                negative_factors=["Test"],
                warnings=[ConfidenceWarning.LOW_VOLUME],
                blocked_reasons=[
                    ConfidenceWarning.STRUCTURE_CONFLICT,
                    ConfidenceWarning.LOW_VOLUME,
                ],
                timestamp=datetime.now(UTC),
            ),
        )
        result = detector.detect(snapshot)
        assert result.direction is None
        assert result.is_valid_setup is False
        assert len(result.triggered_rules) == 0

    def test_blocked_confidence_does_not_affect_is_valid_setup(self):
        """is_valid_setup hanya dari detection, bukan execution permission."""
        detector = SetupDetector()
        snapshot = _make_snapshot(
            confidence=ConfidenceResult(
                score=0.75,
                level=ConfidenceLevel.HIGH,
                positive_factors=["Test"],
                negative_factors=[],
                warnings=[],
                blocked_reasons=[ConfidenceWarning.STRUCTURE_CONFLICT],
                timestamp=datetime.now(UTC),
            ),
        )
        result = detector.detect(snapshot)
        # Setup tetap valid meskipun ada blocked_reasons (itu urusan Validator)
        assert result.is_valid_setup is True
        assert len(result.blocked_reasons) > 0

    def test_deterministic(self):
        detector = SetupDetector()
        snapshot = _make_snapshot()
        results = [detector.detect(snapshot) for _ in range(10)]
        for r in results[1:]:
            assert r.direction == results[0].direction
            assert r.setup_type == results[0].setup_type
            assert r.is_valid_setup == results[0].is_valid_setup
