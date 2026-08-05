"""Setup Detection result model."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import (
    ConfidenceLevel,
    ConfidenceWarning,
    RuleType,
    SetupType,
    Side,
)


class SetupResult(BaseModel):
    """Hasil deteksi setup trading."""

    direction: Side | None
    setup_type: SetupType | None
    triggered_rules: list[RuleType]
    failed_rules: list[RuleType]
    confidence_score: float
    confidence_level: ConfidenceLevel
    blocked_reasons: list[ConfidenceWarning]
    is_valid_setup: bool
    reasoning: list[str]
    timestamp: datetime