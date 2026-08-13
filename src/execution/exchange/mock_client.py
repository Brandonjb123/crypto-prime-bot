"""Mock Exchange Client — TESTNET simulation."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.models.order import OrderResult
from src.core.types.enums import ExecutionType, OrderRejectReason, OrderStatus
from src.exchange.base import BaseExchangeAdapter


class MockExchangeClient(BaseExchangeAdapter):
    def __init__(self, behavior: str = "fill_immediately"):
        self.behavior = behavior

    async def place_order(self, plan: ExecutionPlan) -> OrderResult:
        now = datetime.now(UTC)
        exec_id = uuid4()
        order_id = uuid4()

        base_result = {
            "execution_id": exec_id,
            "order_id": order_id,
            "execution_type": ExecutionType.LIVE,
            "side": plan.side,
            "symbol": "TESTNET:BTCUSDT",
            "requested_entry": plan.entry_price,
            "position_size": plan.position_size,
            "stop_loss": plan.stop_loss,
            "take_profit": plan.take_profit,
            "timestamp": now,
        }

        if self.behavior == "fill_immediately":
            return OrderResult(
                **base_result,
                status=OrderStatus.FILLED,
                reject_reason=OrderRejectReason.NONE,
                executed_entry=plan.entry_price,
            )
        elif self.behavior == "reject":
            return OrderResult(
                **base_result,
                status=OrderStatus.REJECTED,
                reject_reason=OrderRejectReason.UNKNOWN,
                executed_entry=None,
            )
        elif self.behavior == "partial_fill":
            return OrderResult(
                **base_result,
                status=OrderStatus.PARTIALLY_FILLED,
                reject_reason=OrderRejectReason.UNKNOWN,
                executed_entry=plan.entry_price,
            )
        elif self.behavior == "timeout":
            raise TimeoutError("Mock timeout")
        elif self.behavior == "network_error":
            raise ConnectionError("Mock network error")
        else:
            return OrderResult(
                **base_result,
                status=OrderStatus.FILLED,
                reject_reason=OrderRejectReason.NONE,
                executed_entry=plan.entry_price,
            )

    async def cancel_order(self, exchange_order_id: str) -> OrderResult:
        now = datetime.now(UTC)
        return OrderResult(
            execution_id=uuid4(),
            order_id=uuid4(),
            status=OrderStatus.CANCELLED,
            reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.LIVE,
            side=None,
            symbol="",
            requested_entry=0.0,
            executed_entry=None,
            position_size=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            timestamp=now,
        )

    async def get_order(self, exchange_order_id: str) -> OrderResult:
        now = datetime.now(UTC)
        return OrderResult(
            execution_id=uuid4(),
            order_id=uuid4(),
            status=OrderStatus.FILLED,
            reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.LIVE,
            side=None,
            symbol="",
            requested_entry=0.0,
            executed_entry=None,
            position_size=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            timestamp=now,
        )

    async def get_open_orders(self, symbol: str | None = None) -> list[OrderResult]:
        return []

    async def get_positions(self, symbol: str | None = None) -> list[dict]:
        return []

    async def get_balance(self) -> dict[str, float]:
        return {"USDT": 10000.0}