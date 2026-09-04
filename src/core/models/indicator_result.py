"""Indicator Result model — hasil kalkulasi teknikal."""

from datetime import datetime

from pydantic import BaseModel


class IndicatorResult(BaseModel):
    symbol: str
    timeframe: str
    ema20: float | None = None
    ema50: float | None = None
    rsi14: float | None = None
    atr14: float | None = None
    average_volume: float | None = None
    highest_high: float | None = None
    lowest_low: float | None = None
    timestamp: datetime