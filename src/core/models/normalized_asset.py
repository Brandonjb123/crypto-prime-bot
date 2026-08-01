"""Normalized asset models — Sprint 1 RawData types."""

from pydantic import BaseModel


class NormalizedAsset(BaseModel):
    """Normalized asset data hasil processing dari normalizer."""
    symbol: str
    current_price: float
    volume_24h: float | None = None
    price_change_24h: float | None = None
    raw_data: dict | None = None


# ── Raw Data Models per Collector ──

class RawBinanceData(BaseModel):
    """Raw data dari Binance Futures API."""
    symbol: str
    candles_4h: list
    candles_1h: list
    funding_rate: float
    open_interest: float
    long_short_ratio: float


class RawCoinGeckoData(BaseModel):
    """Raw data dari CoinGecko API."""
    symbol: str
    coin_id: str
    current_price: float
    market_cap: float
    total_volume: float
    price_change_24h: float
    price_change_7d: float


class RawFearGreedData(BaseModel):
    """Raw data dari Fear & Greed Index."""
    symbol: str
    value: int
    classification: str
    timestamp: int


class RawNewsData(BaseModel):
    """Raw data dari Google News RSS."""
    symbol: str
    headlines: list[str]
    article_count: int