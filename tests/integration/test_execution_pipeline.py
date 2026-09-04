"""Integration test: Recommendation → Execution."""

from datetime import UTC, datetime

from src.core.models.execution import ExecutionPlan
from src.core.models.recommendation import RecommendationResult
from src.core.models.risk import RiskResult
from src.core.models.validation import ValidationResult
from src.core.types.enums import (
    ConfidenceLevel,
    ExecutionAction,
    ExecutionStatus,
    RecommendationAction,
    RecommendationReason,
    SetupType,
    Side,
    ValidationCheck,
)
from src.execution.execution_planner import ExecutionPlanner


class TestExecutionPipeline:
    def test_full_execution_flow(self):
        rec = RecommendationResult(
            action=RecommendationAction.BUY,
            summary="Strong bullish",
            reasons=[RecommendationReason.VALIDATED_SETUP],
            warnings=[],
            confidence_score=0.85,
            confidence_level=ConfidenceLevel.HIGH,
            setup_type=SetupType.TREND_FOLLOWING,
            direction=Side.LONG,
            validation_result=ValidationResult(
                approved=True,
                rejection_reasons=[],
                checks_passed={vc: True for vc in ValidationCheck},
                timestamp=datetime.now(UTC),
            ),
            risk_result=RiskResult(
                entry_price=50000.0,
                stop_loss=48000.0,
                stop_distance=2000.0,
                take_profit=55000.0,
                take_profit_distance=5000.0,
                position_size=0.1,
                risk_amount=200.0,
                expected_profit=500.0,
                expected_loss=200.0,
                risk_reward_ratio=2.5,
                max_loss_pct=2.0,
                direction=Side.LONG,
                risk_model="trend",
                timestamp=datetime.now(UTC),
            ),
            ready_for_execution=True,
            timestamp=datetime.now(UTC),
        )
        risk = RiskResult(
            entry_price=50000.0,
            stop_loss=48000.0,
            stop_distance=2000.0,
            take_profit=55000.0,
            take_profit_distance=5000.0,
            position_size=0.1,
            risk_amount=200.0,
            expected_profit=500.0,
            expected_loss=200.0,
            risk_reward_ratio=2.5,
            max_loss_pct=2.0,
            direction=Side.LONG,
            risk_model="trend",
            warnings=[],
            timestamp=datetime.now(UTC),
        )
        validation = ValidationResult(
            approved=True,
            rejection_reasons=[],
            checks_passed={vc: True for vc in ValidationCheck},
            timestamp=datetime.now(UTC),
        )

        planner = ExecutionPlanner()
        result = planner.plan(rec, risk, validation)

        assert isinstance(result, ExecutionPlan)
        assert result.action == ExecutionAction.PLACE_ORDER
        assert result.status == ExecutionStatus.READY
        assert result.side == Side.LONG
