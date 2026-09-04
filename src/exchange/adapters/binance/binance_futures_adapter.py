"""Binance Futures Adapter — TESTNET ONLY."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.models.order import OrderResult
from src.core.types.enums import (
    ExchangeErrorType,
    ExecutionStatus,
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
)
from src.exchange.adapters.binance.exceptions import BinanceAPIError
from src.exchange.base import BaseExchangeAdapter


class BinanceFuturesAdapter(BaseExchangeAdapter):
    def __init__(self, client: Any) -> None:
        self.client = client

    def _map_status(self, exchange_status: str) -> OrderStatus:
        status_map = {
            "NEW": OrderStatus.NEW,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.FAILED,
        }
        return status_map.get(exchange_status, OrderStatus.UNKNOWN)

    async def place_order(self, plan: ExecutionPlan) -> OrderResult:
        now = datetime.now(UTC)

        if plan.status != ExecutionStatus.READY:
            return OrderResult(
                execution_id=plan.execution_id,
                order_id=uuid4(),
                status=OrderStatus.REJECTED,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=ExecutionType.LIVE,
                side=plan.side,
                symbol="TESTNET:BTCUSDT",
                requested_entry=plan.entry_price,
                executed_entry=None,
                position_size=0.0,
                stop_loss=plan.stop_loss,
                take_profit=plan.take_profit,
                timestamp=now,
                requested_quantity=plan.position_size,
                filled_quantity=0.0,
                remaining_quantity=plan.position_size,
            )

        try:
            response = await self.client.place_order(
                symbol="BTCUSDT",
                side=plan.side.value if plan.side else "BUY",
                quantity=plan.position_size,
                order_type="MARKET",
                client_order_id=getattr(plan, "client_order_id", None),
            )
        except BinanceAPIError as e:
            error_type = getattr(e, "error_type", None)
            if error_type == ExchangeErrorType.INSUFFICIENT_BALANCE:
                status = OrderStatus.REJECTED
                reject_reason = OrderRejectReason.INSUFFICIENT_BALANCE
            elif error_type in (ExchangeErrorType.INVALID_ORDER, ExchangeErrorType.AUTH_ERROR):
                status = OrderStatus.REJECTED
                reject_reason = OrderRejectReason.UNKNOWN
            else:
                status = OrderStatus.FAILED
                reject_reason = OrderRejectReason.UNKNOWN

            return OrderResult(
                execution_id=plan.execution_id,
                order_id=uuid4(),
                status=status,
                reject_reason=reject_reason,
                execution_type=ExecutionType.LIVE,
                side=plan.side,
                symbol="TESTNET:BTCUSDT",
                requested_entry=plan.entry_price,
                executed_entry=None,
                position_size=0.0,
                stop_loss=plan.stop_loss,
                take_profit=plan.take_profit,
                timestamp=now,
                requested_quantity=plan.position_size,
                filled_quantity=0.0,
                remaining_quantity=plan.position_size,
            )

        status = self._map_status(response.get("status", "UNKNOWN"))
        executed_price = float(response.get("avgPrice") or response.get("price") or plan.entry_price)
        executed_qty = float(response.get("executedQty", 0.0))
        requested_qty = float(response.get("origQty", plan.position_size))

        filled = executed_qty
        remaining = max(requested_qty - executed_qty, 0.0)

        return OrderResult(
            execution_id=plan.execution_id,
            order_id=uuid4(),
            status=status,
            reject_reason=OrderRejectReason.NONE if status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED) else OrderRejectReason.UNKNOWN,
            execution_type=ExecutionType.LIVE,
            side=plan.side,
            symbol=response.get("symbol", "TESTNET:BTCUSDT"),
            requested_entry=plan.entry_price,
            executed_entry=executed_price,
            position_size=filled,  # Quantity yang sebenarnya terisi
            stop_loss=plan.stop_loss,
            take_profit=plan.take_profit,
            timestamp=now,
            requested_quantity=requested_qty,
            filled_quantity=filled,
            remaining_quantity=remaining,
            average_fill_price=executed_price,
        )

    async def cancel_order(self, exchange_order_id: str) -> OrderResult:
        now = datetime.now(UTC)
        response = await self.client.cancel_order(order_id=exchange_order_id)
        status = self._map_status(response.get("status", "CANCELED"))
        return OrderResult(
            execution_id=uuid4(),
            order_id=uuid4(),
            status=status,
            reject_reason=OrderRejectReason.NONE,
            execution_type=ExecutionType.LIVE,
            side=None,
            symbol=str(response.get("symbol", "TESTNET:BTCUSDT")),
            requested_entry=0.0,
            executed_entry=None,
            position_size=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            timestamp=now,
        )

    async def get_order(self, exchange_order_id: str) -> OrderResult:
        now = datetime.now(UTC)
        response = await self.client.get_order(order_id=exchange_order_id)
        status = self._map_status(response.get("status", "UNKNOWN"))
        executed_qty = float(response.get("executedQty", 0.0))
        requested_qty = float(response.get("origQty", 0.0))
        executed_price = float(response.get("avgPrice") or 0.0)

        return OrderResult(
            execution_id=uuid4(),
            order_id=uuid4(),
            status=status,
            reject_reason=OrderRejectReason.NONE if status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED) else OrderRejectReason.UNKNOWN,
            execution_type=ExecutionType.LIVE,
            side=None,
            symbol=str(response.get("symbol", "TESTNET:BTCUSDT")),
            requested_entry=0.0,
            executed_entry=executed_price,
            position_size=executed_qty,
            stop_loss=0.0,
            take_profit=0.0,
            timestamp=now,
            requested_quantity=requested_qty,
            filled_quantity=executed_qty,
            remaining_quantity=max(requested_qty - executed_qty, 0.0),
            average_fill_price=executed_price,
        )

    async def get_open_orders(self, symbol: str | None = None) -> list[OrderResult]:
        now = datetime.now(UTC)
        response = await self.client.get_open_orders(symbol=symbol)
        results = []
        for item in response:
            status = self._map_status(item.get("status", "UNKNOWN"))
            executed_qty = float(item.get("executedQty", 0.0))
            requested_qty = float(item.get("origQty", 0.0))
            executed_price = float(item.get("avgPrice") or 0.0)
            results.append(
                OrderResult(
                    execution_id=uuid4(),
                    order_id=uuid4(),
                    status=status,
                    reject_reason=OrderRejectReason.NONE if status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED) else OrderRejectReason.UNKNOWN,
                    execution_type=ExecutionType.LIVE,
                    side=None,
                    symbol=str(item.get("symbol", "TESTNET:BTCUSDT")),
                    requested_entry=0.0,
                    executed_entry=executed_price,
                    position_size=executed_qty,
                    stop_loss=0.0,
                    take_profit=0.0,
                    timestamp=now,
                    requested_quantity=requested_qty,
                    filled_quantity=executed_qty,
                    remaining_quantity=max(requested_qty - executed_qty, 0.0),
                    average_fill_price=executed_price,
                )
            )
        return results

    async def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        return await self.client.get_positions(symbol=symbol)

    async def get_balance(self) -> dict[str, float]:
        return await self.client.get_balance()