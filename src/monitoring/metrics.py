"""Metrics Collector — in-memory."""

from datetime import datetime, UTC
from src.core.models.metrics import RuntimeMetrics


class MetricsCollector:
    def __init__(self) -> None:
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self._runtimes: list[float] = []
        self.last_error: str | None = None

    def record_success(self, runtime_ms: float) -> None:
        self.total_runs += 1
        self.successful_runs += 1
        self._runtimes.append(runtime_ms)

    def record_failure(self, error: str) -> None:
        self.total_runs += 1
        self.failed_runs += 1
        self.last_error = error

    def snapshot(self) -> RuntimeMetrics:
        avg = sum(self._runtimes) / len(self._runtimes) if self._runtimes else 0.0
        return RuntimeMetrics(
            total_runs=self.total_runs,
            successful_runs=self.successful_runs,
            failed_runs=self.failed_runs,
            average_runtime_ms=round(avg, 2),
            last_error=self.last_error,
            timestamp=datetime.now(UTC),
        )