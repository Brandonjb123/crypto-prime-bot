"""Health Monitor."""

import time
from datetime import UTC, datetime

from src.core.models.health import HealthSnapshot
from src.core.types.enums import HealthStatus, PipelineStatus


class HealthMonitor:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.error_count = 0
        self.last_pipeline_status = PipelineStatus.IDLE
        self.last_success_time: datetime | None = None

    def record_pipeline_status(self, status: PipelineStatus) -> None:
        self.last_pipeline_status = status
        if status == PipelineStatus.COMPLETED:
            self.last_success_time = datetime.now(UTC)

    def record_error(self) -> None:
        self.error_count += 1

    def get_health(self) -> HealthSnapshot:
        uptime = time.time() - self.start_time
        now = datetime.now(UTC)

        # HEALTHY: error count 0 AND pipeline has succeeded within last 30 minutes
        if self.error_count == 0 and self.last_success_time:
            seconds_since_success = (now - self.last_success_time).total_seconds()
            if seconds_since_success < 1800:  # 30 menit
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.DEGRADED  # belum ada success baru-baru ini
        elif self.error_count > 0:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return HealthSnapshot(
            status=status,
            timestamp=now,
            uptime_seconds=round(uptime, 2),
            last_pipeline_status=self.last_pipeline_status,
            last_success_time=self.last_success_time,
            error_count=self.error_count,
        )
