"""Validated Decision model — hasil validasi DecisionResult."""

from datetime import datetime

from pydantic import BaseModel


class ValidatedDecision(BaseModel):
    symbol: str
    decision: str          # BUY / SELL / WAIT
    confidence: int        # 0–100
    risk_level: str        # LOW / MEDIUM / HIGH
    reasoning: list[str]
    validation_passed: bool
    validation_errors: list[str]
    validated_timestamp: datetime