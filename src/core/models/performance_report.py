"""Performance Report model — hasil analisis performa."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel


class PerformanceReport(BaseModel):
    report_id: UUID = uuid4()
    initial_balance: float
    final_balance: float
    net_profit: float
    total_return_percent: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    average_win: float
    average_loss: float
    profit_factor: float | None  # None jika tidak terdefinisi (tidak ada loss)
    expectancy: float
    max_drawdown: float
    max_drawdown_percent: float
    long_trades: int = 0
    short_trades: int = 0
    long_wins: int = 0
    short_wins: int = 0
    long_win_rate: float = 0.0
    short_win_rate: float = 0.0
    timestamp: datetime