"""Trade Lifecycle Engine — evaluasi TP/SL untuk posisi OPEN."""

from datetime import UTC, datetime

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side


class TradeLifecycleEngine:
    """Evaluasi apakah posisi OPEN kena Stop Loss atau Take Profit."""

    def evaluate(self, position: Position, current_price: float) -> Position:
        """
        Evaluasi posisi terhadap harga saat ini.
        Return Position baru (immutable).
        """
        # Closed positions tidak berubah
        if position.status != PositionStatus.OPEN:
            return Position(
                position_id=position.position_id,
                execution_id=position.execution_id,
                order_id=position.order_id,
                symbol=position.symbol,
                side=position.side,
                status=position.status,
                entry_price=position.entry_price,
                stop_loss=position.stop_loss,
                take_profit=position.take_profit,
                position_size=position.position_size,
                opened_at=position.opened_at,
                closed_at=position.closed_at,
                close_reason=position.close_reason,
                last_price=current_price,
                last_updated=datetime.now(UTC),
            )

        if position.side == Side.LONG:
            if current_price <= position.stop_loss:
                return Position(
                    position_id=position.position_id,
                    execution_id=position.execution_id,
                    order_id=position.order_id,
                    symbol=position.symbol,
                    side=position.side,
                    status=PositionStatus.STOPPED,
                    entry_price=position.entry_price,
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                    position_size=position.position_size,
                    opened_at=position.opened_at,
                    closed_at=datetime.now(UTC),
                    close_reason=PositionCloseReason.STOP_LOSS,
                    last_price=current_price,
                    last_updated=datetime.now(UTC),
                )
            elif current_price >= position.take_profit:
                return Position(
                    position_id=position.position_id,
                    execution_id=position.execution_id,
                    order_id=position.order_id,
                    symbol=position.symbol,
                    side=position.side,
                    status=PositionStatus.TAKE_PROFIT,
                    entry_price=position.entry_price,
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                    position_size=position.position_size,
                    opened_at=position.opened_at,
                    closed_at=datetime.now(UTC),
                    close_reason=PositionCloseReason.TAKE_PROFIT,
                    last_price=current_price,
                    last_updated=datetime.now(UTC),
                )
        else:  # SHORT
            if current_price >= position.stop_loss:
                return Position(
                    position_id=position.position_id,
                    execution_id=position.execution_id,
                    order_id=position.order_id,
                    symbol=position.symbol,
                    side=position.side,
                    status=PositionStatus.STOPPED,
                    entry_price=position.entry_price,
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                    position_size=position.position_size,
                    opened_at=position.opened_at,
                    closed_at=datetime.now(UTC),
                    close_reason=PositionCloseReason.STOP_LOSS,
                    last_price=current_price,
                    last_updated=datetime.now(UTC),
                )
            elif current_price <= position.take_profit:
                return Position(
                    position_id=position.position_id,
                    execution_id=position.execution_id,
                    order_id=position.order_id,
                    symbol=position.symbol,
                    side=position.side,
                    status=PositionStatus.TAKE_PROFIT,
                    entry_price=position.entry_price,
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                    position_size=position.position_size,
                    opened_at=position.opened_at,
                    closed_at=datetime.now(UTC),
                    close_reason=PositionCloseReason.TAKE_PROFIT,
                    last_price=current_price,
                    last_updated=datetime.now(UTC),
                )

        # HOLD — tetap OPEN, update last_price
        return Position(
            position_id=position.position_id,
            execution_id=position.execution_id,
            order_id=position.order_id,
            symbol=position.symbol,
            side=position.side,
            status=PositionStatus.OPEN,
            entry_price=position.entry_price,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            position_size=position.position_size,
            opened_at=position.opened_at,
            closed_at=None,
            close_reason=PositionCloseReason.NONE,
            last_price=current_price,
            last_updated=datetime.now(UTC),
        )
