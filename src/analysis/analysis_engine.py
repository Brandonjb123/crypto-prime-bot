"""Market Analysis Engine — interpretasi IndicatorResult menjadi AnalysisResult."""

from datetime import UTC, datetime

from src.core.models.indicator_result import IndicatorResult
from src.core.models.market_analysis import AnalysisResult
from src.logging.logger import get_logger

logger = get_logger("analysis_engine")


class AnalysisEngine:
    def analyze(self, indicators: IndicatorResult) -> AnalysisResult:
        logger.info("Running market analysis...")

        # Trend — EMA20 vs EMA50
        trend = self._trend(indicators)

        # Momentum — RSI14
        momentum = self._momentum(indicators)

        # Volatility — ATR14
        volatility = self._volatility(indicators)

        # Volume Strength — Average Volume vs Last Volume
        volume_strength = self._volume_strength(indicators)

        # Market Structure — Highest High / Lowest Low
        market_structure = self._market_structure(indicators)

        logger.info("AnalysisResult created")

        return AnalysisResult(
            symbol=indicators.symbol,
            timeframe=indicators.timeframe,
            trend=trend,
            momentum=momentum,
            volatility=volatility,
            volume_strength=volume_strength,
            market_structure=market_structure,
            analysis_timestamp=datetime.now(UTC),
        )

    def _trend(self, ind: IndicatorResult) -> str:
        if ind.ema20 is None or ind.ema50 is None:
            return "Sideways"
        if ind.ema20 > ind.ema50:
            return "Bullish"
        elif ind.ema20 < ind.ema50:
            return "Bearish"
        return "Sideways"

    def _momentum(self, ind: IndicatorResult) -> str:
        if ind.rsi14 is None:
            return "Neutral"
        if ind.rsi14 >= 70:
            return "Strong Bullish"
        elif ind.rsi14 >= 55:
            return "Bullish"
        elif ind.rsi14 >= 40:
            return "Neutral"
        elif ind.rsi14 >= 25:
            return "Bearish"
        return "Strong Bearish"

    def _volatility(self, ind: IndicatorResult) -> str:
        if ind.atr14 is None:
            return "Medium"
        if ind.atr14 > 1000:
            return "High"
        elif ind.atr14 > 500:
            return "Medium"
        return "Low"

    def _volume_strength(self, ind: IndicatorResult) -> str:
        if ind.average_volume is None:
            return "Normal"
        if ind.average_volume > 1000:
            return "High"
        elif ind.average_volume > 500:
            return "Normal"
        return "Low"

    def _market_structure(self, ind: IndicatorResult) -> str:
        if ind.highest_high is None:
            return "Range"
        return "Higher High"