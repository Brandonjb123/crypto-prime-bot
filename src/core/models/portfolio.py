"""Portfolio snapshot model — immutable."""

from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict
from src.core.types.enums import PortfolioStatus, RiskWarning


class PortfolioSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: UUID
    timestamp: datetime
    status: PortfolioStatus
    total_positions: int
    open_positions: int
    closed_positions: int
    long_positions: int
    short_positions: int
    net_exposure: float
    gross_exposure: float
    realized_pnl: float
    unrealized_pnl: float
    equity: float
    warnings: list[RiskWarning]