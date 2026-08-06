"""Recommendation Engine result model."""

from datetime import datetime
from pydantic import BaseModel
from src.core.types.enums import (
    ConfidenceLevel, RecommendationAction, RecommendationReason,
    RiskWarning, SetupType, Side,
)
from src.core.models.validation import ValidationResult
from src.core.models.risk import RiskResult


class RecommendationResult(BaseModel):
    action: RecommendationAction
    summary: str
    reasons: list[RecommendationReason]
    warnings: list[RiskWarning]
    confidence_score: float
    confidence_level: ConfidenceLevel
    setup_type: SetupType | None
    direction: Side | None
    validation_result: ValidationResult
    risk_result: RiskResult
    ready_for_execution: bool
    timestamp: datetime