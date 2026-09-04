"""Backtest models — HistoricalCandle, TradeRecord, BacktestResult."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.core.types.enums import BacktestStatus, Side, TradeOutcome


class HistoricalCandle(BaseModel):
    timestamp: datetime
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class TradeRecord(BaseModel):
    trade_id: UUID = uuid4()
    symbol: str
    side: Side
    entry_price: float
    exit_price: float | None = None
    position_size: float
    pnl: float = 0.0
    outcome: TradeOutcome = TradeOutcome.OPEN


class BacktestResult(BaseModel):
    backtest_id: UUID = uuid4()
    status: BacktestStatus
    symbol: str
    timeframe: str
    start_time: datetime
    end_time: datetime
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_profit: float = 0.0
    max_drawdown: float = 0.0
    final_equity: float = 0.0
    trades: list[TradeRecord] = []
    timestamp: datetime = None
