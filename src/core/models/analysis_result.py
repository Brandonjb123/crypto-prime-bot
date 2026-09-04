"""Analysis result model — output dari satu siklus analisis."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel


class AnalysisResult(BaseModel):
    analysis_id: UUID = uuid4()
    symbol: str
    timeframe: str
    status: str  # "completed", "failed"
    error_message: str | None = None
    timestamp: datetime