"""Recommendation Engine — decision aggregation."""

from datetime import UTC, datetime

from config.constants import READY_EXECUTION_MIN_CONFIDENCE, READY_EXECUTION_MIN_RR
from src.core.models.recommendation import RecommendationResult
from src.core.models.risk import RiskResult
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.validation import ValidationResult
from src.core.types.enums import (
    RecommendationAction,
    RecommendationReason,
    Side,
)


class RecommendationEngine:
    def recommend(
        self,
        snapshot: AnalysisSnapshot,
        setup: SetupResult,
        validation: ValidationResult,
        risk: RiskResult,
    ) -> RecommendationResult:
        # ── Reasons & Warnings ──
        reasons: list[RecommendationReason] = []
        warnings: list = risk.warnings if hasattr(risk, "warnings") else []

        # ── Action Mapping ──
        action = self._determine_action(validation, setup, snapshot)

        # ── Ready for Execution ──
        ready = self._is_ready(validation, setup, risk, snapshot)

        # ── Reasons Collection ──
        if not validation.approved:
            reasons.append(RecommendationReason.VALIDATION_FAILED)
        elif setup.direction is None or not setup.is_valid_setup:
            reasons.append(RecommendationReason.NO_SETUP)
            reasons.append(RecommendationReason.SIDEWAYS_MARKET)
        elif validation.approved and setup.is_valid_setup:
            reasons.append(RecommendationReason.VALIDATED_SETUP)

        if setup.blocked_reasons:
            reasons.append(RecommendationReason.BLOCKED_WARNING)

        if risk.risk_reward_ratio < READY_EXECUTION_MIN_RR:
            reasons.append(RecommendationReason.LOW_RISK_REWARD)

        if setup.confidence_score < READY_EXECUTION_MIN_CONFIDENCE:
            reasons.append(RecommendationReason.LOW_CONFIDENCE)

        if risk.risk_reward_ratio < READY_EXECUTION_MIN_RR or risk.max_loss_pct > 5.0:
            reasons.append(RecommendationReason.HIGH_RISK)

        # ── Summary ──
        summary = self._build_summary(action, setup, validation, risk)

        return RecommendationResult(
            action=action,
            summary=summary,
            reasons=reasons,
            warnings=warnings,
            confidence_score=setup.confidence_score,
            confidence_level=setup.confidence_level,
            setup_type=setup.setup_type,
            direction=setup.direction,
            validation_result=validation,
            risk_result=risk,
            ready_for_execution=ready,
            timestamp=datetime.now(UTC),
        )

    def _determine_action(
        self,
        validation: ValidationResult,
        setup: SetupResult,
        snapshot: AnalysisSnapshot,
    ) -> RecommendationAction:
        if not validation.approved:
            return RecommendationAction.SKIP
        if setup.direction is None or not setup.is_valid_setup:
            return RecommendationAction.WAIT
        if setup.direction == Side.LONG:
            return RecommendationAction.BUY
        if setup.direction == Side.SHORT:
            return RecommendationAction.SELL
        return RecommendationAction.WAIT

    def _is_ready(
        self,
        validation: ValidationResult,
        setup: SetupResult,
        risk: RiskResult,
        snapshot: AnalysisSnapshot,
    ) -> bool:
        return (
            validation.approved
            and setup.direction is not None
            and setup.is_valid_setup
            and setup.confidence_score >= READY_EXECUTION_MIN_CONFIDENCE
            and risk.risk_reward_ratio >= READY_EXECUTION_MIN_RR
            and not setup.blocked_reasons
        )

    def _build_summary(
        self,
        action: RecommendationAction,
        setup: SetupResult,
        validation: ValidationResult,
        risk: RiskResult,
    ) -> str:
        if action == RecommendationAction.BUY:
            return f"Strong bullish {setup.setup_type.value if setup.setup_type else 'trend'} setup with acceptable risk."
        elif action == RecommendationAction.SELL:
            return f"Strong bearish {setup.setup_type.value if setup.setup_type else 'trend'} setup with acceptable risk."
        elif action == RecommendationAction.SKIP:
            return "Validation failed due to blocking reasons or low confidence."
        elif action == RecommendationAction.WAIT:
            return "No valid setup detected. Waiting for better market conditions."
        return "Insufficient data for recommendation."
