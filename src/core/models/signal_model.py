from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from src.core.types.enums import Side, Verdict, ConfidenceLevel


class SignalResult(BaseModel):
    """Signal individual dalam batch hasil deteksi."""
    symbol: str
    pair: str
    side: Side
    entry_price: float
    target_price: float
    stop_loss: float
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    risk_reward_ratio: Optional[float] = None
    verdict: Verdict = Verdict.SETUP_VALID
    summary: Optional[str] = None
    risk_notes: Optional[str] = None
    created_at: Optional[datetime] = None


class DetectionBatch(BaseModel):
    """Batch hasil signal detection."""
    signals: list[SignalResult]
    total_analyzed: int
    valid_signals: int
    timestamp: datetime = datetime.now(timezone.utc)