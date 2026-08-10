"""Portfolio state model — untuk Portfolio Engine (Sprint 10D)."""

from datetime import datetime

from pydantic import BaseModel


class PortfolioState(BaseModel):
    account_balance: float
    equity: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    open_positions: int = 0
    closed_positions: int = 0
    peak_equity: float
    drawdown: float = 0.0
    drawdown_percent: float = 0.0
    timestamp: datetime