"""Integration test: OrderResult → PositionManager → Position."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.order import OrderResult
from src.core.types.enums import (
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    PositionStatus,
    Side,
)
from src.position.position_manager import PositionManager


class TestPositionPipeline:
    def test_order_to_position(self):
        order = OrderResult(
            execution_id=uuid4(),
            order_id=uuid4(),
            status=OrderStatus.FILLED,
            reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.MARKET,
            side=Side.LONG,
            symbol="BTC/USDT",
            requested_entry=50000.0,
            executed_entry=50000.0,
            position_size=0.1,
            stop_loss=48000.0,
            take_profit=55000.0,
            timestamp=datetime.now(UTC),
        )
        pm = PositionManager()
        pos = pm.open_position(order)

        assert pos.status == PositionStatus.OPEN
        assert pos.symbol == "BTC/USDT"
        assert pos.side == Side.LONG
        assert pos.entry_price == 50000.0
