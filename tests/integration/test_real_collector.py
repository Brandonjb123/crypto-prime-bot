"""Integration test: PipelineRunner dengan collector (mock)."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.pipeline.pipeline_runner import PipelineRunner


class TestRealCollectorPipeline:
    @patch("src.collectors.binance_collector.httpx.AsyncClient")
    async def test_pipeline_with_binance_collector(self, mock_client_class):
        from src.collectors.binance_collector import BinanceCollector

        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_klines = [[1700000000000, "50000", "51000", "49000", "50500", "100"]]
        mock_price = {"price": "51000.0"}
        mock_client.get = AsyncMock(side_effect=[
            MagicMock(status_code=200, json=MagicMock(return_value=mock_klines)),
            MagicMock(status_code=200, json=MagicMock(return_value=mock_price)),
        ])
        mock_client_class.return_value = mock_client

        collector = BinanceCollector()
        runner = PipelineRunner(collector=collector, indicator_engine=MagicMock())
        result = await runner.run("BTC", "4h")
        assert result.status == "completed"