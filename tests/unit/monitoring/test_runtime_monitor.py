from src.core.types.enums import PipelineStatus, HealthStatus
from src.monitoring.runtime_monitor import RuntimeMonitor


class TestRuntimeMonitor:
    def test_record_success(self):
        rm = RuntimeMonitor()
        rm.record_pipeline_success(150.0)
        assert rm.get_health().status == HealthStatus.HEALTHY
        assert rm.get_metrics().successful_runs == 1

    def test_record_failure(self):
        rm = RuntimeMonitor()
        rm.record_pipeline_failure("timeout")
        snap = rm.get_health()
        assert snap.status == HealthStatus.DEGRADED
        assert snap.error_count == 1

    def test_get_metrics(self):
        rm = RuntimeMonitor()
        rm.record_pipeline_success(100.0)
        rm.record_pipeline_success(200.0)
        metrics = rm.get_metrics()
        assert metrics.total_runs == 2

    def test_get_health(self):
        rm = RuntimeMonitor()
        health = rm.get_health()
        assert health.status == HealthStatus.HEALTHY