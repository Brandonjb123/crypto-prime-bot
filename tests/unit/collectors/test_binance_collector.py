"""Unit tests untuk BinanceCollector."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.collectors.binance_collector import BinanceCollector
from src.core.models.market_snapshot import MarketSnapshot


class TestBinanceCollector:
    @patch("src.collectors.binance_collector.httpx.AsyncClient")
    async def test_collect_returns_snapshot(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        # Mock klines response
        mock_klines = [
            [1700000000000, "50000", "51000", "49000", "50500", "100"],
            [1700003600000, "50500", "51500", "49500", "51000", "200"],
        ]
        mock_price = {"price": "51000.0"}
        mock_client.get = AsyncMock(side_effect=[
            MagicMock(status_code=200, json=MagicMock(return_value=mock_klines)),
            MagicMock(status_code=200, json=MagicMock(return_value=mock_price)),
        ])
        mock_client_class.return_value = mock_client

        collector = BinanceCollector()
        snapshot = await collector.collect("BTC", "4h")

        assert isinstance(snapshot, MarketSnapshot)
        assert snapshot.symbol == "BTC"
        assert snapshot.current_price == 51000.0
        assert len(snapshot.candles) == 2

    @patch("src.collectors.binance_collector.httpx.AsyncClient")
    async def test_retry_mechanism(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        # Gagal dua kali di klines, lalu sukses klines;
        # Sukses langsung di price
        mock_client.get = AsyncMock(side_effect=[
            Exception("timeout"),
            Exception("timeout"),
            MagicMock(status_code=200, json=MagicMock(return_value=[[1700000000000, "50000", "51000", "49000", "50500", "100"]])),
            MagicMock(status_code=200, json=MagicMock(return_value={"price": "50000.0"})),
        ])
        mock_client_class.return_value = mock_client

        collector = BinanceCollector()
        snapshot = await collector.collect("ETH", "1h")
        assert snapshot.current_price == 50000.0

    @patch("src.collectors.binance_collector.httpx.AsyncClient")
    async def test_all_retries_exhausted(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(side_effect=Exception("fail"))
        mock_client_class.return_value = mock_client

        collector = BinanceCollector()
        with pytest.raises(Exception, match="fail"):
            await collector.collect("BTC", "4h")