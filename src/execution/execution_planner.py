"""Execution Planner — mengubah Recommendation + Risk menjadi ExecutionPlan."""

from datetime import UTC, datetime

from src.core.models.execution import ExecutionPlan
from src.core.models.recommendation import RecommendationResult
from src.core.models.risk import RiskResult
from src.core.models.validation import ValidationResult
from src.core.types.enums import (
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    RecommendationAction,
    Side,
)


class ExecutionPlanner:
    """Planner yang mengubah rekomendasi menjadi rencana eksekusi."""

    def plan(
        self,
        recommendation: RecommendationResult,
        risk: RiskResult,
        validation: ValidationResult,
    ) -> ExecutionPlan:
        # Rule 1: Tidak ready → DO_NOT_EXECUTE
        if not recommendation.ready_for_execution:
            return ExecutionPlan(
                action=ExecutionAction.DO_NOT_EXECUTE,
                status=ExecutionStatus.BLOCKED,
                execution_type=ExecutionType.MARKET,
                side=None,
                entry_price=risk.entry_price,
                stop_loss=risk.stop_loss,
                take_profit=risk.take_profit,
                position_size=risk.position_size,
                risk_reward_ratio=risk.risk_reward_ratio,
                confidence_score=recommendation.confidence_score,
                recommendation_action=recommendation.action,
                summary="Execution blocked: "
                + ", ".join(r.value for r in validation.rejection_reasons)
                if validation.rejection_reasons
                else "Not ready for execution",
                blocked_reasons=recommendation.validation_result.blocked_reasons
                if hasattr(recommendation.validation_result, "blocked_reasons")
                else [],
                validation_reasons=validation.rejection_reasons,
                warnings=risk.warnings,
                timestamp=datetime.now(UTC),
            )

        # Rule 2 & 3: BUY → PLACE_ORDER LONG, SELL → PLACE_ORDER SHORT
        if recommendation.action == RecommendationAction.BUY:
            side = Side.LONG
        elif recommendation.action == RecommendationAction.SELL:
            side = Side.SHORT
        else:
            # Rule 4 & 5: WAIT / SKIP → DO_NOT_EXECUTE
            return ExecutionPlan(
                action=ExecutionAction.DO_NOT_EXECUTE,
                status=ExecutionStatus.BLOCKED,
                execution_type=ExecutionType.MARKET,
                side=None,
                entry_price=risk.entry_price,
                stop_loss=risk.stop_loss,
                take_profit=risk.take_profit,
                position_size=risk.position_size,
                risk_reward_ratio=risk.risk_reward_ratio,
                confidence_score=recommendation.confidence_score,
                recommendation_action=recommendation.action,
                summary=f"No execution: {recommendation.action.value}",
                blocked_reasons=[],
                validation_reasons=validation.rejection_reasons,
                warnings=risk.warnings,
                timestamp=datetime.now(UTC),
            )

        # READY — PLACE_ORDER
        summary = (
            f"READY {side.value} {recommendation.setup_type.value if recommendation.setup_type else 'setup'}\n"
            f"Entry {risk.entry_price:.2f}\n"
            f"SL {risk.stop_loss:.2f}\n"
            f"TP {risk.take_profit:.2f}\n"
            f"RR {risk.risk_reward_ratio:.1f}"
        )

        return ExecutionPlan(
            action=ExecutionAction.PLACE_ORDER,
            status=ExecutionStatus.READY,
            execution_type=ExecutionType.MARKET,
            side=side,
            entry_price=risk.entry_price,
            stop_loss=risk.stop_loss,
            take_profit=risk.take_profit,
            position_size=risk.position_size,
            risk_reward_ratio=risk.risk_reward_ratio,
            confidence_score=recommendation.confidence_score,
            recommendation_action=recommendation.action,
            summary=summary,
            blocked_reasons=[],
            validation_reasons=validation.rejection_reasons,
            warnings=risk.warnings,
            timestamp=datetime.now(UTC),
        )