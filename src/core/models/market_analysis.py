"""Market Analysis Result model — hasil interpretasi indikator."""

from datetime import datetime

from pydantic import BaseModel


class AnalysisResult(BaseModel):
    symbol: str
    timeframe: str
    trend: str          # Bullish / Bearish / Sideways
    momentum: str       # Strong Bullish / Bullish / Neutral / Bearish / Strong Bearish
    volatility: str     # Low / Medium / High
    volume_strength: str # Low / Normal / High
    market_structure: str # Higher High / Lower High / Higher Low / Lower Low / Range
    analysis_timestamp: datetime