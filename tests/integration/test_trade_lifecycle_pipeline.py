"""Integration test: PositionManager → TradeLifecycleEngine."""

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
from src.lifecycle.trade_lifecycle_engine import TradeLifecycleEngine
from src.position.position_manager import PositionManager


class TestTradeLifecyclePipeline:
    def test_full_lifecycle_flow(self):
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

        engine = TradeLifecycleEngine()

        # HOLD
        action, fraction = engine.evaluate(pos, 51000.0)
        assert action == "HOLD"
        assert fraction == 0.0

        # HIT TP2 (karena tidak ada tp1/tp2 spesifik, take_profit lama dianggap TP2)
        action, fraction = engine.evaluate(pos, 55000.0)
        assert action == "TP2"
        assert fraction == 1.0