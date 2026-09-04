"""Unit tests untuk RiskEngine — kontrak baru."""

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
    SetupType,
    Side,
    TrendDirection,
    ValidationCheck,
    VolumeSignal,
)
from src.risk.risk_engine import RiskEngine


def _make_snapshot(price=50000.0, atr=1000.0) -> AnalysisSnapshot:
    return AnalysisSnapshot(
        symbol="BTC",
        price=price,
        technical=TechnicalAnalysis(
            ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=atr, timestamp=datetime.now(UTC)
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
            atr=atr,
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


def _make_setup(setup_type=SetupType.TREND_FOLLOWING, direction=Side.LONG) -> SetupResult:
    return SetupResult(
        direction=direction,
        setup_type=setup_type,
        triggered_rules=[],
        failed_rules=[],
        confidence_score=0.85,
        confidence_level=ConfidenceLevel.HIGH,
        blocked_reasons=[],
        is_valid_setup=True,
        reasoning=["Test"],
        timestamp=datetime.now(UTC),
    )


def _make_validation(approved=True) -> ValidationResult:
    return ValidationResult(
        approved=approved,
        rejection_reasons=[],
        checks_passed={vc: True for vc in ValidationCheck},
        timestamp=datetime.now(UTC),
    )


class TestRiskEngine:
    def test_trend_risk_long(self):
        engine = RiskEngine()
        snapshot = _make_snapshot(price=50000.0, atr=1000.0)
        setup = _make_setup(SetupType.TREND_FOLLOWING, Side.LONG)
        validation = _make_validation()
        result = engine.calculate(snapshot, setup, validation)

        assert isinstance(result, RiskResult)
        assert result.entry_price == 50000.0
        assert result.direction == Side.LONG
        assert result.risk_model == "trend"
        assert result.stop_loss < 50000.0
        assert result.take_profit > 50000.0
        assert result.stop_distance > 0
        assert result.take_profit_distance > 0
        assert result.risk_reward_ratio >= 2.0
        assert result.position_size > 0
        assert result.expected_profit > 0
        assert result.expected_loss > 0

    def test_breakout_risk_short(self):
        engine = RiskEngine()
        snapshot = _make_snapshot(price=50000.0, atr=800.0)
        setup = _make_setup(SetupType.BREAKOUT, Side.SHORT)
        validation = _make_validation()
        result = engine.calculate(snapshot, setup, validation)

        assert result.direction == Side.SHORT
        assert result.risk_model == "breakout"
        assert result.stop_loss > 50000.0
        assert result.take_profit < 50000.0
        assert result.risk_reward_ratio >= 2.0

    def test_reversal_risk_long(self):
        engine = RiskEngine()
        snapshot = _make_snapshot(price=50000.0, atr=1200.0)
        setup = _make_setup(SetupType.REVERSAL, Side.LONG)
        validation = _make_validation()
        result = engine.calculate(snapshot, setup, validation)

        assert result.risk_model == "reversal"
        assert result.stop_loss < 50000.0
        assert result.take_profit > 50000.0
        assert result.position_size <= 70.0

    def test_position_size_positive(self):
        engine = RiskEngine()
        snapshot = _make_snapshot(price=50000.0, atr=500.0)
        setup = _make_setup()
        validation = _make_validation()
        result = engine.calculate(snapshot, setup, validation)
        assert result.position_size > 0
        assert result.expected_profit > 0
        assert result.expected_loss > 0

    def test_deterministic(self):
        engine = RiskEngine()
        snapshot = _make_snapshot()
        setup = _make_setup()
        validation = _make_validation()
        r1 = engine.calculate(snapshot, setup, validation)
        r2 = engine.calculate(snapshot, setup, validation)
        assert r1.position_size == r2.position_size
        assert r1.stop_loss == r2.stop_loss
        assert r1.take_profit == r2.take_profit
        assert r1.risk_reward_ratio == r2.risk_reward_ratio
        assert r1.entry_price == r2.entry_price
