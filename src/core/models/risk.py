"""Risk Engine result model."""

from datetime import datetime

from pydantic import BaseModel

from src.core.types.enums import Side


class RiskResult(BaseModel):
    """Output dari Risk Engine."""

    position_size: float
    risk_amount: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    max_loss_pct: float
    direction: Side
    risk_model: str  # "trend" | "breakout" | "reversal"
    timestamp: datetime