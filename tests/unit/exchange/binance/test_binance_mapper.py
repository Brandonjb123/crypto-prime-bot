"""Mapping antara domain model dan Binance response."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.order import OrderResult
from src.core.models.position import Position
from src.core.types.enums import (
    ExchangeOrderStatus,
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    PositionCloseReason,
    PositionStatus,
    Side,
)


def map_order_result(binance_order: dict, execution_id: str) -> OrderResult:
    """Map Binance order response → OrderResult."""
    status_map = {
        ExchangeOrderStatus.NEW: OrderStatus.PENDING,
        ExchangeOrderStatus.PARTIALLY_FILLED: OrderStatus.FILLED,
        ExchangeOrderStatus.FILLED: OrderStatus.FILLED,
        ExchangeOrderStatus.CANCELED: OrderStatus.REJECTED,
        ExchangeOrderStatus.REJECTED: OrderStatus.REJECTED,
        ExchangeOrderStatus.EXPIRED: OrderStatus.REJECTED,
    }
    binance_status = ExchangeOrderStatus(binance_order.get("status", "REJECTED"))
    order_status = status_map.get(binance_status, OrderStatus.REJECTED)

    executed_price = float(binance_order.get("avgPrice", 0)) or None

    return OrderResult(
        execution_id=execution_id,
        order_id=uuid4(),
        status=order_status,
        reject_reason=OrderRejectReason.NONE
        if order_status == OrderStatus.FILLED
        else OrderRejectReason.UNKNOWN,
        execution_type=ExecutionType.MARKET
        if binance_order.get("type") == "MARKET"
        else ExecutionType.LIMIT,
        side=Side.LONG if binance_order.get("side") == "BUY" else Side.SHORT,
        symbol=binance_order.get("symbol", ""),
        requested_entry=float(binance_order.get("price", 0))
        or float(binance_order.get("stopPrice", 0)),
        executed_entry=executed_price,
        position_size=float(binance_order.get("origQty", 0)),
        stop_loss=0.0,
        take_profit=0.0,
        timestamp=datetime.now(UTC),
    )


def map_position(binance_position: dict) -> Position | None:
    """Map Binance position response → Position."""
    amt = float(binance_position.get("positionAmt", 0))
    if amt == 0:
        return None

    entry_price = float(binance_position.get("entryPrice", 0))

    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol=binance_position.get("symbol", ""),
        side=Side.LONG if amt > 0 else Side.SHORT,
        status=PositionStatus.OPEN,
        entry_price=entry_price,
        stop_loss=0.0,
        take_profit=0.0,
        position_size=abs(amt),
        opened_at=datetime.now(UTC),
        closed_at=None,
        close_reason=PositionCloseReason.NONE,
        last_price=None,
        last_updated=None,
    )
