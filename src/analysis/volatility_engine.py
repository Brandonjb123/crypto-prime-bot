"""Volatility Engine — analisis volatilitas dari ATR."""

from datetime import UTC, datetime

from src.core.models.analysis import TechnicalAnalysis
from src.core.models.market_intelligence import VolatilityAnalysis


class VolatilityEngine:
    """Analisis volatilitas dari ATR14."""

    LOW_THRESHOLD = 1.0    # < 1% → LOW
    HIGH_THRESHOLD = 3.0   # >= 3% → HIGH

    def analyze(self, technical: TechnicalAnalysis, price: float) -> VolatilityAnalysis:
        """Klasifikasi risiko berdasarkan ATR sebagai persentase harga."""
        atr = technical.atr14 or 0.0
        atr_pct = (atr / price * 100) if price > 0 else 0.0

        if atr_pct >= self.HIGH_THRESHOLD:
            risk = "HIGH"
            confidence = 0.5  # terlalu volatile
        elif atr_pct >= self.LOW_THRESHOLD:
            risk = "MEDIUM"
            confidence = 1.0  # ideal untuk trading
        else:
            risk = "LOW"
            confidence = 0.7  # kurang volatile

        return VolatilityAnalysis(
            atr=atr,
            atr_normalized=round(atr_pct, 2),
            risk_level=risk,
            confidence_score=confidence,
            timestamp=datetime.now(UTC),
        )