"""Market snapshot model — data mentah dari collector."""

from datetime import datetime

from pydantic import BaseModel


class MarketSnapshot(BaseModel):
    symbol: str
    timeframe: str
    current_price: float
    candles: list  # list of OHLCV candles
    market_cap: float = 0.0
    volume_24h: float = 0.0
    change_24h: float = 0.0
    timestamp: datetime