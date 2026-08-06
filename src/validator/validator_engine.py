"""Validator Engine — menentukan apakah setup layak diteruskan."""

from datetime import UTC, datetime

from config.constants import VALIDATOR_CONFIDENCE_THRESHOLD
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.validation import ValidationResult
from src.core.types.enums import (
    MarketStructure,
    TrendDirection,
    ValidationCheck,
    ValidationReason,
)


class ValidatorEngine:
    def validate(
        self,
        setup: SetupResult,
        snapshot: AnalysisSnapshot,
        existing_signal_count: int = 0,
    ) -> ValidationResult:
        checks_passed: list[ValidationCheck] = []
        rejections: list[ValidationReason] = []

        # 1. Setup completeness
        if setup.direction is None or not setup.is_valid_setup:
            rejections.append(ValidationReason.NO_SETUP_DETECTED)
        else:
            checks_passed.append(ValidationCheck.SETUP_COMPLETENESS)

        # 2. Blocked reasons
        if setup.blocked_reasons:
            rejections.append(ValidationReason.BLOCKED_REASONS)
        else:
            checks_passed.append(ValidationCheck.BLOCKED_REASONS_CHECK)

        # 3. Confidence
        if setup.confidence_score < VALIDATOR_CONFIDENCE_THRESHOLD:
            rejections.append(ValidationReason.LOW_CONFIDENCE)
        else:
            checks_passed.append(ValidationCheck.CONFIDENCE_CHECK)

        # 4. Market condition (no sideways / no structure)
        if snapshot.trend == TrendDirection.SIDEWAYS or snapshot.structure.structure == MarketStructure.NONE:
            rejections.append(ValidationReason.SIDEWAYS_MARKET)
        else:
            checks_passed.append(ValidationCheck.MARKET_CONDITION)

        # 5. Duplicate signal
        if existing_signal_count > 0:
            rejections.append(ValidationReason.DUPLICATE_SIGNAL)
        else:
            checks_passed.append(ValidationCheck.DUPLICATE_SIGNAL)

        return ValidationResult(
            approved=len(rejections) == 0,
            rejection_reasons=rejections,
            checks_passed=checks_passed,
            timestamp=datetime.now(UTC),
        )