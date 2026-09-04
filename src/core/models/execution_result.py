"""Execution Result model — hasil dari paper/live execution."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ExecutionResult(BaseModel):
    execution_id: UUID
    signal_id: UUID
    symbol: str
    side: str          # BUY / SELL
    status: str        # FILLED / REJECTED / SKIPPED
    requested_price: float
    executed_price: float | None = None
    position_size: float = 0.0
    stop_loss: float | None = None
    take_profit: float | None = None
    slippage: float = 0.0
    timestamp: datetime