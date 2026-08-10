"""Unit tests untuk SignalEngine."""

from datetime import UTC, datetime

from src.core.models.trade_plan import TradePlan
from src.core.models.trading_signal import TradingSignal
from src.signal.signal_engine import SignalEngine


def _make_trade_plan(**overrides):
    defaults = dict(
        symbol="BTC",
        decision="BUY",
        entry_price=50000.0,
        position_size=0.1,
        risk_percent=2.0,
        account_balance=1000.0,
        stop_loss=48500.0,
        take_profit=53000.0,
        risk_reward_ratio=2.0,
        estimated_loss=20.0,
        estimated_profit=40.0,
        atr_stop_loss=1500.0,
        atr_take_profit=3000.0,
        timestamp=datetime.now(UTC),
    )
    defaults.update(overrides)
    return TradePlan(**defaults)


class TestSignalEngine:
    def test_active_signal(self):
        engine = SignalEngine()
        plan = _make_trade_plan()
        signal = engine.generate(plan)

        assert isinstance(signal, TradingSignal)
        assert signal.status == "ACTIVE"
        assert signal.side == "BUY"
        assert signal.entry_price == 50000.0
        assert signal.stop_loss == 48500.0
        assert signal.take_profit == 53000.0
        assert signal.position_size == 0.1

    def test_wait_skipped(self):
        engine = SignalEngine()
        plan = _make_trade_plan(decision="WAIT")
        signal = engine.generate(plan)

        assert signal.status == "SKIPPED"
        assert signal.side == "WAIT"
        assert signal.position_size == 0.0

    def test_invalid_position_size(self):
        engine = SignalEngine()
        plan = _make_trade_plan(position_size=0.0)
        signal = engine.generate(plan)

        assert signal.status == "INVALID"
        assert signal.position_size == 0.0

    def test_missing_sl(self):
        engine = SignalEngine()
        plan = _make_trade_plan(stop_loss=None)
        signal = engine.generate(plan)

        assert signal.status == "INVALID"
        assert signal.stop_loss is None

    def test_missing_tp(self):
        engine = SignalEngine()
        plan = _make_trade_plan(take_profit=None)
        signal = engine.generate(plan)

        assert signal.status == "INVALID"
        assert signal.take_profit is None

    def test_signal_id_unique(self):
        engine = SignalEngine()
        plan = _make_trade_plan()
        s1 = engine.generate(plan)
        s2 = engine.generate(plan)
        assert s1.signal_id != s2.signal_id

    def test_status_assignment(self):
        engine = SignalEngine()
        plan = _make_trade_plan(decision="SELL")
        signal = engine.generate(plan)

        assert signal.status == "ACTIVE"
        assert signal.side == "SELL"