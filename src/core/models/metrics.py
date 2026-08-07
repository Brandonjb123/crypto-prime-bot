"""Runtime metrics model."""

from datetime import datetime
from pydantic import BaseModel


class RuntimeMetrics(BaseModel):
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    average_runtime_ms: float = 0.0
    last_error: str | None = None
    timestamp: datetime