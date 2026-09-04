from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.exchange_account import ExchangeAccountSnapshot
from src.core.models.portfolio import PortfolioSnapshot
from src.core.types.enums import PortfolioStatus, SyncStatus
from src.storage.adapters.in_memory_portfolio_repository import InMemoryPortfolioRepository
from src.synchronization.portfolio_reconciler import PortfolioReconciler


class TestPortfolioReconciler:
    def test_equity_in_sync(self):
        repo = InMemoryPortfolioRepository()
        snap = PortfolioSnapshot(
            snapshot_id=uuid4(),
            timestamp=datetime.now(UTC),
            status=PortfolioStatus.ACTIVE,
            total_positions=1,
            open_positions=1,
            closed_positions=0,
            long_positions=1,
            short_positions=0,
            net_exposure=0.1,
            gross_exposure=0.1,
            realized_pnl=0.0,
            unrealized_pnl=100.0,
            equity=10100.0,
            warnings=[],
        )
        repo.save(snap)
        exchange = ExchangeAccountSnapshot(
            asset="USDT",
            wallet_balance=10000.0,
            available_balance=9500.0,
            unrealized_pnl=100.0,
            timestamp=datetime.now(UTC),
        )
        reconciler = PortfolioReconciler(repo)
        result = reconciler.reconcile(exchange, snap)
        assert result.status == SyncStatus.SYNCED

    def test_equity_mismatch(self):
        repo = InMemoryPortfolioRepository()
        snap = PortfolioSnapshot(
            snapshot_id=uuid4(),
            timestamp=datetime.now(UTC),
            status=PortfolioStatus.ACTIVE,
            total_positions=1,
            open_positions=1,
            closed_positions=0,
            long_positions=1,
            short_positions=0,
            net_exposure=0.1,
            gross_exposure=0.1,
            realized_pnl=0.0,
            unrealized_pnl=50.0,
            equity=10050.0,
            warnings=[],
        )
        exchange = ExchangeAccountSnapshot(
            asset="USDT",
            wallet_balance=10000.0,
            available_balance=9500.0,
            unrealized_pnl=200.0,
            timestamp=datetime.now(UTC),
        )
        reconciler = PortfolioReconciler(repo)
        result = reconciler.reconcile(exchange, snap)
        assert result.status == SyncStatus.MISMATCH
