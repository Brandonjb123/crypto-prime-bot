"""Integration test: PipelineRunner + BinanceCollector(mock) + IndicatorEngine."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.analysis.indicator_engine import IndicatorEngine
from src.core.models.analysis_result import AnalysisResult
from src.pipeline.pipeline_runner import PipelineRunner


class TestIndicatorPipeline:
    @patch("src.collectors.binance_collector.httpx.AsyncClient")
    async def test_full_pipeline_with_indicator(self, mock_client_class):
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

        collector = BinanceCollector()
        indicator = IndicatorEngine()
        runner = PipelineRunner(collector=collector, indicator_engine=indicator)

        result = await runner.run("BTC", "4h")
        assert result.status == "completed"
        assert isinstance(result, AnalysisResult)