"""Unit tests untuk TradeLifecycleEngine."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.lifecycle.trade_lifecycle_engine import TradeLifecycleEngine


def _make_position(
    side=Side.LONG,
    status=PositionStatus.OPEN,
    entry=50000.0,
    sl=48000.0,
    tp=55000.0,
    tp1=None,
    tp2=None,
):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol="BTC/USDT",
        side=side,
        status=status,
        entry_price=entry,
        stop_loss=sl,
        take_profit=tp,
        tp1_price=tp1,
        tp2_price=tp2,
        position_size=0.1,
        opened_at=datetime.now(UTC),
        closed_at=None if status == PositionStatus.OPEN else datetime.now(UTC),
        close_reason=PositionCloseReason.NONE
        if status == PositionStatus.OPEN
        else PositionCloseReason.MANUAL,
    )


class TestTradeLifecycleEngine:
    def engine(self):
        return TradeLifecycleEngine()

    def test_long_hold(self):
        action, fraction = self.engine().evaluate(_make_position(Side.LONG), 51000.0)
        assert action == "HOLD"
        assert fraction == 0.0

    def test_long_hit_sl(self):
        action, fraction = self.engine().evaluate(_make_position(Side.LONG), 48000.0)
        assert action == "SL"
        assert fraction == 1.0

    def test_long_hit_tp1(self):
        pos = _make_position(Side.LONG, tp1=52000.0, tp2=55000.0)
        action, fraction = self.engine().evaluate(pos, 52000.0)
        assert action == "TP1"
        assert fraction == 0.5

    def test_long_hit_tp2(self):
        pos = _make_position(Side.LONG, tp1=52000.0, tp2=55000.0)
        action, fraction = self.engine().evaluate(pos, 55000.0)
        assert action == "TP2"
        assert fraction == 1.0

    def test_short_hold(self):
        pos = _make_position(Side.SHORT, sl=52000.0, tp=45000.0)
        action, fraction = self.engine().evaluate(pos, 50000.0)
        assert action == "HOLD"
        assert fraction == 0.0

    def test_short_hit_sl(self):
        pos = _make_position(Side.SHORT, sl=52000.0, tp=45000.0)
        action, fraction = self.engine().evaluate(pos, 52000.0)
        assert action == "SL"
        assert fraction == 1.0

    def test_short_hit_tp1(self):
        pos = _make_position(Side.SHORT, sl=52000.0, tp=45000.0, tp1=47000.0, tp2=45000.0)
        action, fraction = self.engine().evaluate(pos, 47000.0)
        assert action == "TP1"
        assert fraction == 0.5

    def test_short_hit_tp2(self):
        pos = _make_position(Side.SHORT, sl=52000.0, tp=45000.0, tp1=47000.0, tp2=45000.0)
        action, fraction = self.engine().evaluate(pos, 45000.0)
        assert action == "TP2"
        assert fraction == 1.0

    def test_already_closed_no_change(self):
        closed_pos = _make_position(status=PositionStatus.CLOSED)
        action, fraction = self.engine().evaluate(closed_pos, 51000.0)
        assert action == "HOLD"
        assert fraction == 0.0

    def test_deterministic(self):
        engine = TradeLifecycleEngine()
        pos = _make_position(Side.LONG, tp1=52000.0, tp2=55000.0)
        r1 = engine.evaluate(pos, 53000.0)
        r2 = engine.evaluate(pos, 53000.0)
        assert r1 == r2