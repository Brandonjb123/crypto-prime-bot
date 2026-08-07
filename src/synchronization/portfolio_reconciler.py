"""Portfolio Reconciler — bandingkan exchange balance dengan local portfolio."""

from datetime import UTC, datetime

from src.core.models.exchange_account import ExchangeAccountSnapshot
from src.core.models.portfolio import PortfolioSnapshot
from src.core.models.synchronization import SyncResult
from src.core.types.enums import SyncEntityType, SyncReason, SyncStatus
from src.events.event_bus import EventBus
from src.events.events.portfolio_updated import PortfolioUpdatedEvent
from src.storage.repositories.portfolio_repository import PortfolioRepository


class PortfolioReconciler:
    def __init__(self, repository: PortfolioRepository, event_bus: EventBus | None = None):
        self.repository = repository
        self.event_bus = event_bus

    def reconcile(
        self,
        exchange_snapshot: ExchangeAccountSnapshot,
        local_snapshot: PortfolioSnapshot | None,
    ) -> SyncResult:
        details: list[str] = []
        reasons: list[SyncReason] = []

        if local_snapshot is None:
            reasons.append(SyncReason.LOCAL_MISSING)
            # Save exchange snapshot as local
            if self.event_bus:
                self.event_bus.publish(
                    PortfolioUpdatedEvent(
                        snapshot_id=local_snapshot.snapshot_id if local_snapshot else None,
                        equity=exchange_snapshot.wallet_balance + exchange_snapshot.unrealized_pnl,
                        gross_exposure=0.0,
                        net_exposure=0.0,
                    )
                )

            return SyncResult(
                status=SyncStatus.MISMATCH,
                entity_type=SyncEntityType.PORTFOLIO,
                synced_count=0,
                mismatch_count=1,
                reasons=reasons,
                details=details,
                timestamp=datetime.now(UTC),
            )

        # Compare equity
        exchange_equity = exchange_snapshot.wallet_balance + exchange_snapshot.unrealized_pnl
        local_equity = local_snapshot.equity

        if abs(exchange_equity - local_equity) > 1.0:  # tolerance $1
            reasons.append(SyncReason.PRICE_CHANGED)
            details.append(
                f"Equity mismatch: local={local_equity:.2f} exchange={exchange_equity:.2f}"
            )

            if self.event_bus:
                self.event_bus.publish(
                    PortfolioUpdatedEvent(
                        snapshot_id=local_snapshot.snapshot_id,
                        equity=exchange_equity,
                        gross_exposure=local_snapshot.gross_exposure,
                        net_exposure=local_snapshot.net_exposure,
                    )
                )

            return SyncResult(
                status=SyncStatus.MISMATCH,
                entity_type=SyncEntityType.PORTFOLIO,
                synced_count=0,
                mismatch_count=1,
                reasons=reasons,
                details=details,
                timestamp=datetime.now(UTC),
            )

        return SyncResult(
            status=SyncStatus.SYNCED,
            entity_type=SyncEntityType.PORTFOLIO,
            synced_count=1,
            mismatch_count=0,
            reasons=[],
            details=["Portfolio in sync"],
            timestamp=datetime.now(UTC),
        )
