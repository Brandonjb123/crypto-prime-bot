"""Candle model — abstraction untuk OHLCV data."""

from datetime import datetime

from pydantic import BaseModel


class Candle(BaseModel):
    """Single OHLCV candle, format independen dari source."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
