"""SignalLifecycle model — sidecar lifecycle state untuk TradingSignal.

Immutable. Append-once per signal_id. Bukan menggantikan TradingSignal,
bukan menyentuh Position.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.core.types.enums import (
    SignalLifecycleExpireReason,
    SignalLifecycleStatus,
)


class SignalLifecycle(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: UUID
    symbol: str
    status: SignalLifecycleStatus
    expire_reason: SignalLifecycleExpireReason | None = None
    created_at: datetime
    expires_at: datetime
    zone_low: float
    zone_high: float
    terminal_at: datetime | None = None
    superseded_by_signal_id: UUID | None = None