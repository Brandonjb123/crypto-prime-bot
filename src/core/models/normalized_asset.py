from pydantic import BaseModel


class NormalizedAsset(BaseModel):
    """Normalized asset data hasil processing dari normalizer."""

    symbol: str
    current_price: float
    volume_24h: float | None = None
    price_change_24h: float | None = None
    raw_data: dict | None = None
