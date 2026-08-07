"""Health snapshot model."""

from datetime import datetime
from pydantic import BaseModel
from src.core.types.enums import HealthStatus, PipelineStatus


class HealthSnapshot(BaseModel):
    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    last_pipeline_status: PipelineStatus
    error_count: int