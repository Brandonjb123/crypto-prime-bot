"""Health Monitor."""

from datetime import datetime, UTC
import time
from src.core.models.health import HealthSnapshot
from src.core.types.enums import HealthStatus, PipelineStatus


class HealthMonitor:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.error_count = 0
        self.last_pipeline_status = PipelineStatus.IDLE

    def record_pipeline_status(self, status: PipelineStatus) -> None:
        self.last_pipeline_status = status

    def record_error(self) -> None:
        self.error_count += 1

    def get_health(self) -> HealthSnapshot:
        uptime = time.time() - self.start_time
        if self.error_count > 0:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return HealthSnapshot(
            status=status,
            timestamp=datetime.now(UTC),
            uptime_seconds=round(uptime, 2),
            last_pipeline_status=self.last_pipeline_status,
            error_count=self.error_count,
        )