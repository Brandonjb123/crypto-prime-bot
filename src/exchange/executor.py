"""Order Executor — consume ExecutionPlan, return OrderResult."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.models.order import OrderResult
from src.core.types.enums import ExecutionStatus, OrderRejectReason, OrderStatus
from src.exchange.base import BaseExchangeAdapter


class OrderExecutor:
    def __init__(self, adapter: BaseExchangeAdapter) -> None:
        self.adapter = adapter

    async def execute(self, plan: ExecutionPlan) -> OrderResult:
        if plan.status != ExecutionStatus.READY:
            return OrderResult(
                execution_id=plan.execution_id,
                order_id=uuid4(),
                status=OrderStatus.REJECTED,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=plan.execution_type,
                side=plan.side,
                symbol="PAPER:BTC/USDT",
                requested_entry=plan.entry_price,
                executed_entry=None,
                position_size=plan.position_size,
                stop_loss=plan.stop_loss,
                take_profit=plan.take_profit,
                timestamp=datetime.now(UTC),
            )
        return await self.adapter.place_order(plan)