"""Integration test: Scheduler → PipelineRunner → AnalysisResult."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.application.scheduler import SimpleScheduler
from src.core.models.analysis_result import AnalysisResult
from src.pipeline.pipeline_runner import PipelineRunner


class TestMarketPipeline:
    async def test_scheduler_triggers_pipeline(self):
        collector = MagicMock()
        collector.collect = AsyncMock(return_value={"price": 50000})
        analysis = MagicMock()
        analysis.analyze = AsyncMock()

        runner = PipelineRunner(collector=collector, analysis_engine=analysis)
        scheduler = SimpleScheduler(runner, interval_seconds=0.01)

        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()

        # Pipeline harus pernah dipanggil oleh scheduler
        assert collector.collect.called

    async def test_pipeline_runner_integration(self):
        collector = MagicMock()
        collector.collect = AsyncMock(return_value={"price": 45000})
        analysis = MagicMock()
        analysis.analyze = AsyncMock()

        runner = PipelineRunner(collector=collector, analysis_engine=analysis)
        result = await runner.run("ETH", "1h")

        assert isinstance(result, AnalysisResult)
        assert result.symbol == "ETH"
        assert result.timeframe == "1h"
        assert result.status == "completed"