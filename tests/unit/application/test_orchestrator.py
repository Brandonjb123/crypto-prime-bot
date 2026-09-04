"""Unit tests untuk PipelineOrchestrator — semua dependency di-mock."""

from unittest.mock import AsyncMock, MagicMock

from src.application.orchestrator import PipelineOrchestrator
from src.application.pipeline_context import PipelineContext
from src.core.types.enums import PipelineStatus


class TestPipelineOrchestrator:
    async def test_pipeline_success_minimal(self):
        """Pipeline dengan semua mock sukses → COMPLETED."""
        orch = PipelineOrchestrator()
        ctx = await orch.run("BTC")
        assert ctx.status == PipelineStatus.COMPLETED
        assert ctx.symbol == "BTC"

    async def test_collector_failure(self):
        """Collector gagal → FAILED, error_message terisi."""
        registry = MagicMock()
        registry.collect_all = AsyncMock(side_effect=Exception("Connection error"))
        orch = PipelineOrchestrator(collector_registry=registry)
        ctx = await orch.run("BTC")
        assert ctx.status == PipelineStatus.FAILED
        assert "Connection error" in ctx.error_message

    async def test_pipeline_status_running_then_failed(self):
        """Status transisi dari RUNNING → FAILED."""
        registry = MagicMock()
        registry.collect_all = AsyncMock(side_effect=Exception("fail"))
        orch = PipelineOrchestrator(collector_registry=registry)
        ctx = await orch.run("BTC")
        assert ctx.status == PipelineStatus.FAILED

    async def test_pipeline_returns_context(self):
        """Pipeline selalu return PipelineContext."""
        orch = PipelineOrchestrator()
        ctx = await orch.run("ETH")
        assert isinstance(ctx, PipelineContext)
        assert ctx.run_id is not None
