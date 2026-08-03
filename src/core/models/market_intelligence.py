"""Output models untuk Market Intelligence Engines (Sprint 3C)."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import SentimentLevel, VolumeSignal


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