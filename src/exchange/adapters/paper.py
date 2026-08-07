"""Paper Exchange Adapter — deterministic, no network."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.models.order import OrderResult
from src.core.types.enums import ExecutionStatus, OrderRejectReason, OrderStatus
from src.exchange.base import BaseExchangeAdapter


class PaperExchangeAdapter(BaseExchangeAdapter):
    async def place_order(self, plan: ExecutionPlan) -> OrderResult:
        if plan.status == ExecutionStatus.READY:
            return OrderResult(
                execution_id=plan.execution_id,
                order_id=uuid4(),
                status=OrderStatus.FILLED,
                reject_reason=OrderRejectReason.NONE,
                execution_type=plan.execution_type,
                side=plan.side,
                symbol="PAPER:BTC/USDT",
                requested_entry=plan.entry_price,
                executed_entry=plan.entry_price,
                position_size=plan.position_size,
                stop_loss=plan.stop_loss,
                take_profit=plan.take_profit,
                timestamp=datetime.now(UTC),
            )
        else:
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
