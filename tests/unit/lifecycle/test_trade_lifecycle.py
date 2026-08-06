"""Unit tests untuk TradeLifecycleEngine."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.lifecycle.trade_lifecycle_engine import TradeLifecycleEngine


def _make_position(side=Side.LONG, status=PositionStatus.OPEN, entry=50000.0, sl=48000.0, tp=55000.0):
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
        position_size=0.1,
        opened_at=datetime.now(UTC),
        closed_at=None if status == PositionStatus.OPEN else datetime.now(UTC),
        close_reason=PositionCloseReason.NONE if status == PositionStatus.OPEN else PositionCloseReason.MANUAL,
    )


class TestTradeLifecycleEngine:
    def engine(self):
        return TradeLifecycleEngine()

    def test_long_hold(self):
        pos = self.engine().evaluate(_make_position(Side.LONG), 51000.0)
        assert pos.status == PositionStatus.OPEN
        assert pos.last_price == 51000.0
        assert pos.last_updated is not None

    def test_long_hit_tp(self):
        pos = self.engine().evaluate(_make_position(Side.LONG), 55000.0)
        assert pos.status == PositionStatus.TAKE_PROFIT
        assert pos.close_reason == PositionCloseReason.TAKE_PROFIT
        assert pos.closed_at is not None

    def test_long_hit_sl(self):
        pos = self.engine().evaluate(_make_position(Side.LONG), 48000.0)
        assert pos.status == PositionStatus.STOPPED
        assert pos.close_reason == PositionCloseReason.STOP_LOSS

    def test_short_hold(self):
        pos = self.engine().evaluate(_make_position(Side.SHORT, sl=52000.0, tp=45000.0), 50000.0)
        assert pos.status == PositionStatus.OPEN

    def test_short_hit_tp(self):
        pos = self.engine().evaluate(_make_position(Side.SHORT, sl=52000.0, tp=45000.0), 45000.0)
        assert pos.status == PositionStatus.TAKE_PROFIT
        assert pos.close_reason == PositionCloseReason.TAKE_PROFIT

    def test_short_hit_sl(self):
        pos = self.engine().evaluate(_make_position(Side.SHORT, sl=52000.0, tp=45000.0), 52000.0)
        assert pos.status == PositionStatus.STOPPED
        assert pos.close_reason == PositionCloseReason.STOP_LOSS

    def test_already_closed_no_change(self):
        closed_pos = _make_position(status=PositionStatus.CLOSED)
        pos = self.engine().evaluate(closed_pos, 51000.0)
        assert pos.status == PositionStatus.CLOSED
        assert pos.closed_at is not None

    def test_immutable_new_position(self):
        original = _make_position(Side.LONG)
        new_pos = self.engine().evaluate(original, 55000.0)
        # Original tidak berubah
        assert original.status == PositionStatus.OPEN
        assert original.close_reason == PositionCloseReason.NONE
        # Yang baru berubah
        assert new_pos.status == PositionStatus.TAKE_PROFIT

    def test_entry_unchanged(self):
        original = _make_position(Side.LONG, entry=50000.0)
        new_pos = self.engine().evaluate(original, 51000.0)
        assert new_pos.entry_price == 50000.0
        assert new_pos.position_size == 0.1

    def test_timestamp_updated(self):
        pos = self.engine().evaluate(_make_position(Side.LONG), 51000.0)
        assert pos.last_updated is not None

    def test_deterministic(self):
        engine = TradeLifecycleEngine()
        pos = _make_position(Side.LONG)
        r1 = engine.evaluate(pos, 51000.0)
        r2 = engine.evaluate(pos, 51000.0)
        assert r1.status == r2.status
        assert r1.last_price == r2.last_price