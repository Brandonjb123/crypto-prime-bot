"""Binance Futures Testnet HTTP client — real implementation.

Hanya untuk TESTNET. Production endpoint tidak digunakan di modul ini.
"""

import asyncio
import hashlib
import hmac
import time
import urllib.parse
from typing import Any

import httpx

from config.constants import BINANCE_TESTNET_BASE_URL
from src.exchange.adapters.binance.exceptions import BinanceAPIError, ExchangeErrorType


class BinanceClient:
    MAX_GET_ATTEMPTS = 3
    RETRY_BACKOFF_SECONDS = 0.5

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = BINANCE_TESTNET_BASE_URL if testnet else "https://fapi.binance.com"

    def _sign(self, params: dict[str, Any]) -> str:
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _classify_error(self, status_code: int, message: str) -> BinanceAPIError:
        if status_code in (401, 403):
            error_type = ExchangeErrorType.AUTH_ERROR
        elif status_code >= 500:
            error_type = ExchangeErrorType.NETWORK_ERROR
        else:
            error_type = ExchangeErrorType.INVALID_ORDER
        return BinanceAPIError(message, error_type)

    async def _request(
        self,
        method: str,
        path: str,
        signed: bool = False,
        allow_retries: bool = False,
        **kwargs,
    ) -> dict | list:
        params = kwargs.pop("params", {})

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)

        headers = {"X-MBX-APIKEY": self.api_key}

        max_attempts = self.MAX_GET_ATTEMPTS if allow_retries else 1
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=10.0,
                ) as client:
                    response = await client.request(
                        method,
                        path,
                        params=params,
                        headers=headers,
                        **kwargs,
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                if allow_retries and attempt < max_attempts:
                    await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * (attempt - 1))
                    continue
                raise BinanceAPIError("Timeout", ExchangeErrorType.NETWORK_ERROR) from e

            except httpx.ConnectError as e:
                last_error = e
                if allow_retries and attempt < max_attempts:
                    await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * (attempt - 1))
                    continue
                raise BinanceAPIError("Connection error", ExchangeErrorType.NETWORK_ERROR) from e

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                message = f"HTTP {status_code}"
                if allow_retries and status_code >= 500 and attempt < max_attempts:
                    await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * (attempt - 1))
                    last_error = e
                    continue
                raise self._classify_error(status_code, message) from e

            except Exception as e:
                # Unknown error — jangan retry, jangan disembunyikan
                raise BinanceAPIError(str(e), ExchangeErrorType.UNKNOWN) from e

        # Jika sampai di sini berarti retry habis
        raise BinanceAPIError("Retries exhausted", ExchangeErrorType.NETWORK_ERROR) from last_error

    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float | None = None,
        order_type: str = "MARKET",
        client_order_id: str | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> dict:
        """Place TESTNET order. TIDAK ADA RETRY untuk POST."""
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }
        if price is not None:
            params["price"] = str(price)
        if client_order_id:
            params["newClientOrderId"] = client_order_id

        return await self._request(
            "POST",
            "/fapi/v1/order",
            signed=True,
            params=params,
        )

    async def cancel_order(self, order_id: str) -> dict:
        """Cancel TESTNET order. TIDAK ADA RETRY untuk DELETE."""
        return await self._request(
            "DELETE",
            "/fapi/v1/order",
            signed=True,
            params={"orderId": order_id},
        )

    async def get_order(self, order_id: str) -> dict:
        """Get TESTNET order by ID. GET retry diizinkan."""
        return await self._request(
            "GET",
            "/fapi/v1/order",
            signed=True,
            allow_retries=True,
            params={"orderId": order_id},
        )

    async def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        """Get open TESTNET orders. GET retry diizinkan."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._request(
            "GET",
            "/fapi/v1/openOrders",
            signed=True,
            allow_retries=True,
            params=params,
        )

    async def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get current TESTNET positions. GET retry diizinkan."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._request(
            "GET",
            "/fapi/v2/positionRisk",
            signed=True,
            allow_retries=True,
            params=params,
        )

    async def get_balance(self) -> dict[str, float]:
        """Get TESTNET account balance. GET retry diizinkan."""
        account = await self._request(
            "GET",
            "/fapi/v2/balance",
            signed=True,
            allow_retries=True,
        )
        result: dict[str, float] = {}
        for asset in account:
            result[asset["asset"]] = float(asset["balance"])
        return result