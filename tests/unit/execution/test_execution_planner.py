from datetime import UTC, datetime

from src.core.models.recommendation import RecommendationResult
from src.core.models.risk import RiskResult
from src.core.models.validation import ValidationResult
from src.core.types.enums import (
    ConfidenceLevel,
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    RecommendationAction,
    RecommendationReason,
    RiskWarning,
    SetupType,
    Side,
    ValidationCheck,
    ValidationReason,
)
from src.execution.execution_planner import ExecutionPlanner


def _make_recommendation(
    action=RecommendationAction.BUY,
    ready=True,
    direction=Side.LONG,
    confidence=0.85,
    setup_type=SetupType.TREND_FOLLOWING,
):
    return RecommendationResult(
        action=action,
        summary="Test summary",
        reasons=[RecommendationReason.VALIDATED_SETUP],
        warnings=[],
        confidence_score=confidence,
        confidence_level=ConfidenceLevel.HIGH,
        setup_type=setup_type,
        direction=direction,
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
        ready_for_execution=ready,
        timestamp=datetime.now(UTC),
    )


def _make_risk():
    return RiskResult(
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


def _make_validation(approved=True):
    return ValidationResult(
        approved=approved,
        rejection_reasons=[],
        checks_passed={vc: True for vc in ValidationCheck},
        timestamp=datetime.now(UTC),
    )


class TestExecutionPlanner:
    def pln(self):
        return ExecutionPlanner()

    def test_buy_place_order(self):
        result = self.pln().plan(
            _make_recommendation(RecommendationAction.BUY, True, Side.LONG),
            _make_risk(),
            _make_validation(),
        )
        assert result.action == ExecutionAction.PLACE_ORDER
        assert result.status == ExecutionStatus.READY
        assert result.side == Side.LONG
        assert result.execution_type == ExecutionType.MARKET

    def test_sell_place_order(self):
        result = self.pln().plan(
            _make_recommendation(RecommendationAction.SELL, True, Side.SHORT),
            _make_risk(),
            _make_validation(),
        )
        assert result.action == ExecutionAction.PLACE_ORDER
        assert result.side == Side.SHORT

    def test_wait_do_not_execute(self):
        result = self.pln().plan(
            _make_recommendation(RecommendationAction.WAIT, False, None),
            _make_risk(),
            _make_validation(),
        )
        assert result.action == ExecutionAction.DO_NOT_EXECUTE
        assert result.status == ExecutionStatus.BLOCKED

    def test_skip_do_not_execute(self):
        result = self.pln().plan(
            _make_recommendation(RecommendationAction.SKIP, False, None),
            _make_risk(),
            _make_validation(),
        )
        assert result.action == ExecutionAction.DO_NOT_EXECUTE

    def test_not_ready_blocked(self):
        result = self.pln().plan(
            _make_recommendation(ready=False), _make_risk(), _make_validation()
        )
        assert result.action == ExecutionAction.DO_NOT_EXECUTE
        assert result.status == ExecutionStatus.BLOCKED

    def test_ready_status(self):
        result = self.pln().plan(_make_recommendation(ready=True), _make_risk(), _make_validation())
        assert result.status == ExecutionStatus.READY
        assert result.action == ExecutionAction.PLACE_ORDER

    def test_blocked_status(self):
        result = self.pln().plan(
            _make_recommendation(ready=False), _make_risk(), _make_validation(False)
        )
        assert result.status == ExecutionStatus.BLOCKED

    def test_forward_warnings(self):
        risk = _make_risk()
        risk.warnings = [RiskWarning.RR_TOO_LOW, RiskWarning.POSITION_SIZE_CAPPED]
        result = self.pln().plan(_make_recommendation(), risk, _make_validation())
        assert RiskWarning.RR_TOO_LOW in result.warnings
        assert RiskWarning.POSITION_SIZE_CAPPED in result.warnings

    def test_forward_validation_reasons(self):
        validation = _make_validation(False)
        validation.rejection_reasons = [
            ValidationReason.LOW_CONFIDENCE,
            ValidationReason.BLOCKED_REASONS,
        ]
        result = self.pln().plan(_make_recommendation(ready=False), _make_risk(), validation)
        assert ValidationReason.LOW_CONFIDENCE in result.validation_reasons
        assert ValidationReason.BLOCKED_REASONS in result.validation_reasons

    def test_summary_generated(self):
        result = self.pln().plan(_make_recommendation(), _make_risk(), _make_validation())
        assert len(result.summary) > 0
        assert "READY" in result.summary

    def test_deterministic(self):
        planner = self.pln()
        rec = _make_recommendation()
        risk = _make_risk()
        val = _make_validation()
        r1 = planner.plan(rec, risk, val)
        r2 = planner.plan(rec, risk, val)
        assert r1.action == r2.action
        assert r1.status == r2.status
        assert r1.side == r2.side
