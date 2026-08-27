"""Trade Plan model — hasil perhitungan risk."""

from datetime import datetime

from pydantic import BaseModel


class TradePlan(BaseModel):
    symbol: str
    decision: str          # BUY / SELL / WAIT
    entry_price: float | None = None
    position_size: float = 0.0
    risk_percent: float = 0.0
    account_balance: float = 0.0
    stop_loss: float | None = None
    take_profit: float | None = None
    take_profit_1: float | None = None
    take_profit_2: float | None = None
    risk_reward_ratio: float = 0.0
    estimated_loss: float = 0.0
    estimated_profit: float = 0.0
    atr_stop_loss: float | None = None
    atr_take_profit: float | None = None
    timestamp: datetime