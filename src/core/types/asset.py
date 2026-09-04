from pydantic import BaseModel


class Asset(BaseModel):
    """Normalized asset object untuk semua data collectors."""

    symbol: str
    name: str | None = None
    coingecko_id: str | None = None
    current_price: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    price_change_24h: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
