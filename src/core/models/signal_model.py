from datetime import UTC, datetime

from pydantic import BaseModel

from src.core.types.enums import ConfidenceLevel, Side, Verdict


class SignalResult(BaseModel):
    """Signal individual dalam batch hasil deteksi."""

    symbol: str
    pair: str
    side: Side
    entry_price: float
    target_price: float
    stop_loss: float
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    risk_reward_ratio: float | None = None
    verdict: Verdict = Verdict.SETUP_VALID
    summary: str | None = None
    risk_notes: str | None = None
    created_at: datetime | None = None


class DetectionBatch(BaseModel):
    """Batch hasil signal detection."""

    signals: list[SignalResult]
    total_analyzed: int
    valid_signals: int
    timestamp: datetime = datetime.now(UTC)
