"""Confidence Engine — rule-based scoring dengan conflict detection."""

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
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import (
    ConfidenceLevel,
    MarketStructure,
    SentimentLevel,
    TrendDirection,
    VolumeSignal,
)


class ConfidenceEngine:
    """Rule-based confidence scoring dari semua Analysis Engines."""

    # Thresholds
    HIGH_THRESHOLD = 0.75
    MEDIUM_THRESHOLD = 0.60

    def calculate(
        self,
        technical: TechnicalAnalysis,
        trend: TrendDirection,
        structure: MarketStructureResult,
        volume: VolumeAnalysis,
        futures: FuturesAnalysis,
        volatility: VolatilityAnalysis,
        sr: SupportResistanceResult,
        sentiment: SentimentAnalysis,
        price: float,
    ) -> ConfidenceResult:
        """Hitung confidence score dari semua analysis results."""
        score = 0.5
        positive: list[str] = []
        negative: list[str] = []
        warnings: list[str] = []

        # ── POSITIVE RULES ──

        # Trend + Structure aligned (bullish)
        if trend == TrendDirection.BULLISH and structure.structure == MarketStructure.BOS_BULLISH:
            score += 0.15
            positive.append("Trend BULLISH aligned with BOS_BULLISH")

        # Trend + Structure aligned (bearish)
        if trend == TrendDirection.BEARISH and structure.structure == MarketStructure.BOS_BEARISH:
            score += 0.15
            positive.append("Trend BEARISH aligned with BOS_BEARISH")

        # Volume SPIKE
        if volume.state == VolumeSignal.SPIKE:
            score += 0.10
            positive.append("Volume SPIKE menunjukkan momentum kuat")

        # Funding NEUTRAL (tidak extreme)
        if futures.sentiment == SentimentLevel.NEUTRAL:
            score += 0.08
            positive.append("Funding rate NEUTRAL — tidak ada extreme positioning")

        # Sentiment aligned dengan trend
        if trend == TrendDirection.BULLISH and sentiment.overall == SentimentLevel.GREED:
            score += 0.08
            positive.append("Sentiment GREED aligned dengan BULLISH trend")
        elif trend == TrendDirection.BEARISH and sentiment.overall == SentimentLevel.FEAR:
            score += 0.08
            positive.append("Sentiment FEAR aligned dengan BEARISH trend")
        elif sentiment.overall == SentimentLevel.NEUTRAL:
            score += 0.08
            positive.append("Sentiment NEUTRAL — tidak ada extreme bias")

        # Price position favorable
        if sr.price_position is not None:
            if sr.price_position < 0.4:
                score += 0.07
                positive.append("Price di lower half — favorable untuk LONG")
            elif sr.price_position > 0.6:
                score += 0.07
                positive.append("Price di upper half — favorable untuk SHORT")

        # Volatility MEDIUM (ideal)
        if volatility.risk_level == "MEDIUM":
            score += 0.05
            positive.append("Volatility MEDIUM — ideal untuk trading")

        # ── NEGATIVE RULES ──

        # Trend + Structure CONFLICT
        trend_struct_conflict = (
            (trend == TrendDirection.BULLISH and structure.structure == MarketStructure.BOS_BEARISH)
            or (trend == TrendDirection.BEARISH and structure.structure == MarketStructure.BOS_BULLISH)
        )
        if trend_struct_conflict:
            score -= 0.20
            negative.append("⚠ Trend dan Market Structure CONFLICT")

        # Volume WEAK
        if volume.state == VolumeSignal.WEAK:
            score -= 0.15
            negative.append("Volume WEAK — kurang partisipasi pasar")

        # Sentiment conflict dengan trend
        sentiment_conflict = (
            (trend == TrendDirection.BULLISH and sentiment.overall == SentimentLevel.FEAR)
            or (trend == TrendDirection.BEARISH and sentiment.overall == SentimentLevel.GREED)
        )
        if sentiment_conflict:
            score -= 0.10
            negative.append("Sentiment CONFLICT dengan Trend")

        # Funding extreme
        if trend == TrendDirection.BULLISH and futures.sentiment == SentimentLevel.GREED and futures.funding_rate > 0.0005:
            score -= 0.08
            negative.append("Funding extreme GREED — risiko reversal")
        if trend == TrendDirection.BEARISH and futures.sentiment == SentimentLevel.FEAR and futures.funding_rate < -0.0005:
            score -= 0.08
            negative.append("Funding extreme FEAR — risiko squeeze")

        # Volatility HIGH
        if volatility.risk_level == "HIGH":
            score -= 0.05
            negative.append("Volatility HIGH — chaotic market")

        # ── WARNINGS ──

        if volatility.risk_level == "HIGH" and volatility.atr_normalized > 3.0:
            warnings.append("High volatility detected")

        if abs(futures.funding_rate) > 0.0005:
            warnings.append("Funding rate extreme")

        if sr.price_position is not None:
            if sr.price_position > 0.85:
                warnings.append("Price near resistance")
            elif sr.price_position < 0.15:
                warnings.append("Price near support")

        if volume.state == VolumeSignal.WEAK:
            warnings.append("Low volume")

        if sentiment_conflict:
            warnings.append("Sentiment conflict with trend")

        # ── Clamp & finalize ──
        score = max(0.0, min(1.0, score))

        if score >= self.HIGH_THRESHOLD:
            level = ConfidenceLevel.HIGH
        elif score >= self.MEDIUM_THRESHOLD:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        is_tradeable = (
            score >= self.MEDIUM_THRESHOLD
            and not trend_struct_conflict
            and volatility.risk_level != "HIGH"
        )

        return ConfidenceResult(
            score=round(score, 4),
            level=level,
            positive_factors=positive,
            negative_factors=negative,
            warnings=warnings,
            is_tradeable=is_tradeable,
            timestamp=datetime.now(UTC),
        )