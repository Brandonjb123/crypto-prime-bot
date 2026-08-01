from pydantic import BaseModel
from typing import Optional


class NormalizedAsset(BaseModel):
    """Normalized asset data hasil processing dari normalizer."""
    symbol: str
    current_price: float
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    raw_data: Optional[dict] = None