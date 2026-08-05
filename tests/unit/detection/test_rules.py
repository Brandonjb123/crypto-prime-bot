"""Unit tests untuk semua detection rules."""

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
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import (
    ConfidenceLevel,
    ConfidenceWarning,
    MarketStructure,
    SentimentLevel,
    TrendDirection,
    VolumeSignal,
)
from src.detection.rules.breakout import BreakoutRule
from src.detection.rules.reversal import ReversalRule
from src.detection.rules.trend_following import TrendFollowingRule

# ── Helpers ──

def _make_snapshot(**overrides) -> AnalysisSnapshot:
    defaults = dict(
        symbol="BTC", price=50000.0,
        technical=TechnicalAnalysis(ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=1000.0, timestamp=datetime.now(UTC)),
        trend=TrendDirection.BULLISH,
        structure=MarketStructureResult(structure=MarketStructure.BOS_BULLISH, direction=TrendDirection.BULLISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
        volume=VolumeAnalysis(state=VolumeSignal.SPIKE, spike_ratio=2.5, confidence_score=0.8, timestamp=datetime.now(UTC)),
        futures=FuturesAnalysis(sentiment=SentimentLevel.NEUTRAL, funding_rate=0.0001, open_interest=1e10, long_short_ratio=1.2, confidence_score=0.7, timestamp=datetime.now(UTC)),
        volatility=VolatilityAnalysis(atr=1000.0, atr_normalized=2.0, risk_level="MEDIUM", confidence_score=1.0, timestamp=datetime.now(UTC)),
        support_resistance=SupportResistanceResult(nearest_support=45000.0, nearest_resistance=55000.0, price_position=0.5, confidence_score=0.8, timestamp=datetime.now(UTC)),
        sentiment=SentimentAnalysis(overall=SentimentLevel.GREED, fear_greed_value=75, fear_greed_label="Greed", news_score=0.5, news_headline_count=5, confidence_score=0.8, timestamp=datetime.now(UTC)),
        confidence=ConfidenceResult(score=0.85, level=ConfidenceLevel.HIGH, positive_factors=["Test"], negative_factors=[], warnings=[], blocked_reasons=[], timestamp=datetime.now(UTC)),
        timestamp=datetime.now(UTC),
    )
    defaults.update(overrides)
    return AnalysisSnapshot(**defaults)


class TestTrendFollowingRule:
    def test_bullish_aligned_pass(self):
        rule = TrendFollowingRule()
        snapshot = _make_snapshot()
        result = rule.evaluate(snapshot)
        assert result.passed is True
        assert result.direction == "LONG"

    def test_bearish_aligned_pass(self):
        rule = TrendFollowingRule()
        snapshot = _make_snapshot(
            trend=TrendDirection.BEARISH,
            structure=MarketStructureResult(structure=MarketStructure.BOS_BEARISH, direction=TrendDirection.BEARISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
            sentiment=SentimentAnalysis(overall=SentimentLevel.FEAR, fear_greed_value=20, fear_greed_label="Fear", news_score=-0.5, news_headline_count=5, confidence_score=0.8, timestamp=datetime.now(UTC)),
        )
        result = rule.evaluate(snapshot)
        assert result.passed is True
        assert result.direction == "SHORT"

    def test_sideways_fail(self):
        rule = TrendFollowingRule()
        snapshot = _make_snapshot(trend=TrendDirection.SIDEWAYS)
        result = rule.evaluate(snapshot)
        assert result.passed is False

    def test_weak_volume_fail(self):
        rule = TrendFollowingRule()
        snapshot = _make_snapshot(
            volume=VolumeAnalysis(state=VolumeSignal.WEAK, spike_ratio=0.5, confidence_score=0.3, timestamp=datetime.now(UTC)),
        )
        result = rule.evaluate(snapshot)
        assert result.passed is False

    def test_blocked_confidence_fail(self):
        rule = TrendFollowingRule()
        snapshot = _make_snapshot(
            confidence=ConfidenceResult(score=0.55, level=ConfidenceLevel.LOW, positive_factors=[], negative_factors=[], warnings=[], blocked_reasons=[ConfidenceWarning.STRUCTURE_CONFLICT], timestamp=datetime.now(UTC)),
        )
        result = rule.evaluate(snapshot)
        assert result.passed is False


class TestBreakoutRule:
    def test_bos_bullish_spike_pass(self):
        rule = BreakoutRule()
        snapshot = _make_snapshot(price_position=0.3)
        result = rule.evaluate(snapshot)
        assert result.passed is True
        assert result.direction == "LONG"

    def test_bos_bearish_spike_pass(self):
        rule = BreakoutRule()
        snapshot = _make_snapshot(
            trend=TrendDirection.BEARISH,
            structure=MarketStructureResult(structure=MarketStructure.BOS_BEARISH, direction=TrendDirection.BEARISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
            sentiment=SentimentAnalysis(overall=SentimentLevel.FEAR, fear_greed_value=20, fear_greed_label="Fear", news_score=-0.5, news_headline_count=5, confidence_score=0.8, timestamp=datetime.now(UTC)),
            price_position=0.7,
        )
        result = rule.evaluate(snapshot)
        assert result.passed is True
        assert result.direction == "SHORT"

    def test_no_volume_spike_fail(self):
        rule = BreakoutRule()
        snapshot = _make_snapshot(
            volume=VolumeAnalysis(state=VolumeSignal.NORMAL, spike_ratio=1.2, confidence_score=0.5, timestamp=datetime.now(UTC)),
        )
        result = rule.evaluate(snapshot)
        assert result.passed is False

    def test_unfavorable_price_position_fail(self):
        rule = BreakoutRule()
        snapshot = _make_snapshot()
        snapshot.support_resistance = SupportResistanceResult(
            nearest_support=45000.0, nearest_resistance=55000.0,
            price_position=0.8, confidence_score=0.8,
            timestamp=datetime.now(UTC),
        )
        result = rule.evaluate(snapshot)
        assert result.passed is False



class TestReversalRule:
    def test_choch_bullish_pass(self):
        rule = ReversalRule()
        snapshot = _make_snapshot(
            structure=MarketStructureResult(structure=MarketStructure.CHOCH, direction=TrendDirection.BULLISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
            confidence=ConfidenceResult(score=0.75, level=ConfidenceLevel.HIGH, positive_factors=["Test"], negative_factors=[], warnings=[], blocked_reasons=[], timestamp=datetime.now(UTC)),
        )
        result = rule.evaluate(snapshot)
        assert result.passed is True
        assert result.direction == "LONG"

    def test_choch_bearish_pass(self):
        rule = ReversalRule()
        snapshot = _make_snapshot(
            trend=TrendDirection.BEARISH,
            structure=MarketStructureResult(structure=MarketStructure.CHOCH, direction=TrendDirection.BEARISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
            sentiment=SentimentAnalysis(overall=SentimentLevel.FEAR, fear_greed_value=20, fear_greed_label="Fear", news_score=-0.5, news_headline_count=5, confidence_score=0.8, timestamp=datetime.now(UTC)),
            confidence=ConfidenceResult(score=0.75, level=ConfidenceLevel.HIGH, positive_factors=["Test"], negative_factors=[], warnings=[], blocked_reasons=[], timestamp=datetime.now(UTC)),
        )
        result = rule.evaluate(snapshot)
        assert result.passed is True
        assert result.direction == "SHORT"

    def test_not_choch_fail(self):
        rule = ReversalRule()
        snapshot = _make_snapshot()
        result = rule.evaluate(snapshot)
        assert result.passed is False

    def test_low_confidence_fail(self):
        rule = ReversalRule()
        snapshot = _make_snapshot(
            structure=MarketStructureResult(structure=MarketStructure.CHOCH, direction=TrendDirection.BULLISH, swing_high=52000.0, swing_low=44000.0, timestamp=datetime.now(UTC)),
            confidence=ConfidenceResult(score=0.65, level=ConfidenceLevel.MEDIUM, positive_factors=[], negative_factors=[], warnings=[], blocked_reasons=[], timestamp=datetime.now(UTC)),
        )
        result = rule.evaluate(snapshot)
        assert result.passed is False