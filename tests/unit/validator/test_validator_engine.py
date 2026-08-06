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
    SetupType,
    Side,
    TrendDirection,
    ValidationReason,
)
from src.validator.validator_engine import ValidatorEngine


def _make_setup(overrides=None) -> SetupResult:
    defaults = dict(
        direction=Side.LONG,
        setup_type=SetupType.TREND_FOLLOWING,
        triggered_rules=[],
        failed_rules=[],
        confidence_score=0.85,
        confidence_level=ConfidenceLevel.HIGH,
        blocked_reasons=[],
        is_valid_setup=True,
        reasoning=["Test"],
        timestamp=datetime.now(UTC),
    )
    if overrides:
        defaults.update(overrides)
    return SetupResult(**defaults)

def _make_snapshot(**overrides) -> AnalysisSnapshot:
    defaults = dict(
        symbol="BTC", price=50000.0,
        technical=TechnicalAnalysis(ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=1000.0, timestamp=datetime.now(UTC)),
        trend=TrendDirection.BULLISH,
        structure=MarketStructureResult(structure=MarketStructure.BOS_BULLISH, direction=TrendDirection.BULLISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
        volume=VolumeAnalysis(state="SPIKE", spike_ratio=2.5, confidence_score=0.8, timestamp=datetime.now(UTC)),
        futures=FuturesAnalysis(sentiment="NEUTRAL", funding_rate=0.0001, open_interest=1e10, long_short_ratio=1.2, confidence_score=0.7, timestamp=datetime.now(UTC)),
        volatility=VolatilityAnalysis(atr=1000.0, atr_normalized=2.0, risk_level="MEDIUM", confidence_score=1.0, timestamp=datetime.now(UTC)),
        support_resistance=SupportResistanceResult(nearest_support=45000.0, nearest_resistance=55000.0, price_position=0.3, confidence_score=0.8, timestamp=datetime.now(UTC)),
        sentiment=SentimentAnalysis(overall="GREED", fear_greed_value=75, fear_greed_label="Greed", news_score=0.5, news_headline_count=5, confidence_score=0.8, timestamp=datetime.now(UTC)),
        confidence=ConfidenceResult(score=0.85, level=ConfidenceLevel.HIGH, positive_factors=["Test"], negative_factors=[], warnings=[], blocked_reasons=[], timestamp=datetime.now(UTC)),
        timestamp=datetime.now(UTC),
    )
    defaults.update(overrides)
    return AnalysisSnapshot(**defaults)


class TestValidatorEngine:
    def test_valid_setup_approved(self):
        engine = ValidatorEngine()
        setup = _make_setup()
        snapshot = _make_snapshot()
        result = engine.validate(setup, snapshot)
        assert result.approved is True
        assert len(result.rejection_reasons) == 0
        assert len(result.checks_passed) == 5

    def test_blocked_reasons_rejected(self):
        engine = ValidatorEngine()
        setup = _make_setup({"blocked_reasons": [ConfidenceWarning.STRUCTURE_CONFLICT]})
        snapshot = _make_snapshot()
        result = engine.validate(setup, snapshot)
        assert result.approved is False
        assert ValidationReason.BLOCKED_REASONS in result.rejection_reasons

    def test_low_confidence_rejected(self):
        engine = ValidatorEngine()
        setup = _make_setup({"confidence_score": 0.55, "confidence_level": ConfidenceLevel.LOW})
        snapshot = _make_snapshot()
        result = engine.validate(setup, snapshot)
        assert result.approved is False
        assert ValidationReason.LOW_CONFIDENCE in result.rejection_reasons

    def test_sideways_market_rejected(self):
        engine = ValidatorEngine()
        setup = _make_setup()
        snapshot = _make_snapshot(trend=TrendDirection.SIDEWAYS)
        result = engine.validate(setup, snapshot)
        assert result.approved is False
        assert ValidationReason.SIDEWAYS_MARKET in result.rejection_reasons

    def test_no_setup_rejected(self):
        engine = ValidatorEngine()
        setup = _make_setup({"direction": None, "is_valid_setup": False})
        snapshot = _make_snapshot()
        result = engine.validate(setup, snapshot)
        assert result.approved is False
        assert ValidationReason.NO_SETUP_DETECTED in result.rejection_reasons

    def test_duplicate_signal_rejected(self):
        engine = ValidatorEngine()
        setup = _make_setup()
        snapshot = _make_snapshot()
        result = engine.validate(setup, snapshot, existing_signal_count=1)
        assert result.approved is False
        assert ValidationReason.DUPLICATE_SIGNAL in result.rejection_reasons

    def test_deterministic(self):
        engine = ValidatorEngine()
        setup = _make_setup()
        snapshot = _make_snapshot()
        r1 = engine.validate(setup, snapshot)
        r2 = engine.validate(setup, snapshot)
        assert r1.approved == r2.approved
        assert r1.rejection_reasons == r2.rejection_reasons