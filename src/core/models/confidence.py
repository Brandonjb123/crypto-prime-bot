"""Confidence Engine output model."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import ConfidenceLevel


class ConfidenceResult(BaseModel):
    """Hasil analisis confidence dari semua Analysis Engines."""

    score: float
    level: ConfidenceLevel
    positive_factors: list[str]
    negative_factors: list[str]
    warnings: list[str]
    is_tradeable: bool
    timestamp: datetime