"""Setup Detection result model."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import ConfidenceLevel, ConfidenceWarning, Side


class SetupResult(BaseModel):
    """Hasil deteksi setup trading."""

    direction: Side | None
    setup_type: str | None
    triggered_rules: list[str]
    failed_rules: list[str]
    confidence_score: float
    confidence_level: ConfidenceLevel
    blocked_reasons: list[ConfidenceWarning]
    is_valid_setup: bool
    reasoning: list[str]
    timestamp: datetime