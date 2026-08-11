"""Backtest models for Sprint 11B — Backtesting Integration."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel


class BacktestConfig(BaseModel):
    symbol: str = "BTC"
    timeframe: str = "4h"
    initial_balance: float = 10000.0
    start_time: datetime | None = None
    end_time: datetime | None = None
    slippage: float = 0.0


class TradeRecord(BaseModel):
    trade_id: UUID = uuid4()
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    status: str  # WIN, LOSS, BREAKEVEN


class BacktestResult(BaseModel):
    backtest_id: UUID = uuid4()
    config: BacktestConfig
    initial_balance: float
    final_balance: float
    total_pnl: float
    total_return_percent: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    max_drawdown_percent: float
    open_positions: int
    closed_positions: int
    trades: list[TradeRecord] = []
    start_time: datetime
    end_time: datetime