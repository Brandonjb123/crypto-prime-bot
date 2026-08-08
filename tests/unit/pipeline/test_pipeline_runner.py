"""Unit tests untuk PipelineRunner."""

from unittest.mock import AsyncMock, MagicMock

from src.core.models.analysis_result import AnalysisResult
from src.pipeline.pipeline_runner import PipelineRunner


class TestPipelineRunner:
    async def test_run_success(self):
        collector = MagicMock()
        collector.collect = AsyncMock(return_value={"price": 50000})
        analysis = MagicMock()
        analysis.analyze = AsyncMock()

        runner = PipelineRunner(collector=collector, analysis_engine=analysis)
        result = await runner.run("BTC")

        assert isinstance(result, AnalysisResult)
        assert result.status == "completed"
        assert result.symbol == "BTC"

    async def test_collector_failure_does_not_crash(self):
        collector = MagicMock()
        collector.collect = AsyncMock(side_effect=Exception("API down"))
        analysis = MagicMock()

        runner = PipelineRunner(collector=collector, analysis_engine=analysis)
        result = await runner.run("ETH")

        assert result.status == "failed"
        assert "API down" in result.error_message

    async def test_analysis_failure_does_not_crash(self):
        collector = MagicMock()
        collector.collect = AsyncMock(return_value={"price": 50000})
        analysis = MagicMock()
        analysis.analyze = AsyncMock(side_effect=Exception("Analysis error"))

        runner = PipelineRunner(collector=collector, analysis_engine=analysis)
        result = await runner.run("BTC")

        assert result.status == "failed"
        assert "Analysis error" in result.error_message

    async def test_no_collector_still_completes(self):
        runner = PipelineRunner(collector=None, analysis_engine=AsyncMock())
        result = await runner.run("BTC")
        assert result.status == "completed"

    async def test_deterministic(self):
        collector = MagicMock()
        collector.collect = AsyncMock(return_value={"price": 50000})
        analysis = MagicMock()
        analysis.analyze = AsyncMock()

        runner = PipelineRunner(collector=collector, analysis_engine=analysis)
        r1 = await runner.run("BTC")
        r2 = await runner.run("BTC")
        assert r1.status == r2.status