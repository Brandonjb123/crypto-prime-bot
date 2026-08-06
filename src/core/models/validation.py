"""Validation result model."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import ValidationCheck, ValidationReason


class ValidationResult(BaseModel):
    approved: bool
    rejection_reasons: list[ValidationReason]
    checks_passed: list[ValidationCheck]
    timestamp: datetime