"""Unit tests untuk TradeRiskEngine."""

from datetime import UTC, datetime

import pytest

from src.core.models.trade_plan import TradePlan
from src.core.models.validated_decision import ValidatedDecision
from src.risk.trade_risk_engine import TradeRiskEngine


def _make_validated(**overrides):
    defaults = dict(
        symbol="BTC",
        decision="BUY",
        confidence=85,
        risk_level="LOW",
        reasoning=["Bullish trend"],
        validation_passed=True,
        validation_errors=[],
        validated_timestamp=datetime.now(UTC),
    )
    defaults.update(overrides)
    return ValidatedDecision(**defaults)


class TestTradeRiskEngine:
    def test_buy_creates_trade_plan(self):
        engine = TradeRiskEngine()
        validated = _make_validated(decision="BUY")
        plan = engine.calculate(validated, entry_price=50000.0, atr=1000.0)

        assert isinstance(plan, TradePlan)
        assert plan.decision == "BUY"
        assert plan.entry_price == 50000.0
        assert plan.position_size > 0
        assert plan.stop_loss < 50000.0
        assert plan.take_profit > 50000.0
        assert plan.risk_reward_ratio > 0
        assert plan.estimated_loss > 0
        assert plan.estimated_profit > 0

    def test_sell_creates_trade_plan(self):
        engine = TradeRiskEngine()
        validated = _make_validated(decision="SELL")
        plan = engine.calculate(validated, entry_price=50000.0, atr=1000.0)

        assert plan.decision == "SELL"
        assert plan.stop_loss > 50000.0
        assert plan.take_profit < 50000.0

    def test_wait_returns_empty_plan(self):
        engine = TradeRiskEngine()
        validated = _make_validated(decision="WAIT")
        plan = engine.calculate(validated, entry_price=50000.0, atr=1000.0)

        assert plan.decision == "WAIT"
        assert plan.position_size == 0.0
        assert plan.entry_price is None
        assert plan.stop_loss is None
        assert plan.take_profit is None

    def test_invalid_atr_returns_wait(self):
        engine = TradeRiskEngine()
        validated = _make_validated(decision="BUY")
        plan = engine.calculate(validated, entry_price=50000.0, atr=0.0)

        assert plan.decision == "WAIT"
        assert plan.position_size == 0.0

    def test_position_size_calculation(self):
        engine = TradeRiskEngine(risk_percent=2.0)
        validated = _make_validated(decision="BUY")
        plan = engine.calculate(validated, entry_price=50000.0, atr=1000.0, account_balance=1000.0)

        # max_risk = 1000 * 2% = 20
        # sl_distance = 1000 * 1.5 = 1500
        # position_size = 20 / 1500 = 0.01333...
        assert plan.position_size == pytest.approx(0.013333, rel=0.01)
        assert plan.estimated_loss == pytest.approx(20.0, rel=0.1)

    def test_risk_reward_ratio(self):
        engine = TradeRiskEngine(risk_reward=2.0)
        validated = _make_validated(decision="BUY")
        plan = engine.calculate(validated, entry_price=50000.0, atr=1000.0)

        # tp_distance = 1000 * 3.0 = 3000
        # sl_distance = 1000 * 1.5 = 1500
        # rr = 3000 / 1500 = 2.0
        assert plan.risk_reward_ratio == 2.0

    def test_zero_balance(self):
        engine = TradeRiskEngine()
        validated = _make_validated(decision="BUY")
        plan = engine.calculate(validated, entry_price=50000.0, atr=1000.0, account_balance=0.0)

        assert plan.position_size == 0.0
        assert plan.estimated_loss == 0.0

    def test_configurable_multipliers(self):
        engine = TradeRiskEngine(atr_sl_multiplier=2.0, atr_tp_multiplier=4.0)
        validated = _make_validated(decision="BUY")
        plan = engine.calculate(validated, entry_price=50000.0, atr=1000.0)

        # sl_distance = 1000 * 2.0 = 2000
        # tp_distance = 1000 * 4.0 = 4000
        assert plan.stop_loss == 48000.0
        assert plan.take_profit == 54000.0