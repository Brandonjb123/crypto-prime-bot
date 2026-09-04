"""Order Reconciler — bandingkan exchange orders dengan local."""

from datetime import UTC, datetime

from src.core.models.order import OrderResult
from src.core.models.synchronization import SyncResult
from src.core.types.enums import SyncEntityType, SyncReason, SyncStatus
from src.storage.repositories.order_repository import OrderRepository


class OrderReconciler:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def reconcile(self, exchange_orders: list[OrderResult]) -> SyncResult:
        local_orders = self.repository.get_all()
        details: list[str] = []
        reasons: list[SyncReason] = []
        synced = 0
        mismatch = 0

        exchange_map = {str(o.order_id): o for o in exchange_orders}

        for lo in local_orders:
            eo = exchange_map.get(str(lo.order_id))
            if eo is None:
                reasons.append(SyncReason.EXCHANGE_MISSING)
                mismatch += 1
                continue

            if eo.status != lo.status:
                reasons.append(SyncReason.STATUS_CHANGED)
                mismatch += 1
                details.append(
                    f"STATUS_CHANGED: {lo.order_id} ({lo.status.value} → {eo.status.value})"
                )
                # Update local order
                updated = OrderResult(
                    execution_id=lo.execution_id,
                    order_id=lo.order_id,
                    status=eo.status,
                    reject_reason=eo.reject_reason,
                    execution_type=lo.execution_type,
                    side=lo.side,
                    symbol=lo.symbol,
                    requested_entry=lo.requested_entry,
                    executed_entry=eo.executed_entry,
                    position_size=lo.position_size,
                    stop_loss=lo.stop_loss,
                    take_profit=lo.take_profit,
                    timestamp=datetime.now(UTC),
                )
                self.repository.save(updated)
            else:
                synced += 1

        # Exchange orders not in local
        local_ids = {str(o.order_id) for o in local_orders}
        for eo in exchange_orders:
            if str(eo.order_id) not in local_ids:
                reasons.append(SyncReason.LOCAL_MISSING)
                mismatch += 1
                details.append(f"LOCAL_MISSING: {eo.order_id} — saving")
                self.repository.save(eo)

        status = SyncStatus.SYNCED if mismatch == 0 else SyncStatus.MISMATCH
        return SyncResult(
            status=status,
            entity_type=SyncEntityType.ORDER,
            synced_count=synced,
            mismatch_count=mismatch,
            reasons=list(set(reasons)),
            details=details,
            timestamp=datetime.now(UTC),
        )
