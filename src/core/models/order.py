"""Order result model — immutable."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.core.types.enums import ExecutionType, OrderRejectReason, OrderStatus, Side


class OrderResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: UUID
    order_id: UUID
    status: OrderStatus
    reject_reason: OrderRejectReason
    execution_type: ExecutionType
    side: Side | None
    symbol: str
    requested_entry: float
    executed_entry: float | None
    position_size: float
    stop_loss: float
    take_profit: float
    timestamp: datetime