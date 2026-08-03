"""Normalized asset models — Sprint 2 final."""

from datetime import datetime

from pydantic import BaseModel

from src.core.models.candle import Candle


class NormalizedAsset(BaseModel):
    """Final normalized asset — kontrak antar layer. Tidak boleh diubah tanpa review."""

    symbol: str
    price: float
    volume_24h: float
    volume_spike_ratio: float
    market_cap: float
    price_change_24h: float
    price_change_7d: float
    funding_rate: float
    open_interest: float
    long_short_ratio: float
    fear_greed_value: int
    fear_greed_classification: str
    news_headlines: list[str]
    candles_4h: list[Candle]
    candles_1h: list[Candle]
    data_quality_score: float
    timestamp: datetime


# ── Raw Data Models (dari Sprint 1, tetap dipertahankan) ──

class RawBinanceData(BaseModel):
    symbol: str
    candles_4h: list
    candles_1h: list
    funding_rate: float
    open_interest: float
    long_short_ratio: float


class RawCoinGeckoData(BaseModel):
    symbol: str
    coin_id: str
    current_price: float
    market_cap: float
    total_volume: float
    price_change_24h: float
    price_change_7d: float


class RawFearGreedData(BaseModel):
    symbol: str
    value: int
    classification: str
    timestamp: int


class RawNewsData(BaseModel):
    symbol: str
    headlines: list[str]
    article_count: int