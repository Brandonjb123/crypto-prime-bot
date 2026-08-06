from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.exceptions.collector_exceptions import (
    DuplicatePositionError,
    PositionAlreadyClosedError,
)
from src.core.models.order import OrderResult
from src.core.types.enums import (
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    PositionCloseReason,
    PositionStatus,
    Side,
)
from src.position.position_manager import PositionManager


def _make_order(status=OrderStatus.FILLED, symbol="BTC/USDT", side=Side.LONG, entry=50000.0, sl=48000.0, tp=55000.0):
    return OrderResult(
        execution_id=uuid4(),
        order_id=uuid4(),
        status=status,
        reject_reason=OrderRejectReason.NONE,
        execution_type=ExecutionType.MARKET,
        side=side,
        symbol=symbol,
        requested_entry=entry,
        executed_entry=entry,
        position_size=0.1,
        stop_loss=sl,
        take_profit=tp,
        timestamp=datetime.now(UTC),
    )


class TestPositionManager:
    def pm(self):
        return PositionManager()

    def test_open_position_success(self):
        pos = self.pm().open_position(_make_order())
        assert pos.status == PositionStatus.OPEN
        assert pos.symbol == "BTC/USDT"
        assert pos.side == Side.LONG

    def test_reject_non_filled_order(self):
        with pytest.raises(ValueError):
            self.pm().open_position(_make_order(OrderStatus.REJECTED))

    def test_duplicate_position(self):
        pm = self.pm()
        pm.open_position(_make_order())
        with pytest.raises(DuplicatePositionError):
            pm.open_position(_make_order())

    def test_close_position_success(self):
        pm = self.pm()
        pos = pm.open_position(_make_order())
        closed = pm.close_position(str(pos.position_id), PositionCloseReason.MANUAL)
        assert closed.status == PositionStatus.CLOSED
        assert closed.close_reason == PositionCloseReason.MANUAL
        assert closed.closed_at is not None

    def test_close_already_closed(self):
        pm = self.pm()
        pos = pm.open_position(_make_order())
        pm.close_position(str(pos.position_id), PositionCloseReason.MANUAL)
        with pytest.raises(PositionAlreadyClosedError):
            pm.close_position(str(pos.position_id), PositionCloseReason.MANUAL)

    def test_get_position(self):
        pm = self.pm()
        pos = pm.open_position(_make_order())
        found = pm.get_position(str(pos.position_id))
        assert found is not None
        assert found.position_id == pos.position_id

    def test_get_open_positions(self):
        pm = self.pm()
        pm.open_position(_make_order(symbol="BTC/USDT"))
        pm.open_position(_make_order(symbol="ETH/USDT"))
        open_pos = pm.get_open_positions()
        assert len(open_pos) == 2

    def test_get_all_positions(self):
        pm = self.pm()
        pos1 = pm.open_position(_make_order(symbol="BTC/USDT"))
        pm.close_position(str(pos1.position_id), PositionCloseReason.MANUAL)
        pm.open_position(_make_order(symbol="ETH/USDT"))
        all_pos = pm.get_all_positions()
        assert len(all_pos) == 2

    def test_has_open_position_true(self):
        pm = self.pm()
        pm.open_position(_make_order(symbol="BTC/USDT"))
        assert pm.has_open_position("BTC/USDT") is True

    def test_has_open_position_false(self):
        pm = self.pm()
        assert pm.has_open_position("BTC/USDT") is False

    def test_registry_consistency(self):
        pm = self.pm()
        pos1 = pm.open_position(_make_order(symbol="BTC/USDT"))
        pm.open_position(_make_order(symbol="ETH/USDT"))
        assert len(pm.get_all_positions()) == 2
        pm.close_position(str(pos1.position_id), PositionCloseReason.MANUAL)
        assert len(pm.get_open_positions()) == 1
        assert len(pm.get_all_positions()) == 2

    def test_immutable_position(self):
        from pydantic import ValidationError
        pos = self.pm().open_position(_make_order())
        with pytest.raises(ValidationError):  # frozen model tidak bisa diubah
            pos.status = PositionStatus.CLOSED

    def test_deterministic(self):
        pm1 = PositionManager()
        pm2 = PositionManager()
        order = _make_order()
        pos1 = pm1.open_position(order)
        pos2 = pm2.open_position(order)
        assert pos1.symbol == pos2.symbol
        assert pos1.side == pos2.side
        assert pos1.entry_price == pos2.entry_price