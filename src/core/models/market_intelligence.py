"""Output models untuk Market Intelligence Engines (Sprint 3C)."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import SentimentLevel, VolumeSignal


class SentimentAnalysis(BaseModel):
    """Hasil analisis sentimen (Fear & Greed + News)."""
    overall: SentimentLevel      # GREED | NEUTRAL | FEAR
    fear_greed_value: int        # 0-100
    fear_greed_label: str        # classification dari API
    news_score: float            # -1.0 to 1.0
    news_headline_count: int
    confidence_score: float      # 0.0-1.0
    timestamp: datetime

class VolumeAnalysis(BaseModel):
    """Hasil analisis volume."""
    state: VolumeSignal
    spike_ratio: float
    confidence_score: float
    timestamp: datetime


class FuturesAnalysis(BaseModel):
    """Hasil analisis futures market."""
    sentiment: SentimentLevel
    funding_rate: float
    open_interest: float
    long_short_ratio: float
    confidence_score: float
    timestamp: datetime


class VolatilityAnalysis(BaseModel):
    """Hasil analisis volatilitas."""
    atr: float
    atr_normalized: float
    risk_level: str  # LOW | MEDIUM | HIGH
    confidence_score: float
    timestamp: datetime


class SupportResistanceResult(BaseModel):
    """Hasil deteksi support & resistance."""
    nearest_support: float | None
    nearest_resistance: float | None
    price_position: float
    confidence_score: float
    timestamp: datetime