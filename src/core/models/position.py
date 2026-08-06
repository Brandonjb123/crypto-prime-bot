"""Position model — immutable."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.core.types.enums import PositionCloseReason, PositionStatus, Side


class Position(BaseModel):
    model_config = ConfigDict(frozen=True)

    position_id: UUID
    execution_id: UUID
    order_id: UUID
    symbol: str
    side: Side
    status: PositionStatus
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    opened_at: datetime
    closed_at: datetime | None
    close_reason: PositionCloseReason