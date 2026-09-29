"""Test bahwa setiap signal yang di-generate masuk ke repository."""

from datetime import UTC, datetime

from src.core.models.decision_result import DecisionResult
from src.core.models.trade_plan import TradePlan
from src.signal.signal_engine import SignalEngine
from src.storage.adapters.in_memory_signal_repository import InMemorySignalRepository


def _make_trade_plan(decision="BUY", position_size=0.01):
    return TradePlan(
        symbol="BTC",
        decision=decision,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        take_profit_1=51000.0,
        take_profit_2=52000.0,
        position_size=position_size,
        risk_percent=1.0,
        timestamp=datetime.now(UTC),
    )


def _make_decision(confidence=85, reasoning=None, risk_level="MEDIUM"):
    return DecisionResult(
        symbol="BTC",
        decision="BUY",
        confidence=confidence,
        risk_level=risk_level,
        reasoning=reasoning or ["test reasoning"],
        model="test",
        timestamp=datetime.now(UTC),
    )


class TestSignalEnginePropagation:
    def test_confidence_from_decision(self):
        engine = SignalEngine()
        signal = engine.generate(_make_trade_plan(), _make_decision(confidence=85))
        assert signal.confidence == 85

    def test_reasoning_from_decision(self):
        engine = SignalEngine()
        signal = engine.generate(
            _make_trade_plan(), _make_decision(reasoning=["bullish momentum"])
        )
        assert signal.reasoning == ["bullish momentum"]

    def test_risk_level_from_decision(self):
        engine = SignalEngine()
        signal = engine.generate(
            _make_trade_plan(), _make_decision(risk_level="HIGH")
        )
        assert signal.risk_level == "HIGH"


class TestSignalRepositoryPersistence:
    def test_wait_signal_is_appended(self):
        engine = SignalEngine()
        repo = InMemorySignalRepository()
        signal = engine.generate(_make_trade_plan(decision="WAIT"), _make_decision())
        repo.append(signal)
        assert repo.latest_by_symbol("BTC") is not None

    def test_invalid_signal_is_appended(self):
        engine = SignalEngine()
        repo = InMemorySignalRepository()
        signal = engine.generate(
            _make_trade_plan(position_size=0.0), _make_decision()
        )
        repo.append(signal)
        assert repo.latest_by_symbol("BTC").status == "INVALID"