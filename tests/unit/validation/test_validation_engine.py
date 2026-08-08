"""Unit tests untuk ValidationEngine."""

from datetime import UTC, datetime

from src.core.models.decision_result import DecisionResult
from src.core.models.validated_decision import ValidatedDecision
from src.validation.validation_engine import ValidationEngine


def _make_decision(**overrides):
    defaults = dict(
        symbol="BTC",
        decision="BUY",
        confidence=85,
        risk_level="LOW",
        reasoning=["Bullish trend", "Strong momentum"],
        model="claude-haiku",
        timestamp=datetime.now(UTC),
    )
    defaults.update(overrides)
    return DecisionResult(**defaults)


class TestValidationEngine:
    def test_valid_decision_passes(self):
        engine = ValidationEngine(confidence_threshold=70)
        decision = _make_decision()
        result = engine.validate(decision)

        assert isinstance(result, ValidatedDecision)
        assert result.validation_passed is True
        assert result.validation_errors == []
        assert result.decision == "BUY"

    def test_confidence_below_threshold(self):
        engine = ValidationEngine(confidence_threshold=70)
        decision = _make_decision(confidence=50)
        result = engine.validate(decision)

        assert result.validation_passed is False
        assert "Confidence below threshold" in result.validation_errors
        assert result.decision == "WAIT"

    def test_decision_invalid(self):
        engine = ValidationEngine(confidence_threshold=70)
        decision = _make_decision(decision="HOLD")
        result = engine.validate(decision)

        assert result.validation_passed is False
        assert "Decision invalid" in result.validation_errors
        assert result.decision == "WAIT"

    def test_risk_level_high(self):
        engine = ValidationEngine(confidence_threshold=70)
        decision = _make_decision(risk_level="HIGH")
        result = engine.validate(decision)

        assert result.validation_passed is False
        assert "Risk level HIGH" in result.validation_errors
        assert result.decision == "WAIT"

    def test_reasoning_empty(self):
        engine = ValidationEngine(confidence_threshold=70)
        decision = _make_decision(reasoning=[])
        result = engine.validate(decision)

        assert result.validation_passed is False
        assert "Reasoning empty" in result.validation_errors
        assert result.decision == "WAIT"

    def test_multiple_errors(self):
        engine = ValidationEngine(confidence_threshold=70)
        decision = _make_decision(decision="HOLD", confidence=30, risk_level="HIGH", reasoning=[])
        result = engine.validate(decision)

        assert result.validation_passed is False
        assert len(result.validation_errors) >= 3
        assert result.decision == "WAIT"

    def test_confidence_out_of_range(self):
        engine = ValidationEngine(confidence_threshold=70)
        decision = _make_decision(confidence=150)
        result = engine.validate(decision)

        assert result.validation_passed is False
        assert "Confidence out of range" in result.validation_errors

    def test_risk_level_invalid(self):
        engine = ValidationEngine(confidence_threshold=70)
        decision = _make_decision(risk_level="UNKNOWN")
        result = engine.validate(decision)

        assert result.validation_passed is False
        assert "Risk level invalid" in result.validation_errors