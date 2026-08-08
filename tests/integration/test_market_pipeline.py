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
        indicator = MagicMock()
        indicator.calculate = MagicMock(return_value={})

        runner = PipelineRunner(collector=collector, indicator_engine=indicator)
        scheduler = SimpleScheduler(runner, interval_seconds=0.01)

        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()

        # Pipeline harus pernah dipanggil oleh scheduler
        assert collector.collect.called

    async def test_pipeline_runner_integration(self):
        collector = MagicMock()
        collector.collect = AsyncMock(return_value={"price": 45000})
        indicator = MagicMock()
        indicator.calculate = MagicMock(return_value={})

        runner = PipelineRunner(collector=collector, indicator_engine=indicator)
        result = await runner.run("ETH", "1h")

        assert isinstance(result, AnalysisResult)
        assert result.symbol == "ETH"
        assert result.timeframe == "1h"
        assert result.status == "completed"