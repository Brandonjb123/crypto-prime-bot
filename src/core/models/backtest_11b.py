"""Backtest models for Sprint 11B — Backtesting Integration."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel


class EquityPoint(BaseModel):
    timestamp: datetime
    equity: float
    drawdown: float = 0.0
    drawdown_percent: float = 0.0

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
    side: str          # "BUY" or "SELL"
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    status: str
    entry_timestamp: datetime | None = None
    exit_timestamp: datetime | None = None
    gross_pnl: float = 0.0
    fees: float = 0.0
    net_pnl: float = 0.0
    signal_id: UUID | None = None
    execution_id: UUID | None = None
    stop_loss: float | None = None
    take_profit: float | None = None


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
    equity_curve: list[EquityPoint] = []
    total_fees: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0

