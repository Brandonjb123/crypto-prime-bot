"""Trend Engine — menentukan TrendDirection dari TechnicalAnalysis."""

from src.core.models.analysis import TechnicalAnalysis
from src.core.types.enums import TrendDirection


class TrendEngine:
    """Analyze trend direction berdasarkan EMA dan price."""

    def analyze(self, technical: TechnicalAnalysis, price: float) -> TrendDirection:
        """
        Tentukan trend direction.

        Args:
            technical: TechnicalAnalysis hasil dari TechnicalAnalysisEngine
            price: Harga terbaru (dari NormalizedAsset.price)

        Returns:
            TrendDirection: BULLISH, BEARISH, atau SIDEWAYS
        """
        # Kalau EMA tidak tersedia → SIDEWAYS
        if technical.ema20 is None or technical.ema50 is None:
            return TrendDirection.SIDEWAYS

        # BULLISH: EMA20 > EMA50 AND price > EMA20
        if technical.ema20 > technical.ema50 and price > technical.ema20:
            return TrendDirection.BULLISH

        # BEARISH: EMA20 < EMA50 AND price < EMA20
        if technical.ema20 < technical.ema50 and price < technical.ema20:
            return TrendDirection.BEARISH

        # Semua kondisi lain → SIDEWAYS
        return TrendDirection.SIDEWAYS
