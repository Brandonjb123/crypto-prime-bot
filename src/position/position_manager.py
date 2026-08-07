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
from src.events.event_bus import EventBus
from src.events.events.position_closed import PositionClosedEvent
from src.events.events.position_opened import PositionOpenedEvent


class PositionManager:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._positions: dict[str, Position] = {}
        self.event_bus = event_bus

    def open_position(self, order: OrderResult) -> Position:
        if order.status != OrderStatus.FILLED:
            raise ValueError(f"Cannot open position from order status: {order.status}")

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

        if self.event_bus:
            self.event_bus.publish(
                PositionOpenedEvent(
                    position_id=position.position_id,
                    symbol=position.symbol,
                    side=position.side,
                    entry_price=position.entry_price,
                    position_size=position.position_size,
                )
            )

        return position

    def close_position(self, position_id: str, reason: PositionCloseReason) -> Position:
        pos = self._positions.get(position_id)
        if pos is None:
            raise ValueError(f"Position not found: {position_id}")
        if pos.status != PositionStatus.OPEN:
            raise PositionAlreadyClosedError(f"Position {position_id} already closed")

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

        if self.event_bus:
            self.event_bus.publish(
                PositionClosedEvent(
                    position_id=closed_pos.position_id,
                    reason=reason,
                    exit_price=None,
                )
            )

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
