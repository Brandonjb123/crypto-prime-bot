"""Unit tests untuk ConfidenceEngine."""

from datetime import UTC, datetime

from src.confidence.confidence_engine import ConfidenceEngine
from src.core.models.analysis import TechnicalAnalysis
from src.core.models.confidence import ConfidenceResult
from src.core.models.market_intelligence import (
    FuturesAnalysis,
    SentimentAnalysis,
    SupportResistanceResult,
    VolatilityAnalysis,
    VolumeAnalysis,
)
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import (
    ConfidenceLevel,
    MarketStructure,
    SentimentLevel,
    TrendDirection,
    VolumeSignal,
)

# ── Helpers ──

def _make_ta(ema20=50000.0, ema50=48000.0, rsi14=60.0, atr14=1000.0):
    return TechnicalAnalysis(ema20=ema20, ema50=ema50, rsi14=rsi14, atr14=atr14, timestamp=datetime.now(UTC))

def _make_volume(state=VolumeSignal.SPIKE, spike_ratio=2.5, confidence=0.8):
    return VolumeAnalysis(state=state, spike_ratio=spike_ratio, confidence_score=confidence, timestamp=datetime.now(UTC))

def _make_futures(sentiment=SentimentLevel.NEUTRAL, funding_rate=0.0001, oi=1e10, ls=1.2, confidence=0.7):
    return FuturesAnalysis(sentiment=sentiment, funding_rate=funding_rate, open_interest=oi, long_short_ratio=ls, confidence_score=confidence, timestamp=datetime.now(UTC))

def _make_volatility(risk="MEDIUM", atr=1000.0, atr_norm=2.0, confidence=1.0):
    return VolatilityAnalysis(atr=atr, atr_normalized=atr_norm, risk_level=risk, confidence_score=confidence, timestamp=datetime.now(UTC))

def _make_sr(support=45000.0, resistance=55000.0, price_position=0.5, confidence=0.8):
    return SupportResistanceResult(nearest_support=support, nearest_resistance=resistance, price_position=price_position, confidence_score=confidence, timestamp=datetime.now(UTC))

def _make_structure(structure=MarketStructure.BOS_BULLISH, direction=TrendDirection.BULLISH, sh=52000.0, sl=44000.0):
    return MarketStructureResult(structure=structure, direction=direction, swing_high=sh, swing_low=sl, timestamp=datetime.now(UTC))

def _make_sentiment(overall=SentimentLevel.GREED, fg_value=75, fg_label="Greed", news_score=0.5, headline_count=5, confidence=0.8):
    return SentimentAnalysis(overall=overall, fear_greed_value=fg_value, fear_greed_label=fg_label, news_score=news_score, news_headline_count=headline_count, confidence_score=confidence, timestamp=datetime.now(UTC))


