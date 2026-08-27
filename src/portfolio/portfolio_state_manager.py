"""Portfolio State Manager — mengelola state portfolio."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.core.models.portfolio_state import PortfolioState
from src.core.models.position import Position
from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.logging.logger import get_logger
from src.market.pnl_engine import calculate_unrealized
from src.storage.adapters.in_memory_position_repository import InMemoryPositionRepository

logger = get_logger("portfolio_state_manager")


class PortfolioStateManager:
    def __init__(
        self,
        initial_balance: float,
        position_repository: InMemoryPositionRepository | None = None,
        price_provider=None,
    ):
        self.initial_balance = initial_balance
        self.repo = position_repository or InMemoryPositionRepository()
        self.price_provider = price_provider
        self.realized_pnl = 0.0
        self.peak_equity = initial_balance
        self._used_signal_ids: set[str] = set()

    def open_position(self, signal: TradingSignal) -> Position | None:
        if signal.status != "ACTIVE":
            logger.info(f"Signal {signal.signal_id} is not ACTIVE, skipping")
            return None

        if str(signal.signal_id) in self._used_signal_ids:
            logger.warning(f"Position for signal {signal.signal_id} already exists")
            return None

        logger.info(f"Opening position for {signal.symbol} {signal.side}")

        position = Position(
            position_id=uuid4(),
            execution_id=uuid4(),
            order_id=uuid4(),
            symbol=signal.symbol,
            side=Side.LONG if signal.side == "BUY" else Side.SHORT,
            status=PositionStatus.OPEN,
            entry_price=signal.entry_price or 0.0,
            stop_loss=signal.stop_loss or 0.0,
            take_profit=signal.take_profit or 0.0,
            tp1_price=getattr(signal, "take_profit_1", None),
            tp2_price=getattr(signal, "take_profit_2", None),
            position_size=signal.position_size,
            opened_at=datetime.now(UTC),
            closed_at=None,
            close_reason=PositionCloseReason.NONE,
            last_price=signal.entry_price,
            last_updated=datetime.now(UTC),
        )

        self._used_signal_ids.add(str(signal.signal_id))
        self.repo.save(position)
        logger.info(f"Position opened: {position.position_id}")
        return position

    def update_position_price(self, position_id: UUID, current_price: float) -> float:
        pos = self.repo.get_by_id(position_id)
        if not pos or pos.status != PositionStatus.OPEN:
            return 0.0

        updated = Position(
            position_id=pos.position_id,
            execution_id=pos.execution_id,
            order_id=pos.order_id,
            symbol=pos.symbol,
            side=pos.side,
            status=pos.status,
            entry_price=pos.entry_price,
            stop_loss=pos.stop_loss,
            take_profit=pos.take_profit,
            tp1_price=pos.tp1_price,
            tp2_price=pos.tp2_price,
            position_size=pos.position_size,
            opened_at=pos.opened_at,
            closed_at=pos.closed_at,
            close_reason=pos.close_reason,
            last_price=current_price,
            last_updated=datetime.now(UTC),
        )
        self.repo.save(updated)

        if pos.side == Side.LONG:
            pnl = (current_price - pos.entry_price) * pos.position_size
        else:
            pnl = (pos.entry_price - current_price) * pos.position_size

        return pnl

    def update_price(self, position_id: UUID, current_price: float) -> float:
        return self.update_position_price(position_id, current_price)

    def get_open_positions(self) -> list[Position]:
        return self.repo.get_open()

    def has_open_position(self, symbol: str, side: Side) -> bool:
        return any(
            p.symbol == symbol and p.side == side and p.status == PositionStatus.OPEN
            for p in self.repo.get_open()
        )

    def partial_close(
        self,
        position_id: UUID,
        exit_price: float,
        fraction: float,
    ) -> tuple[Position | None, float]:
        """Partial close sebagian posisi. Return (sisa posisi, realized pnl)."""
        pos = self.repo.get_by_id(position_id)
        if not pos or pos.status != PositionStatus.OPEN:
            logger.warning(f"Position {position_id} not found or not open")
            return None, 0.0

        if fraction <= 0 or fraction >= 1:
            return None, 0.0

        if pos.side == Side.LONG:
            pnl = (exit_price - pos.entry_price) * (pos.position_size * fraction)
        else:
            pnl = (pos.entry_price - exit_price) * (pos.position_size * fraction)

        self.realized_pnl += pnl

        new_size = pos.position_size * (1 - fraction)
        new_position = Position(
            position_id=pos.position_id,
            execution_id=pos.execution_id,
            order_id=pos.order_id,
            symbol=pos.symbol,
            side=pos.side,
            status=PositionStatus.OPEN,
            entry_price=pos.entry_price,
            stop_loss=pos.stop_loss,
            take_profit=pos.take_profit,
            tp1_price=pos.tp1_price,
            tp2_price=pos.tp2_price,
            position_size=new_size,
            opened_at=pos.opened_at,
            closed_at=None,
            close_reason=PositionCloseReason.NONE,
            last_price=exit_price,
            last_updated=datetime.now(UTC),
        )
        self.repo.save(new_position)
        logger.info(
            f"Partial close {fraction*100:.0f}% of position {position_id}: realized ${pnl:.2f}"
        )
        return new_position, pnl

    def close_position(
        self,
        position_id: UUID,
        exit_price: float,
        close_reason: PositionCloseReason = PositionCloseReason.MANUAL,
    ) -> Position | None:
        pos = self.repo.get_by_id(position_id)
        if not pos or pos.status != PositionStatus.OPEN:
            logger.warning(f"Position {position_id} not found or already closed")
            return None

        if pos.side == Side.LONG:
            pnl = (exit_price - pos.entry_price) * pos.position_size
        else:
            pnl = (pos.entry_price - exit_price) * pos.position_size

        self.realized_pnl += pnl
        logger.info(f"Realized PnL for {position_id}: {pnl:.2f}")

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
            tp1_price=pos.tp1_price,
            tp2_price=pos.tp2_price,
            position_size=pos.position_size,
            opened_at=pos.opened_at,
            closed_at=datetime.now(UTC),
            close_reason=close_reason,
            last_price=exit_price,
            last_updated=datetime.now(UTC),
        )
        self.repo.save(closed_pos)
        logger.info(f"Position closed: {closed_pos.position_id}")
        return closed_pos

    def get_state(self) -> PortfolioState:
        open_positions = self.repo.get_open()
        closed_positions = self.repo.get_closed()

        total_unrealized_pnl = 0.0
        if self.price_provider:
            total_unrealized_pnl = calculate_unrealized(open_positions, self.price_provider)

        equity = self.initial_balance + self.realized_pnl + total_unrealized_pnl

        if equity > self.peak_equity:
            self.peak_equity = equity

        drawdown = self.peak_equity - equity
        drawdown_pct = (drawdown / self.peak_equity) * 100 if self.peak_equity > 0 else 0.0

        total_pnl = self.realized_pnl + total_unrealized_pnl

        return PortfolioState(
            account_balance=self.initial_balance,
            equity=equity,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=total_unrealized_pnl,
            total_pnl=total_pnl,
            open_positions=len(open_positions),
            closed_positions=len(closed_positions),
            peak_equity=self.peak_equity,
            drawdown=drawdown,
            drawdown_percent=round(drawdown_pct, 2),
            timestamp=datetime.now(UTC),
        )