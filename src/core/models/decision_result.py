"""Decision Result model — output dari AI Decision Engine."""

from datetime import datetime

from pydantic import BaseModel


class DecisionResult(BaseModel):
    symbol: str
    decision: str          # BUY / SELL / WAIT
    confidence: int        # 0–100
    risk_level: str        # LOW / MEDIUM / HIGH
    reasoning: list[str]
    model: str = "claude-haiku"
    timestamp: datetime