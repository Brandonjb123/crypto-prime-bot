from typing import Optional
from pydantic import BaseModel


class Asset(BaseModel):
    """Normalized asset object untuk semua data collectors."""
    symbol: str
    name: Optional[str] = None
    coingecko_id: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None