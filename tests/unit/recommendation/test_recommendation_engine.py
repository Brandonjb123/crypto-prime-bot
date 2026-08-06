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
from src.core.models.risk import RiskResult
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.structure import MarketStructureResult
from src.core.models.validation import ValidationResult
from src.core.types.enums import (
    ConfidenceLevel,
    MarketStructure,
    RecommendationAction,
    RecommendationReason,
    SetupType,
    Side,
    TrendDirection,
    ValidationCheck,
    VolumeSignal,
)
from src.recommendation.recommendation_engine import RecommendationEngine


def _make_snapshot(trend=TrendDirection.BULLISH):
    return AnalysisSnapshot(
        symbol="BTC", price=50000.0,
        technical=TechnicalAnalysis(ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=1000.0, timestamp=datetime.now(UTC)),
        trend=trend,
        structure=MarketStructureResult(structure=MarketStructure.BOS_BULLISH, direction=TrendDirection.BULLISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
        volume=VolumeAnalysis(state=VolumeSignal.SPIKE, spike_ratio=2.5, confidence_score=0.8, timestamp=datetime.now(UTC)),
        futures=FuturesAnalysis(sentiment="NEUTRAL", funding_rate=0.0001, open_interest=1e10, long_short_ratio=1.2, confidence_score=0.7, timestamp=datetime.now(UTC)),
        volatility=VolatilityAnalysis(atr=1000.0, atr_normalized=2.0, risk_level="MEDIUM", confidence_score=1.0, timestamp=datetime.now(UTC)),
        support_resistance=SupportResistanceResult(nearest_support=45000.0, nearest_resistance=55000.0, price_position=0.3, confidence_score=0.8, timestamp=datetime.now(UTC)),
        sentiment=SentimentAnalysis(overall="GREED", fear_greed_value=75, fear_greed_label="Greed", news_score=0.5, news_headline_count=5, confidence_score=0.8, timestamp=datetime.now(UTC)),
        confidence=ConfidenceResult(score=0.85, level=ConfidenceLevel.HIGH, positive_factors=["Test"], negative_factors=[], warnings=[], blocked_reasons=[], timestamp=datetime.now(UTC)),
        timestamp=datetime.now(UTC),
    )


def _make_setup(direction=Side.LONG, is_valid=True, blocked=None, confidence=0.85):
    return SetupResult(
        direction=direction,
        setup_type=SetupType.TREND_FOLLOWING,
        triggered_rules=[],
        failed_rules=[],
        confidence_score=confidence,
        confidence_level=ConfidenceLevel.HIGH if confidence >= 0.60 else ConfidenceLevel.LOW,
        blocked_reasons=blocked or [],
        is_valid_setup=is_valid,
        reasoning=["Test"],
        timestamp=datetime.now(UTC),
    )


def _make_validation(approved=True):
    return ValidationResult(
        approved=approved,
        rejection_reasons=[],
        checks_passed={vc: True for vc in ValidationCheck},
        timestamp=datetime.now(UTC),
    )


def _make_risk(rr=2.5):
    return RiskResult(
        entry_price=50000.0,
        stop_loss=48000.0,
        stop_distance=2000.0,
        take_profit=55000.0,
        take_profit_distance=5000.0,
        position_size=0.1,
        risk_amount=200.0,
        expected_profit=500.0,
        expected_loss=200.0,
        risk_reward_ratio=rr,
        max_loss_pct=2.0,
        direction=Side.LONG,
        risk_model="trend",
        timestamp=datetime.now(UTC),
    )


class TestRecommendationEngine:
    def engine(self):
        return RecommendationEngine()

    def test_long_buy(self):
        result = self.engine().recommend(
            _make_snapshot(), _make_setup(Side.LONG), _make_validation(), _make_risk()
        )
        assert result.action == RecommendationAction.BUY
        assert result.ready_for_execution is True
        assert RecommendationReason.VALIDATED_SETUP in result.reasons

    def test_short_sell(self):
        result = self.engine().recommend(
            _make_snapshot(TrendDirection.BEARISH),
            _make_setup(Side.SHORT),
            _make_validation(),
            _make_risk(),
        )
        assert result.action == RecommendationAction.SELL

    def test_validation_fail_skip(self):
        result = self.engine().recommend(
            _make_snapshot(), _make_setup(Side.LONG), _make_validation(False), _make_risk()
        )
        assert result.action == RecommendationAction.SKIP
        assert RecommendationReason.VALIDATION_FAILED in result.reasons

    def test_no_setup_wait(self):
        result = self.engine().recommend(
            _make_snapshot(), _make_setup(None, False), _make_validation(), _make_risk()
        )
        assert result.action == RecommendationAction.WAIT
        assert RecommendationReason.NO_SETUP in result.reasons

    def test_sideways_wait(self):
        result = self.engine().recommend(
            _make_snapshot(TrendDirection.SIDEWAYS),
            _make_setup(None, False),
            _make_validation(),
            _make_risk(),
        )
        assert result.action == RecommendationAction.WAIT

    def test_low_rr_not_ready(self):
        result = self.engine().recommend(
            _make_snapshot(), _make_setup(), _make_validation(), _make_risk(rr=1.5)
        )
        assert result.ready_for_execution is False
        assert RecommendationReason.LOW_RISK_REWARD in result.reasons

    def test_low_confidence_skip(self):
        result = self.engine().recommend(
            _make_snapshot(),
            _make_setup(confidence=0.50),
            _make_validation(),
            _make_risk(),
        )
        assert result.action == RecommendationAction.BUY  # Direction LONG tetap BUY
        assert result.ready_for_execution is False
        assert RecommendationReason.LOW_CONFIDENCE in result.reasons

    def test_warnings_forwarded(self):
        from src.core.types.enums import RiskWarning
        risk = _make_risk()
        risk.warnings = [RiskWarning.RR_TOO_LOW]
        result = self.engine().recommend(_make_snapshot(), _make_setup(), _make_validation(), risk)
        assert RiskWarning.RR_TOO_LOW in result.warnings

    def test_summary_not_empty(self):
        result = self.engine().recommend(_make_snapshot(), _make_setup(), _make_validation(), _make_risk())
        assert len(result.summary) > 0

    def test_deterministic(self):
        engine = self.engine()
        args = (_make_snapshot(), _make_setup(), _make_validation(), _make_risk())
        r1 = engine.recommend(*args)
        r2 = engine.recommend(*args)
        assert r1.action == r2.action
        assert r1.ready_for_execution == r2.ready_for_execution
        assert r1.summary == r2.summary