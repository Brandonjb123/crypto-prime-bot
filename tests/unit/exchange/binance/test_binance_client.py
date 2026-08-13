"""Unit tests untuk BinanceClient HTTP methods dan GET retry."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.exchange.adapters.binance.client import BinanceClient
from src.exchange.adapters.binance.exceptions import BinanceAPIError


@pytest.fixture
def client():
    return BinanceClient(api_key="testkey", api_secret="testsecret", testnet=True)


class TestBinanceClient:
    def test_signature_deterministic(self, client):
        params = {"symbol": "BTCUSDT", "side": "BUY", "timestamp": 123456789}
        sig1 = client._sign(params)
        sig2 = client._sign(params)
        assert sig1 == sig2

    @pytest.mark.asyncio
    async def test_place_order_calls_http_no_retry(self, client):
        fake_response = MagicMock()
        fake_response.json.return_value = {"orderId": "1", "status": "FILLED"}
        fake_response.raise_for_status = MagicMock()

        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
        ) as mock_req:
            mock_req.return_value = fake_response
            result = await client.place_order(
                symbol="BTCUSDT", side="BUY", quantity=0.1, order_type="MARKET"
            )
            assert result["status"] == "FILLED"
            assert mock_req.call_count == 1  # Tidak ada retry untuk POST

    @pytest.mark.asyncio
    async def test_get_balance_retries_on_connect_error(self, client):
        fake_response = MagicMock()
        fake_response.json.return_value = [{"asset": "USDT", "balance": "100.0"}]
        fake_response.raise_for_status = MagicMock()

        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
        ) as mock_req:
            mock_req.side_effect = [
                httpx.ConnectError("connection failed 1"),
                httpx.ConnectError("connection failed 2"),
                fake_response,
            ]
            result = await client.get_balance()
            assert result == {"USDT": 100.0}
            assert mock_req.call_count == 3

    @pytest.mark.asyncio
    async def test_get_order_retries_on_5xx(self, client):
        fake_response = MagicMock()
        fake_response.json.return_value = {"orderId": "1", "status": "FILLED"}
        fake_response.raise_for_status = MagicMock()

        resp_500 = MagicMock()
        resp_500.status_code = 500
        resp_500.raise_for_status.side_effect = httpx.HTTPStatusError(
            "server error",
            request=MagicMock(),
            response=resp_500,
        )

        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
        ) as mock_req:
            mock_req.side_effect = [
                httpx.HTTPStatusError("server error", request=MagicMock(), response=resp_500),
                httpx.HTTPStatusError("server error", request=MagicMock(), response=resp_500),
                fake_response,
            ]
            result = await client.get_order("1")
            assert result["status"] == "FILLED"
            assert mock_req.call_count == 3

    @pytest.mark.asyncio
    async def test_get_order_does_not_retry_on_4xx(self, client):
        resp_400 = MagicMock()
        resp_400.status_code = 400

        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
        ) as mock_req:
            mock_req.side_effect = httpx.HTTPStatusError(
                "bad request",
                request=MagicMock(),
                response=resp_400,
            )
            with pytest.raises(BinanceAPIError):
                await client.get_order("1")
            assert mock_req.call_count == 1  # Tidak retry 4xx