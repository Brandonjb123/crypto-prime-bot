"""Position Manager — mengelola lifecycle posisi in-memory."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.exceptions.collector_exceptions import (
    DuplicatePositionError,
    PositionAlreadyClosedError,
)
from src.core.models.order import OrderResult
from src.core.models.position import Position
from src.core.types.enums import OrderStatus, PositionCloseReason, PositionStatus


class PositionManager:
    def __init__(self) -> None:
        self._positions: dict[str, Position] = {}  # key = position_id (str)

    def open_position(self, order: OrderResult) -> Position:
        # Rule 1: Hanya FILLED yang bisa buka posisi
        if order.status != OrderStatus.FILLED:
            raise ValueError(f"Cannot open position from order status: {order.status}")

        # Rule 3: 1 symbol = 1 open position (LONG atau SHORT)
        for pos in self._positions.values():
            if pos.symbol == order.symbol and pos.status == PositionStatus.OPEN:
                raise DuplicatePositionError(
                    f"Position already open for {order.symbol} ({pos.side.value})"
                )

        position = Position(
            position_id=uuid4(),
            execution_id=order.execution_id,
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            status=PositionStatus.OPEN,
            entry_price=order.requested_entry,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            position_size=order.position_size,
            opened_at=datetime.now(UTC),
            closed_at=None,
            close_reason=PositionCloseReason.NONE,
        )
        self._positions[str(position.position_id)] = position
        return position

    def close_position(self, position_id: str, reason: PositionCloseReason) -> Position:
        pos = self._positions.get(position_id)
        if pos is None:
            raise ValueError(f"Position not found: {position_id}")
        if pos.status != PositionStatus.OPEN:
            raise PositionAlreadyClosedError(f"Position {position_id} already closed")

        # Buat object baru (immutable)
        closed_pos = Position(
            position_id=pos.position_id,
            execution_id=pos.execution_id,
            order_id=pos.order_id,
            symbol=pos.symbol,
            side=pos.side,
            status=PositionStatus.CLOSED,
            entry_price=pos.entry_price,
            stop_loss=pos.stop_loss,
            take_profit=pos.take_profit,
            position_size=pos.position_size,
            opened_at=pos.opened_at,
            closed_at=datetime.now(UTC),
            close_reason=reason,
        )
        self._positions[str(position_id)] = closed_pos
        return closed_pos

    def has_open_position(self, symbol: str, side: str | None = None) -> bool:
        for pos in self._positions.values():
            if pos.symbol == symbol and pos.status == PositionStatus.OPEN:
                if side is None or pos.side.value == side:
                    return True
        return False

    def get_position(self, position_id: str) -> Position | None:
        return self._positions.get(position_id)

    def get_open_positions(self) -> list[Position]:
        return [p for p in self._positions.values() if p.status == PositionStatus.OPEN]

    def get_all_positions(self) -> list[Position]:
        return list(self._positions.values())