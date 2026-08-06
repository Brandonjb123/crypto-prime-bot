"""Exchange account snapshot model — immutable."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExchangeAccountSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    asset: str
    wallet_balance: float
    available_balance: float
    unrealized_pnl: float
    timestamp: datetime