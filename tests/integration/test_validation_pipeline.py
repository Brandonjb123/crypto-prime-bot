"""Integration test: PipelineRunner + ValidationEngine."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.core.models.analysis_result import AnalysisResult as PipelineResult
from src.pipeline.pipeline_runner import PipelineRunner
from src.validation.validation_engine import ValidationEngine


class TestValidationPipeline:
    @patch("src.collectors.binance_collector.httpx.AsyncClient")
    async def test_full_pipeline_with_validation(self, mock_client_class):
        from src.ai.decision_engine import DecisionEngine
        from src.ai.prompt_builder import PromptBuilder
        from src.analysis.analysis_engine import AnalysisEngine
        from src.analysis.indicator_engine import IndicatorEngine
        from src.collectors.binance_collector import BinanceCollector

        # Mock collector
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_klines = []
        base = 50000.0
        for i in range(60):
            ts = 1700000000000 + i * 3600000 * 4
            open_p = base + i * 10
            high = open_p + 20
            low = open_p - 20
            close = open_p + 5
            vol = 100.0 + i
            mock_klines.append([ts, str(open_p), str(high), str(low), str(close), str(vol)])
        mock_price = {"price": "50500.0"}
        mock_client.get = AsyncMock(side_effect=[
            MagicMock(status_code=200, json=MagicMock(return_value=mock_klines)),
            MagicMock(status_code=200, json=MagicMock(return_value=mock_price)),
        ])
        mock_client_class.return_value = mock_client

        # Mock AI client
        ai_client = MagicMock()
        ai_client.complete = AsyncMock(return_value={
            "decision": "BUY",
            "confidence": 85,
            "risk_level": "MEDIUM",
            "reasoning": ["test"],
        })
        prompt_builder = PromptBuilder()

        collector = BinanceCollector()
        indicator = IndicatorEngine()
        analysis = AnalysisEngine()
        decision = DecisionEngine(client=ai_client, prompt_builder=prompt_builder)
        validation = ValidationEngine(confidence_threshold=70)

        runner = PipelineRunner(
            collector=collector,
            indicator_engine=indicator,
            analysis_engine=analysis,
            decision_engine=decision,
            validation_engine=validation,
        )

        result = await runner.run("BTC", "4h")
        assert result.status == "completed"
        assert isinstance(result, PipelineResult)