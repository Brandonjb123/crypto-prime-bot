"""Technical Analysis Engine — orchestrator untuk semua indikator teknikal."""

from datetime import UTC, datetime

from src.analysis.indicators.atr import ATRCalculator
from src.analysis.indicators.ema import EMACalculator
from src.analysis.indicators.rsi import RSICalculator
from src.core.models.analysis import TechnicalAnalysis
from src.core.models.normalized_asset import NormalizedAsset


class TechnicalAnalysisEngine:
    """Orchestrate perhitungan EMA, RSI, ATR dari NormalizedAsset."""

    MIN_CANDLES = 50  # Minimum 50 candle untuk hasil reliable (EMA50 butuh 50)

    def __init__(self) -> None:
        self.ema = EMACalculator()
        self.rsi = RSICalculator()
        self.atr = ATRCalculator()

    def analyze(self, asset: NormalizedAsset) -> TechnicalAnalysis:
        """
        Hitung semua indikator teknikal dari NormalizedAsset.
        
        Kalau candles_4h kurang dari MIN_CANDLES, semua field = None.
        """
        candles = asset.candles_4h

        if len(candles) < self.MIN_CANDLES:
            return TechnicalAnalysis(
                ema20=None,
                ema50=None,
                rsi14=None,
                atr14=None,
                timestamp=datetime.now(UTC),
            )

        return TechnicalAnalysis(
            ema20=self.ema.calculate(candles, period=20),
            ema50=self.ema.calculate(candles, period=50),
            rsi14=self.rsi.calculate(candles, period=14),
            atr14=self.atr.calculate(candles, period=14),
            timestamp=datetime.now(UTC),
        )