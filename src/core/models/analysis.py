"""Analysis result models — output dari Analysis Modules."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import (
    MarketStructure,
    SentimentLevel,
    TrendDirection,
    VolumeSignal,
)


class TechnicalAnalysis(BaseModel):
    """Hasil analisis teknikal — EMA, RSI, ATR."""

    ema20: float | None = None
    ema50: float | None = None
    rsi14: float | None = None
    atr14: float | None = None
    timestamp: datetime


class MarketAnalysis(BaseModel):
    """Hasil analisis market structure, volume, futures sentiment."""

    trend: TrendDirection
    market_structure: MarketStructure
    volume_state: VolumeSignal
    futures_sentiment: SentimentLevel
    timestamp: datetime 