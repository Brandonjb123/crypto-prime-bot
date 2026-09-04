"""Position Reconciler — bandingkan exchange positions dengan local."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.models.synchronization import SyncResult
from src.core.types.enums import (
    PositionCloseReason,
    PositionStatus,
    SyncEntityType,
    SyncReason,
    SyncStatus,
)
from src.events.event_bus import EventBus
from src.events.events.position_updated import PositionUpdatedEvent
from src.storage.repositories.position_repository import PositionRepository


class PositionReconciler:
    def __init__(self, repository: PositionRepository, event_bus: EventBus | None = None):
        self.repository = repository
        self.event_bus = event_bus

    def reconcile(self, exchange_positions: list[Position]) -> SyncResult:
        local_positions = self.repository.get_all()
        details: list[str] = []
        reasons: list[SyncReason] = []
        synced = 0
        mismatch = 0

        # Map exchange positions by symbol
        exchange_map: dict[str, Position] = {}
        for ep in exchange_positions:
            exchange_map[ep.symbol] = ep

        # Check local positions against exchange
        for lp in local_positions:
            if lp.status != PositionStatus.OPEN:
                continue
            ep = exchange_map.get(lp.symbol)
            if ep is None:
                # Local has position, exchange doesn't → mark closed
                reasons.append(SyncReason.EXCHANGE_MISSING)
                mismatch += 1
                details.append(f"EXCHANGE_MISSING: {lp.symbol} — marking closed")
                closed = Position(
                    position_id=lp.position_id,
                    execution_id=lp.execution_id,
                    order_id=lp.order_id,
                    symbol=lp.symbol,
                    side=lp.side,
                    status=PositionStatus.CLOSED,
                    entry_price=lp.entry_price,
                    stop_loss=lp.stop_loss,
                    take_profit=lp.take_profit,
                    position_size=lp.position_size,
                    opened_at=lp.opened_at,
                    closed_at=datetime.now(UTC),
                    close_reason=PositionCloseReason.MANUAL,
                    last_price=lp.last_price,
                    last_updated=datetime.now(UTC),
                )
                self.repository.save(closed)
                if self.event_bus:
                    self.event_bus.publish(
                        PositionUpdatedEvent(
                            position_id=lp.position_id,
                            old_status=PositionStatus.OPEN,
                            new_status=PositionStatus.CLOSED,
                            reason="EXCHANGE_MISSING",
                        )
                    )
                continue

            # Both exist — compare
            if abs(ep.position_size - lp.position_size) > 0.0001:
                reasons.append(SyncReason.SIZE_CHANGED)
                mismatch += 1
                details.append(
                    f"SIZE_CHANGED: {lp.symbol} ({lp.position_size} → {ep.position_size})"
                )
                # Update local with exchange size
                updated = Position(
                    position_id=lp.position_id,
                    execution_id=lp.execution_id,
                    order_id=lp.order_id,
                    symbol=lp.symbol,
                    side=lp.side,
                    status=lp.status,
                    entry_price=lp.entry_price,
                    stop_loss=lp.stop_loss,
                    take_profit=lp.take_profit,
                    position_size=ep.position_size,
                    opened_at=lp.opened_at,
                    closed_at=lp.closed_at,
                    close_reason=lp.close_reason,
                    last_price=ep.last_price,
                    last_updated=datetime.now(UTC),
                )
                self.repository.save(updated)
            else:
                synced += 1

        # Check exchange positions not in local
        local_map = {p.symbol: p for p in local_positions if p.status == PositionStatus.OPEN}
        for symbol, ep in exchange_map.items():
            if symbol not in local_map:
                reasons.append(SyncReason.LOCAL_MISSING)
                mismatch += 1
                details.append(f"LOCAL_MISSING: {symbol} — creating")
                new_pos = Position(
                    position_id=uuid4(),
                    execution_id=uuid4(),
                    order_id=uuid4(),
                    symbol=ep.symbol,
                    side=ep.side,
                    status=PositionStatus.OPEN,
                    entry_price=ep.entry_price,
                    stop_loss=ep.stop_loss,
                    take_profit=ep.take_profit,
                    position_size=ep.position_size,
                    opened_at=datetime.now(UTC),
                    closed_at=None,
                    close_reason=PositionCloseReason.NONE,
                    last_price=ep.last_price,
                    last_updated=datetime.now(UTC),
                )
                self.repository.save(new_pos)

        status = SyncStatus.SYNCED if mismatch == 0 else SyncStatus.MISMATCH
        return SyncResult(
            status=status,
            entity_type=SyncEntityType.POSITION,
            synced_count=synced,
            mismatch_count=mismatch,
            reasons=list(set(reasons)),
            details=details,
            timestamp=datetime.now(UTC),
        )
