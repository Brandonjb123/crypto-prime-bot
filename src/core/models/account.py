"""Account snapshot model — immutable."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AccountSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    balance: float
    equity: float
    margin_used: float
    free_margin: float
    timestamp: datetime