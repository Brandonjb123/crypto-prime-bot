"""Execution Plan model."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import (
    ConfidenceWarning,
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    RecommendationAction,
    RiskWarning,
    Side,
    ValidationReason,
)


class ExecutionPlan(BaseModel):
    action: ExecutionAction
    status: ExecutionStatus
    execution_type: ExecutionType
    side: Side | None
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_reward_ratio: float
    confidence_score: float
    recommendation_action: RecommendationAction
    summary: str
    blocked_reasons: list[ConfidenceWarning]
    validation_reasons: list[ValidationReason]
    warnings: list[RiskWarning]
    timestamp: datetime