class TestConfidenceEngine:
    def test_strong_bullish_aligned(self):
        """Fixture bullish aligned → score >= 0.75, HIGH, is_tradeable=True."""
        engine = ConfidenceEngine()
        result = engine.calculate(
            technical=_make_ta(),
            trend=TrendDirection.BULLISH,
            structure=_make_structure(),
            volume=_make_volume(),
            futures=_make_futures(),
            volatility=_make_volatility(),
            sr=_make_sr(price_position=0.3),
            sentiment=_make_sentiment(),
            price=50000.0,
        )

        assert isinstance(result, ConfidenceResult)
        assert result.score >= 0.75
        assert result.level == ConfidenceLevel.HIGH
        assert result.is_tradeable is True
        assert len(result.positive_factors) > 0

    def test_strong_bearish_aligned(self):
        """Fixture bearish aligned → score >= 0.75, HIGH."""
        engine = ConfidenceEngine()
        result = engine.calculate(
            technical=_make_ta(ema20=45000.0, ema50=47000.0, rsi14=40.0),
            trend=TrendDirection.BEARISH,
            structure=_make_structure(structure=MarketStructure.BOS_BEARISH, direction=TrendDirection.BEARISH),
            volume=_make_volume(),
            futures=_make_futures(),
            volatility=_make_volatility(),
            sr=_make_sr(price_position=0.7),
            sentiment=_make_sentiment(overall=SentimentLevel.FEAR, fg_value=20, fg_label="Fear", news_score=-0.5),
            price=50000.0,
        )

        assert result.score >= 0.75
        assert result.level == ConfidenceLevel.HIGH
        assert result.is_tradeable is True

    def test_conflict_bullish_trend_bearish_structure(self):
        """Trend BULLISH + BOS_BEARISH → conflict, score rendah, is_tradeable=False."""
        engine = ConfidenceEngine()
        result = engine.calculate(
            technical=_make_ta(),
            trend=TrendDirection.BULLISH,
            structure=_make_structure(structure=MarketStructure.BOS_BEARISH),
            volume=_make_volume(state=VolumeSignal.NORMAL, spike_ratio=1.2),
            futures=_make_futures(sentiment=SentimentLevel.GREED),
            volatility=_make_volatility(risk="HIGH", atr_norm=4.0, confidence=0.5),
            sr=_make_sr(),
            sentiment=_make_sentiment(overall=SentimentLevel.FEAR, fg_value=20, news_score=-0.5),
            price=50000.0,
        )

        assert result.score <= 0.50
        assert result.is_tradeable is False

    def test_weak_volume_warning(self):
        """Volume WEAK → negative_factors mengandung volume warning."""
        engine = ConfidenceEngine()
        result = engine.calculate(
            technical=_make_ta(),
            trend=TrendDirection.BULLISH,
            structure=_make_structure(),
            volume=_make_volume(state=VolumeSignal.WEAK, spike_ratio=0.5),
            futures=_make_futures(),
            volatility=_make_volatility(),
            sr=_make_sr(),
            sentiment=_make_sentiment(),
            price=50000.0,
        )

        assert any("WEAK" in f or "Volume" in f for f in result.negative_factors)
        assert any("Low volume" in w for w in result.warnings)

    def test_high_volatility_not_tradeable(self):
        """Volatility HIGH → is_tradeable=False, warnings tidak kosong."""
        engine = ConfidenceEngine()
        result = engine.calculate(
            technical=_make_ta(),
            trend=TrendDirection.BULLISH,
            structure=_make_structure(),
            volume=_make_volume(),
            futures=_make_futures(),
            volatility=_make_volatility(risk="HIGH", atr_norm=4.0, confidence=0.5),
            sr=_make_sr(),
            sentiment=_make_sentiment(),
            price=50000.0,
        )

        assert result.is_tradeable is False
        assert any("High volatility" in w for w in result.warnings)

    def test_score_range(self):
        """Score selalu 0.0-1.0 untuk berbagai input."""
        engine = ConfidenceEngine()
        for trend, struct in [
            (TrendDirection.BULLISH, MarketStructure.BOS_BULLISH),
            (TrendDirection.BEARISH, MarketStructure.BOS_BEARISH),
            (TrendDirection.BULLISH, MarketStructure.BOS_BEARISH),
            (TrendDirection.SIDEWAYS, MarketStructure.NONE),
        ]:
            result = engine.calculate(
                technical=_make_ta(),
                trend=trend,
                structure=_make_structure(structure=struct, direction=trend),
                volume=_make_volume(),
                futures=_make_futures(),
                volatility=_make_volatility(),
                sr=_make_sr(),
                sentiment=_make_sentiment(),
                price=50000.0,
            )
            assert 0.0 <= result.score <= 1.0

    def test_deterministic(self):
        """Input sama → output sama persis."""
        engine = ConfidenceEngine()
        result1 = engine.calculate(
            technical=_make_ta(), trend=TrendDirection.BULLISH,
            structure=_make_structure(), volume=_make_volume(),
            futures=_make_futures(), volatility=_make_volatility(),
            sr=_make_sr(), sentiment=_make_sentiment(), price=50000.0,
        )
        result2 = engine.calculate(
            technical=_make_ta(), trend=TrendDirection.BULLISH,
            structure=_make_structure(), volume=_make_volume(),
            futures=_make_futures(), volatility=_make_volatility(),
            sr=_make_sr(), sentiment=_make_sentiment(), price=50000.0,
        )
        assert result1.score == result2.score
        assert result1.is_tradeable == result2.is_tradeable
        assert result1.positive_factors == result2.positive_factors