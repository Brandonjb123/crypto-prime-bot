from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.order import OrderResult
from src.core.types.enums import (
    ExecutionType,
    OrderRejectReason,
    OrderStatus,
    Side,
    SyncReason,
    SyncStatus,
)
from src.storage.adapters.in_memory_order_repository import InMemoryOrderRepository
from src.synchronization.order_reconciler import OrderReconciler


def _make_order(order_id=None, status=OrderStatus.FILLED):
    return OrderResult(
        execution_id=uuid4(),
        order_id=order_id or uuid4(),
        status=status,
        reject_reason=OrderRejectReason.NONE,
        execution_type=ExecutionType.MARKET,
        side=Side.LONG,
        symbol="BTCUSDT",
        requested_entry=50000.0,
        executed_entry=50000.0,
        position_size=0.1,
        stop_loss=48000.0,
        take_profit=55000.0,
        timestamp=datetime.now(UTC),
    )


class TestOrderReconciler:
    def test_same_order_synced(self):
        repo = InMemoryOrderRepository()
        order = _make_order()
        repo.save(order)
        reconciler = OrderReconciler(repo)
        result = reconciler.reconcile([order])
        assert result.status == SyncStatus.SYNCED

    def test_status_changed(self):
        repo = InMemoryOrderRepository()
        order = _make_order(status=OrderStatus.PENDING)
        repo.save(order)
        updated = _make_order(order_id=order.order_id, status=OrderStatus.FILLED)
        reconciler = OrderReconciler(repo)
        result = reconciler.reconcile([updated])
        assert SyncReason.STATUS_CHANGED in result.reasons

    def test_local_missing(self):
        repo = InMemoryOrderRepository()
        reconciler = OrderReconciler(repo)
        order = _make_order()
        result = reconciler.reconcile([order])
        assert SyncReason.LOCAL_MISSING in result.reasons
