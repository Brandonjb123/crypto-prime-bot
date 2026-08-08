"""Indicator Engine — menghitung indikator dari MarketSnapshot."""

from datetime import UTC, datetime

from src.analysis.indicators.atr import ATRCalculator
from src.analysis.indicators.ema import EMACalculator
from src.analysis.indicators.rsi import RSICalculator
from src.core.models.candle import Candle
from src.core.models.indicator_result import IndicatorResult
from src.core.models.market_snapshot import MarketSnapshot
from src.logging.logger import get_logger

logger = get_logger("indicator_engine")


class IndicatorEngine:
    def __init__(self) -> None:
        self.ema_calc = EMACalculator()
        self.rsi_calc = RSICalculator()
        self.atr_calc = ATRCalculator()

    def calculate(self, snapshot: MarketSnapshot) -> IndicatorResult:
        logger.info("Calculating indicators...")

        # Konversi candles mentah ke list[Candle]
        candles = self._parse_candles(snapshot.candles)

        # EMA
        ema20 = self.ema_calc.calculate(candles, period=20)
        ema50 = self.ema_calc.calculate(candles, period=50)

        # RSI
        rsi14 = self.rsi_calc.calculate(candles, period=14)

        # ATR
        atr14 = self.atr_calc.calculate(candles, period=14)

        # Average Volume
        avg_volume = self._average_volume(candles)

        # Highest High / Lowest Low
        high = max(c.high for c in candles) if candles else None
        low = min(c.low for c in candles) if candles else None

        logger.info("IndicatorResult created")

        return IndicatorResult(
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe,
            ema20=ema20,
            ema50=ema50,
            rsi14=rsi14,
            atr14=atr14,
            average_volume=avg_volume,
            highest_high=high,
            lowest_low=low,
            timestamp=datetime.now(UTC),
        )

    def _parse_candles(self, raw_candles: list) -> list[Candle]:
        """Parsing raw Binance klines ke list Candle."""
        parsed = []
        for k in raw_candles:
            try:
                parsed.append(
                    Candle(
                        timestamp=datetime.fromtimestamp(k[0] / 1000, UTC),
                        open=float(k[1]),
                        high=float(k[2]),
                        low=float(k[3]),
                        close=float(k[4]),
                        volume=float(k[5]),
                    )
                )
            except (IndexError, ValueError):
                continue
        return parsed

    def _average_volume(self, candles: list[Candle]) -> float | None:
        if not candles:
            return None
        return round(sum(c.volume for c in candles) / len(candles), 2)