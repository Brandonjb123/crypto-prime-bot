"""Integration test: Pipeline failure → Metrics + Health DEGRADED."""

from src.monitoring.runtime_monitor import RuntimeMonitor
from src.logging.audit_logger import AuditLogger
from src.core.types.enums import AuditEventType, HealthStatus


class TestPipelineFailureMonitoring:
    def test_failure_flow(self):
        monitor = RuntimeMonitor()
        audit = AuditLogger()

        audit.record(AuditEventType.PIPELINE_START, "BTCUSDT")
        monitor.record_pipeline_failure("connection timeout")
        audit.record(AuditEventType.PIPELINE_FAILED, "connection timeout")

        health = monitor.get_health()
        assert health.status == HealthStatus.DEGRADED
        assert health.error_count == 1

        metrics = monitor.get_metrics()
        assert metrics.failed_runs == 1
        assert metrics.last_error == "connection timeout"

        records = audit.get_records()
        assert len(records) == 2