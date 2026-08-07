from src.monitoring.metrics import MetricsCollector


class TestMetricsCollector:
    def test_record_success(self):
        mc = MetricsCollector()
        mc.record_success(100.0)
        snap = mc.snapshot()
        assert snap.total_runs == 1
        assert snap.successful_runs == 1
        assert snap.failed_runs == 0

    def test_record_failure(self):
        mc = MetricsCollector()
        mc.record_failure("test error")
        snap = mc.snapshot()
        assert snap.failed_runs == 1
        assert snap.last_error == "test error"

    def test_average_runtime(self):
        mc = MetricsCollector()
        mc.record_success(100.0)
        mc.record_success(200.0)
        snap = mc.snapshot()
        assert snap.average_runtime_ms == 150.0

    def test_multiple_runs(self):
        mc = MetricsCollector()
        mc.record_success(50.0)
        mc.record_failure("err")
        mc.record_success(30.0)
        snap = mc.snapshot()
        assert snap.total_runs == 3
        assert snap.successful_runs == 2

    def test_empty_snapshot(self):
        mc = MetricsCollector()
        snap = mc.snapshot()
        assert snap.total_runs == 0
        assert snap.average_runtime_ms == 0.0

    def test_last_error_updated(self):
        mc = MetricsCollector()
        mc.record_failure("first")
        mc.record_failure("second")
        snap = mc.snapshot()
        assert snap.last_error == "second"
