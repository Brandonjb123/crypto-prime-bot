"""Binance Futures Adapter — implementasi BaseExchangeAdapter."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.execution import ExecutionPlan
from src.core.models.order import OrderResult
from src.core.types.enums import (
    ExchangeErrorType,
    ExecutionStatus,
    OrderRejectReason,
    OrderStatus,
)
from src.exchange.adapters.binance.binance_mapper import map_order_result
from src.exchange.adapters.binance.client import BinanceClient
from src.exchange.adapters.binance.exceptions import BinanceAPIError
from src.exchange.base import BaseExchangeAdapter


class BinanceFuturesAdapter(BaseExchangeAdapter):
    def __init__(self, client: BinanceClient) -> None:
        self.client = client

    async def place_order(self, execution_plan: ExecutionPlan) -> OrderResult:
        if execution_plan.status != ExecutionStatus.READY:
            return OrderResult(
                execution_id=execution_plan.execution_id,
                order_id=uuid4(),
                status=OrderStatus.REJECTED,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=execution_plan.execution_type,
                side=execution_plan.side,
                symbol=execution_plan.side.value + "_" + execution_plan.side.value if execution_plan.side else "",
                requested_entry=execution_plan.entry_price,
                executed_entry=None,
                position_size=execution_plan.position_size,
                stop_loss=execution_plan.stop_loss,
                take_profit=execution_plan.take_profit,
                timestamp=datetime.now(UTC),
            )

        try:
            side = "BUY" if execution_plan.side and execution_plan.side.value == "LONG" else "SELL"
            response = await self.client.place_order(
                symbol="BTCUSDT",
                side=side,
                quantity=execution_plan.position_size,
            )
            return map_order_result(response, execution_plan.execution_id)
        except BinanceAPIError as e:
            return OrderResult(
                execution_id=execution_plan.execution_id,
                order_id=uuid4(),
                status=OrderStatus.REJECTED,
                reject_reason=self._map_error_to_reject_reason(e.error_type),
                execution_type=execution_plan.execution_type,
                side=execution_plan.side,
                symbol="",
                requested_entry=execution_plan.entry_price,
                executed_entry=None,
                position_size=execution_plan.position_size,
                stop_loss=execution_plan.stop_loss,
                take_profit=execution_plan.take_profit,
                timestamp=datetime.now(UTC),
            )
        except Exception:
            return OrderResult(
                execution_id=execution_plan.execution_id,
                order_id=uuid4(),
                status=OrderStatus.REJECTED,
                reject_reason=OrderRejectReason.UNKNOWN,
                execution_type=execution_plan.execution_type,
                side=execution_plan.side,
                symbol="",
                requested_entry=execution_plan.entry_price,
                executed_entry=None,
                position_size=execution_plan.position_size,
                stop_loss=execution_plan.stop_loss,
                take_profit=execution_plan.take_profit,
                timestamp=datetime.now(UTC),
            )

    def _map_error_to_reject_reason(self, error_type: ExchangeErrorType) -> OrderRejectReason:
        mapping = {
            ExchangeErrorType.INSUFFICIENT_BALANCE: OrderRejectReason.INSUFFICIENT_BALANCE,
            ExchangeErrorType.INVALID_ORDER: OrderRejectReason.INVALID_PRICE,
            ExchangeErrorType.NETWORK_ERROR: OrderRejectReason.UNKNOWN,
            ExchangeErrorType.AUTH_ERROR: OrderRejectReason.UNKNOWN,
            ExchangeErrorType.RATE_LIMIT: OrderRejectReason.UNKNOWN,
            ExchangeErrorType.UNKNOWN: OrderRejectReason.UNKNOWN,
        }
        return mapping.get(error_type, OrderRejectReason.UNKNOWN)