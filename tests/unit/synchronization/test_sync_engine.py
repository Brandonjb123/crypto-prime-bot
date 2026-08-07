from unittest.mock import AsyncMock, MagicMock

from src.core.types.enums import SyncEntityType, SyncStatus
from src.storage.adapters.in_memory_order_repository import InMemoryOrderRepository
from src.storage.adapters.in_memory_portfolio_repository import InMemoryPortfolioRepository
from src.storage.adapters.in_memory_position_repository import InMemoryPositionRepository
from src.synchronization.order_reconciler import OrderReconciler
from src.synchronization.portfolio_reconciler import PortfolioReconciler
from src.synchronization.position_reconciler import PositionReconciler
from src.synchronization.sync_engine import ExchangeSyncEngine


class TestExchangeSyncEngine:
    async def test_full_sync_success(self):
        pos_provider = MagicMock()
        pos_provider.get_exchange_positions = AsyncMock(return_value=[])
        order_provider = MagicMock()
        order_provider.get_exchange_orders = AsyncMock(return_value=[])
        balance_provider = MagicMock()
        balance_provider.get_account_snapshot = AsyncMock(
            return_value=MagicMock(
                wallet_balance=10000.0,
                available_balance=9500.0,
                unrealized_pnl=100.0,
            )
        )

        engine = ExchangeSyncEngine(
            exchange_position_provider=pos_provider,
            exchange_order_provider=order_provider,
            exchange_balance_provider=balance_provider,
            position_reconciler=PositionReconciler(InMemoryPositionRepository()),
            order_reconciler=OrderReconciler(InMemoryOrderRepository()),
            portfolio_reconciler=PortfolioReconciler(InMemoryPortfolioRepository()),
        )
        results = await engine.sync()
        assert len(results) == 3
        assert all(
            r.status in (SyncStatus.SYNCED, SyncStatus.MISMATCH, SyncStatus.FAILED) for r in results
        )

    async def test_empty_exchange(self):
        pos_provider = MagicMock()
        pos_provider.get_exchange_positions = AsyncMock(return_value=[])
        engine = ExchangeSyncEngine(
            exchange_position_provider=pos_provider,
            position_reconciler=PositionReconciler(InMemoryPositionRepository()),
        )
        results = await engine.sync()
        assert len(results) == 1
        assert results[0].entity_type == SyncEntityType.POSITION

    async def test_provider_failure(self):
        pos_provider = MagicMock()
        pos_provider.get_exchange_positions = AsyncMock(side_effect=Exception("API down"))
        engine = ExchangeSyncEngine(
            exchange_position_provider=pos_provider,
            position_reconciler=PositionReconciler(InMemoryPositionRepository()),
        )
        results = await engine.sync()
        assert results[0].status == SyncStatus.FAILED
