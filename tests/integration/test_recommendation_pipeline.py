"""Integration test: Validator → Risk → Recommendation."""

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
from src.core.models.recommendation import RecommendationResult
from src.core.models.risk import RiskResult
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.structure import MarketStructureResult
from src.core.models.validation import ValidationResult
from src.core.types.enums import (
    ConfidenceLevel,
    MarketStructure,
    RecommendationAction,
    SetupType,
    Side,
    TrendDirection,
    ValidationCheck,
    VolumeSignal,
)
from src.recommendation.recommendation_engine import RecommendationEngine


class TestRecommendationPipeline:
    def test_full_recommendation_flow(self):
        snapshot = AnalysisSnapshot(
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
                sentiment="NEUTRAL",
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
                overall="GREED",
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
        setup = SetupResult(
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
        validation = ValidationResult(
            approved=True,
            rejection_reasons=[],
            checks_passed={vc: True for vc in ValidationCheck},
            timestamp=datetime.now(UTC),
        )
        risk = RiskResult(
            entry_price=50000.0,
            stop_loss=48000.0,
            stop_distance=2000.0,
            take_profit=55000.0,
            take_profit_distance=5000.0,
            position_size=0.1,
            risk_amount=200.0,
            expected_profit=500.0,
            expected_loss=200.0,
            risk_reward_ratio=2.5,
            max_loss_pct=2.0,
            direction=Side.LONG,
            risk_model="trend",
            timestamp=datetime.now(UTC),
        )

        engine = RecommendationEngine()
        result = engine.recommend(snapshot, setup, validation, risk)

        assert isinstance(result, RecommendationResult)
        assert result.action == RecommendationAction.BUY
        assert result.ready_for_execution is True
        assert len(result.summary) > 0
