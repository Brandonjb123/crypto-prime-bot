"""Confidence Engine — rule-based scoring dengan conflict detection."""

from datetime import UTC, datetime

from config.constants import CONFIDENCE_WEIGHTS
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
    ConfidenceWarning,
    MarketStructure,
    SentimentLevel,
    TrendDirection,
    VolumeSignal,
)


class ConfidenceEngine:
    """Rule-based confidence scoring dari semua Analysis Engines."""

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
        w = CONFIDENCE_WEIGHTS
        score = w["base_score"]
        positive: list[str] = []
        negative: list[str] = []
        warnings: list[ConfidenceWarning] = []
        blocked_reasons: list[ConfidenceWarning] = []

        # ── POSITIVE RULES ──

        if trend == TrendDirection.BULLISH and structure.structure == MarketStructure.BOS_BULLISH:
            score += w["trend_structure_aligned"]
            positive.append("Trend BULLISH aligned with BOS_BULLISH")

        if trend == TrendDirection.BEARISH and structure.structure == MarketStructure.BOS_BEARISH:
            score += w["trend_structure_aligned"]
            positive.append("Trend BEARISH aligned with BOS_BEARISH")

        if volume.state == VolumeSignal.SPIKE:
            score += w["volume_spike"]
            positive.append("Volume SPIKE menunjukkan momentum kuat")

        if futures.sentiment == SentimentLevel.NEUTRAL:
            score += w["funding_neutral"]
            positive.append("Funding rate NEUTRAL — tidak ada extreme positioning")

        if trend == TrendDirection.BULLISH and sentiment.overall == SentimentLevel.GREED:
            score += w["sentiment_aligned"]
            positive.append("Sentiment GREED aligned dengan trend")
        elif trend == TrendDirection.BEARISH and sentiment.overall == SentimentLevel.FEAR:
            score += w["sentiment_aligned"]
            positive.append("Sentiment FEAR aligned dengan trend")
        elif sentiment.overall == SentimentLevel.NEUTRAL:
            score += w["sentiment_aligned"]
            positive.append("Sentiment NEUTRAL — tidak ada extreme bias")

        # Price position favorable (tanpa asumsi LONG/SHORT)
        if sr.price_position is not None and sr.price_position < 0.4:
            score += w["price_position_favorable"]
            positive.append("Price di lower half — ada ruang naik")
        elif sr.price_position is not None and sr.price_position > 0.6:
            score += w["price_position_favorable"]
            positive.append("Price di upper half — ada ruang turun")

        if volatility.risk_level == "MEDIUM":
            score += w["volatility_medium"]
            positive.append("Volatility MEDIUM — ideal untuk trading")

        # ── NEGATIVE RULES ──

        trend_struct_conflict = (
            trend == TrendDirection.BULLISH and structure.structure == MarketStructure.BOS_BEARISH
        ) or (
            trend == TrendDirection.BEARISH and structure.structure == MarketStructure.BOS_BULLISH
        )
        if trend_struct_conflict:
            score += w["trend_structure_conflict"]
            negative.append("⚠ Trend dan Market Structure CONFLICT")
            warnings.append(ConfidenceWarning.STRUCTURE_CONFLICT)

        if volume.state == VolumeSignal.WEAK:
            score += w["volume_weak"]
            negative.append("Volume WEAK — kurang partisipasi pasar")
            warnings.append(ConfidenceWarning.LOW_VOLUME)

        sentiment_conflict = (
            trend == TrendDirection.BULLISH and sentiment.overall == SentimentLevel.FEAR
        ) or (trend == TrendDirection.BEARISH and sentiment.overall == SentimentLevel.GREED)
        if sentiment_conflict:
            score += w["sentiment_conflict"]
            negative.append("Sentiment CONFLICT dengan Trend")
            warnings.append(ConfidenceWarning.SENTIMENT_CONFLICT)

        if futures.funding_rate > 0.0005 or futures.funding_rate < -0.0005:
            score += w["funding_extreme"]
            negative.append("Funding rate extreme")
            warnings.append(ConfidenceWarning.FUNDING_EXTREME)

        if volatility.risk_level == "HIGH":
            score += w["volatility_high"]
            negative.append("Volatility HIGH — chaotic market")
            warnings.append(ConfidenceWarning.HIGH_VOLATILITY)

        # ── ADDITIONAL WARNINGS ──

        if sr.price_position is not None:
            if sr.price_position > 0.85:
                warnings.append(ConfidenceWarning.PRICE_NEAR_RESISTANCE)
            elif sr.price_position < 0.15:
                warnings.append(ConfidenceWarning.PRICE_NEAR_SUPPORT)

        # ── BLOCKED REASONS ──

        if score < self.MEDIUM_THRESHOLD:
            blocked_reasons.append(ConfidenceWarning.INSUFFICIENT_DATA)
        if ConfidenceWarning.STRUCTURE_CONFLICT in warnings:
            blocked_reasons.append(ConfidenceWarning.STRUCTURE_CONFLICT)
        if ConfidenceWarning.HIGH_VOLATILITY in warnings:
            blocked_reasons.append(ConfidenceWarning.HIGH_VOLATILITY)

        # ── Clamp & finalize ──
        score = max(0.0, min(1.0, score))

        if score >= self.HIGH_THRESHOLD:
            level = ConfidenceLevel.HIGH
        elif score >= self.MEDIUM_THRESHOLD:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return ConfidenceResult(
            score=round(score, 4),
            level=level,
            positive_factors=positive,
            negative_factors=negative,
            warnings=list(set(warnings)),  # deduplicate
            blocked_reasons=list(set(blocked_reasons)),
            timestamp=datetime.now(UTC),
        )
