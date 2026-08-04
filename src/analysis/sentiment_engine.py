"""Sentiment Engine — Fear & Greed + News headline sentiment."""

from datetime import UTC, datetime

from src.core.models.market_intelligence import SentimentAnalysis
from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.enums import SentimentLevel


class SentimentEngine:
    """Analisis sentimen gabungan Fear & Greed + News."""

    # Keyword lists
    BULLISH_KEYWORDS = [
        "bullish", "surge", "rally", "breakout", "gain", "pump",
        "up", "high", "buy", "adoption", "partnership", "launch",
    ]
    BEARISH_KEYWORDS = [
        "bearish", "crash", "dump", "drop", "fall", "down",
        "sell", "hack", "ban", "lawsuit", "regulation", "fear",
    ]

    def analyze(self, asset: NormalizedAsset) -> SentimentAnalysis:
        """Analisis sentimen dari Fear & Greed Index dan News headlines."""
        fg_value = asset.fear_greed_value
        fg_label = asset.fear_greed_classification
        headlines = asset.news_headlines

        # ── Fear & Greed → score ──
        if fg_value == 0:
            fg_score = 0.0
            fg_used = False
        else:
            fg_used = True
            if fg_value >= 60:
                fg_score = 1.0  # GREED
            elif fg_value >= 40:
                fg_score = 0.0  # NEUTRAL
            else:
                fg_score = -1.0  # FEAR

        # ── News sentiment scoring ──
        news_score = self._score_headlines(headlines)

        # ── Combined ──
        if fg_used:
            combined = fg_score * 0.6 + news_score * 0.4
        else:
            combined = news_score  # fallback ke news saja

        if combined >= 0.2:
            overall = SentimentLevel.GREED
        elif combined <= -0.2:
            overall = SentimentLevel.FEAR
        else:
            overall = SentimentLevel.NEUTRAL

        # Confidence: alignment antara F&G dan News
        confidence = 1.0 - abs(fg_score - news_score) / 2.0

        return SentimentAnalysis(
            overall=overall,
            fear_greed_value=fg_value,
            fear_greed_label=fg_label,
            news_score=news_score,
            news_headline_count=len(headlines),
            confidence_score=round(confidence, 4),
            timestamp=datetime.now(UTC),
        )

    def _score_headlines(self, headlines: list[str]) -> float:
        """Rule-based keyword scoring per headline."""
        if not headlines:
            return 0.0

        total_score = 0.0
        for headline in headlines:
            lower = headline.lower()
            bull_hits = sum(1 for kw in self.BULLISH_KEYWORDS if kw in lower)
            bear_hits = sum(1 for kw in self.BEARISH_KEYWORDS if kw in lower)

            if bull_hits > bear_hits:
                total_score += 1.0
            elif bear_hits > bull_hits:
                total_score -= 1.0
            # else: neutral, no change

        # Normalize ke -1.0 .. 1.0
        return max(-1.0, min(1.0, total_score / max(len(headlines), 1)))