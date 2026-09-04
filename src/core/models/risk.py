"""Risk Engine result model."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import RiskWarning, Side


class RiskResult(BaseModel):
    entry_price: float
    stop_loss: float
    stop_distance: float
    take_profit: float
    take_profit_distance: float
    position_size: float
    risk_amount: float
    expected_profit: float
    expected_loss: float
    risk_reward_ratio: float
    max_loss_pct: float
    direction: Side
    risk_model: str
    warnings: list[RiskWarning] = []
    timestamp: datetime
