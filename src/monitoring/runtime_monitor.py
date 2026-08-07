"""Runtime Monitor — gabungan Health + Metrics."""

from src.monitoring.health import HealthMonitor
from src.monitoring.metrics import MetricsCollector
from src.core.models.health import HealthSnapshot
from src.core.models.metrics import RuntimeMetrics
from src.core.types.enums import PipelineStatus


class RuntimeMonitor:
    def __init__(self) -> None:
        self.health = HealthMonitor()
        self.metrics = MetricsCollector()

    def record_pipeline_success(self, runtime_ms: float) -> None:
        self.health.record_pipeline_status(PipelineStatus.COMPLETED)
        self.metrics.record_success(runtime_ms)

    def record_pipeline_failure(self, error: str) -> None:
        self.health.record_pipeline_status(PipelineStatus.FAILED)
        self.health.record_error()
        self.metrics.record_failure(error)

    def get_health(self) -> HealthSnapshot:
        return self.health.get_health()

    def get_metrics(self) -> RuntimeMetrics:
        return self.metrics.snapshot()