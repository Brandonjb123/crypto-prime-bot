"""Decision Validation Engine — memvalidasi hasil AI sebelum diteruskan."""

from datetime import UTC, datetime

from config.constants import DECISION_CONFIDENCE_THRESHOLD
from src.core.models.decision_result import DecisionResult
from src.core.models.validated_decision import ValidatedDecision
from src.logging.logger import get_logger

logger = get_logger("validation")


class ValidationEngine:
    def __init__(self, confidence_threshold: int = DECISION_CONFIDENCE_THRESHOLD):
        self.confidence_threshold = confidence_threshold

    def validate(self, decision: DecisionResult) -> ValidatedDecision:
        errors: list[str] = []

        # 1. Valid decision value
        if decision.decision not in ("BUY", "SELL", "WAIT"):
            errors.append("Decision invalid")

        # 2. Confidence range
        if not (0 <= decision.confidence <= 100):
            errors.append("Confidence out of range")

        # 3. Confidence threshold
        if decision.confidence < self.confidence_threshold:
            errors.append("Confidence below threshold")

        # 4. Risk level
        if decision.risk_level not in ("LOW", "MEDIUM", "HIGH"):
            errors.append("Risk level invalid")

        # 5. Risk policy: HIGH → WAIT
        if decision.risk_level == "HIGH":
            errors.append("Risk level HIGH")

        # 6. Reasoning tidak kosong
        if not decision.reasoning or len(decision.reasoning) == 0:
            errors.append("Reasoning empty")

        passed = len(errors) == 0

        if passed:
            logger.info("Validation passed")
            final_decision = decision.decision
            final_reasoning = decision.reasoning
        else:
            logger.warning(f"Validation failed: {', '.join(errors)}")
            final_decision = "WAIT"
            final_reasoning = []

        return ValidatedDecision(
            symbol=decision.symbol,
            decision=final_decision,
            confidence=decision.confidence,
            risk_level=decision.risk_level,
            reasoning=final_reasoning,
            validation_passed=passed,
            validation_errors=errors,
            validated_timestamp=datetime.now(UTC),
        )