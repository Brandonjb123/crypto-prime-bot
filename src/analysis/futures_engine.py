"""Futures Engine — analisis sentimen dari data futures."""

from datetime import UTC, datetime

from src.core.models.market_intelligence import FuturesAnalysis
from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.enums import SentimentLevel


class FuturesEngine:
    """Analisis sentimen futures dari funding rate dan OI."""

    GREED_THRESHOLD = 0.0001   # > 0.01% → GREED
    FEAR_THRESHOLD = -0.0001   # < -0.01% → FEAR

    def analyze(self, asset: NormalizedAsset) -> FuturesAnalysis:
        """Tentukan sentimen berdasarkan funding rate."""
        funding = asset.funding_rate
        oi = asset.open_interest
        ls_ratio = asset.long_short_ratio

        if funding > self.GREED_THRESHOLD:
            sentiment = SentimentLevel.GREED
        elif funding < self.FEAR_THRESHOLD:
            sentiment = SentimentLevel.FEAR
        else:
            sentiment = SentimentLevel.NEUTRAL

        # Confidence: jarak funding_rate dari 0, dinormalisasi ke 0.0-1.0
        confidence = min(abs(funding) / 0.001, 1.0)  # 0.1% funding = full confidence

        return FuturesAnalysis(
            sentiment=sentiment,
            funding_rate=funding,
            open_interest=oi,
            long_short_ratio=ls_ratio,
            confidence_score=confidence,
            timestamp=datetime.now(UTC),
        )