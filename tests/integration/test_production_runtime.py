"""Integration test: Runtime lifecycle."""

import time

from src.core.types.enums import AuditEventType, HealthStatus
from src.logging.audit_logger import AuditLogger
from src.monitoring.runtime_monitor import RuntimeMonitor


class TestProductionRuntime:
    def test_full_runtime_lifecycle(self):
        monitor = RuntimeMonitor()
        audit = AuditLogger()

        # Simulate pipeline start
        audit.record(AuditEventType.PIPELINE_START, "BTCUSDT analysis started")

        # Simulate pipeline success
        start = time.time()
        time.sleep(0.01)
        runtime_ms = (time.time() - start) * 1000
        monitor.record_pipeline_success(runtime_ms)
        audit.record(AuditEventType.PIPELINE_COMPLETE, "BTCUSDT analysis completed")

        # Assert health
        health = monitor.get_health()
        assert health.status == HealthStatus.HEALTHY
        assert health.last_pipeline_status.value == "COMPLETED"

        # Assert metrics
        metrics = monitor.get_metrics()
        assert metrics.successful_runs == 1
        assert metrics.average_runtime_ms > 0

        # Assert audit
        records = audit.get_records()
        assert len(records) == 2
