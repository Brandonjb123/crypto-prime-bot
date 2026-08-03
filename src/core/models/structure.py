"""Market structure analysis result model."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import MarketStructure, TrendDirection


class MarketStructureResult(BaseModel):
    """Hasil analisis market structure."""
    structure: MarketStructure
    direction: TrendDirection
    swing_high: float | None = None
    swing_low: float | None = None
    timestamp: datetime