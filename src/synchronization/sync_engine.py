"""Exchange Sync Engine — orchestrator untuk semua reconciler."""

from datetime import UTC, datetime

from src.core.models.synchronization import SyncResult
from src.core.types.enums import SyncEntityType, SyncReason, SyncStatus
from src.synchronization.order_reconciler import OrderReconciler
from src.synchronization.portfolio_reconciler import PortfolioReconciler
from src.synchronization.position_reconciler import PositionReconciler


class ExchangeSyncEngine:
    def __init__(
        self,
        exchange_position_provider,
        exchange_order_provider=None,
        exchange_balance_provider=None,
        position_reconciler: PositionReconciler | None = None,
        order_reconciler: OrderReconciler | None = None,
        portfolio_reconciler: PortfolioReconciler | None = None,
    ):
        self.exchange_position_provider = exchange_position_provider
        self.exchange_order_provider = exchange_order_provider
        self.exchange_balance_provider = exchange_balance_provider
        self.position_reconciler = position_reconciler
        self.order_reconciler = order_reconciler
        self.portfolio_reconciler = portfolio_reconciler

    async def sync(self) -> list[SyncResult]:
        results: list[SyncResult] = []

        # Sync positions
        if self.exchange_position_provider and self.position_reconciler:
            try:
                exchange_positions = await self.exchange_position_provider.get_exchange_positions()
                result = self.position_reconciler.reconcile(exchange_positions)
                results.append(result)
            except Exception as e:
                results.append(
                    SyncResult(
                        status=SyncStatus.FAILED,
                        entity_type=SyncEntityType.POSITION,
                        synced_count=0,
                        mismatch_count=0,
                        reasons=[SyncReason.UNKNOWN],
                        details=[str(e)],
                        timestamp=datetime.now(UTC),
                    )
                )

        # Sync orders
        if self.exchange_order_provider and self.order_reconciler:
            try:
                exchange_orders = await self.exchange_order_provider.get_exchange_orders()
                result = self.order_reconciler.reconcile(exchange_orders)
                results.append(result)
            except Exception as e:
                results.append(
                    SyncResult(
                        status=SyncStatus.FAILED,
                        entity_type=SyncEntityType.ORDER,
                        synced_count=0,
                        mismatch_count=0,
                        reasons=[SyncReason.UNKNOWN],
                        details=[str(e)],
                        timestamp=datetime.now(UTC),
                    )
                )

        # Sync portfolio
        if self.exchange_balance_provider and self.portfolio_reconciler:
            try:
                exchange_snapshot = await self.exchange_balance_provider.get_account_snapshot()
                local_snapshot = self.portfolio_reconciler.repository.latest()
                result = self.portfolio_reconciler.reconcile(exchange_snapshot, local_snapshot)
                results.append(result)
            except Exception as e:
                results.append(
                    SyncResult(
                        status=SyncStatus.FAILED,
                        entity_type=SyncEntityType.PORTFOLIO,
                        synced_count=0,
                        mismatch_count=0,
                        reasons=[SyncReason.UNKNOWN],
                        details=[str(e)],
                        timestamp=datetime.now(UTC),
                    )
                )

        return results
