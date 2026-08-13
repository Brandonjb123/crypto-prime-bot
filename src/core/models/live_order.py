"""Live order tracking model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.core.types.enums import OrderStatus, Side


class LiveOrder(BaseModel):
    execution_id: UUID
    signal_id: UUID
    client_order_id: str
    exchange_order_id: str | None = None
    symbol: str
    side: Side
    quantity: float
    requested_price: float
    average_fill_price: float = 0.0
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    status: OrderStatus = OrderStatus.NEW
    created_at: datetime
    updated_at: datetime