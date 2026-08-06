from uuid import uuid4
from datetime import datetime, UTC
from src.core.models.position import Position
from src.core.types.enums import (
    PositionCloseReason, PositionStatus, Side,
    SyncEntityType, SyncReason, SyncStatus,
)
from src.storage.adapters.in_memory_position_repository import InMemoryPositionRepository
from src.synchronization.position_reconciler import PositionReconciler


def _make_pos(symbol="BTCUSDT", side=Side.LONG, size=0.1, status=PositionStatus.OPEN):
    return Position(
        position_id=uuid4(), execution_id=uuid4(), order_id=uuid4(),
        symbol=symbol, side=side, status=status,
        entry_price=50000.0, stop_loss=48000.0, take_profit=55000.0,
        position_size=size, opened_at=datetime.now(UTC),
        closed_at=None if status == PositionStatus.OPEN else datetime.now(UTC),
        close_reason=PositionCloseReason.NONE if status == PositionStatus.OPEN else PositionCloseReason.MANUAL,
    )


class TestPositionReconciler:
    def test_same_position_synced(self):
        repo = InMemoryPositionRepository()
        pos = _make_pos()
        repo.save(pos)
        reconciler = PositionReconciler(repo)
        result = reconciler.reconcile([pos])
        assert result.status == SyncStatus.SYNCED
        assert result.synced_count == 1
        assert result.mismatch_count == 0

    def test_exchange_missing_closes_local(self):
        repo = InMemoryPositionRepository()
        pos = _make_pos()
        repo.save(pos)
        reconciler = PositionReconciler(repo)
        result = reconciler.reconcile([])
        assert result.status == SyncStatus.MISMATCH
        assert SyncReason.EXCHANGE_MISSING in result.reasons

    def test_local_missing_creates(self):
        repo = InMemoryPositionRepository()
        reconciler = PositionReconciler(repo)
        pos = _make_pos()
        result = reconciler.reconcile([pos])
        assert SyncReason.LOCAL_MISSING in result.reasons
        assert repo.count() >= 1

    def test_size_mismatch(self):
        repo = InMemoryPositionRepository()
        local = _make_pos(size=0.1)
        repo.save(local)
        # Buat exchange position dengan ID yang sama tapi size beda
        exchange = Position(
            position_id=local.position_id,
            execution_id=local.execution_id,
            order_id=local.order_id,
            symbol=local.symbol,
            side=local.side,
            status=local.status,
            entry_price=local.entry_price,
            stop_loss=local.stop_loss,
            take_profit=local.take_profit,
            position_size=0.2,  # size berbeda
            opened_at=local.opened_at,
            closed_at=local.closed_at,
            close_reason=local.close_reason,
        )
        reconciler = PositionReconciler(repo)
        result = reconciler.reconcile([exchange])
        assert SyncReason.SIZE_CHANGED in result.reasons