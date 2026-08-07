import time
from src.core.types.enums import HealthStatus, PipelineStatus
from src.monitoring.health import HealthMonitor


class TestHealthMonitor:
    def test_initial_healthy(self):
        hm = HealthMonitor()
        snap = hm.get_health()
        assert snap.status == HealthStatus.HEALTHY
        assert snap.error_count == 0

    def test_degraded_after_error(self):
        hm = HealthMonitor()
        hm.record_error()
        snap = hm.get_health()
        assert snap.status == HealthStatus.DEGRADED

    def test_pipeline_status_recorded(self):
        hm = HealthMonitor()
        hm.record_pipeline_status(PipelineStatus.COMPLETED)
        snap = hm.get_health()
        assert snap.last_pipeline_status == PipelineStatus.COMPLETED

    def test_uptime_positive(self):
        hm = HealthMonitor()
        time.sleep(0.01)
        snap = hm.get_health()
        assert snap.uptime_seconds > 0

    def test_error_count_increments(self):
        hm = HealthMonitor()
        hm.record_error()
        hm.record_error()
        snap = hm.get_health()
        assert snap.error_count == 2