"""Integration test: Mock Binance → Sync Engine → Repository."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import (
    PositionCloseReason,
    PositionStatus,
    Side,
)
from src.storage.adapters.in_memory_position_repository import InMemoryPositionRepository
from src.synchronization.position_reconciler import PositionReconciler
from src.synchronization.sync_engine import ExchangeSyncEngine


class TestExchangeSyncPipeline:
    async def test_sync_positions_from_exchange(self):
        # Setup exchange mock
        pos_provider = MagicMock()
        exchange_positions = [
            Position(
                position_id=uuid4(),
                execution_id=uuid4(),
                order_id=uuid4(),
                symbol="BTCUSDT",
                side=Side.LONG,
                status=PositionStatus.OPEN,
                entry_price=50000.0,
                stop_loss=0.0,
                take_profit=0.0,
                position_size=0.15,
                opened_at=datetime.now(UTC),
                closed_at=None,
                close_reason=PositionCloseReason.NONE,
            ),
        ]
        pos_provider.get_exchange_positions = AsyncMock(return_value=exchange_positions)

        repo = InMemoryPositionRepository()
        engine = ExchangeSyncEngine(
            exchange_position_provider=pos_provider,
            position_reconciler=PositionReconciler(repo),
        )
        results = await engine.sync()

        assert len(results) == 1
        assert results[0].entity_type.value == "POSITION"
        assert repo.count() >= 1
