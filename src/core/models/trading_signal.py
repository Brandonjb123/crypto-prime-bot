"""Trading Signal model — output akhir pipeline analisis. Immutable."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TradingSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: UUID
    symbol: str
    side: str
    status: str
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    take_profit_1: float | None = None
    take_profit_2: float | None = None
    position_size: float = 0.0
    risk_percent: float = 0.0
    confidence: int = 0
    risk_level: str = "MEDIUM"
    reasoning: list[str] = []
    created_at: datetime