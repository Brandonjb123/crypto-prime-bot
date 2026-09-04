"""Unit tests untuk OrderRepository."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.order import OrderResult
from src.core.types.enums import ExecutionType, OrderRejectReason, OrderStatus, Side
from src.storage.adapters.in_memory_order_repository import InMemoryOrderRepository


def _make_order():
    return OrderResult(
        execution_id=uuid4(),
        order_id=uuid4(),
        status=OrderStatus.FILLED,
        reject_reason=OrderRejectReason.NONE,
        execution_type=ExecutionType.MARKET,
        side=Side.LONG,
        symbol="BTC/USDT",
        requested_entry=50000.0,
        executed_entry=50000.0,
        position_size=0.1,
        stop_loss=48000.0,
        take_profit=55000.0,
        timestamp=datetime.now(UTC),
    )


class TestOrderRepository:
    def repo(self):
        return InMemoryOrderRepository()

    def test_save_and_get(self):
        repo = self.repo()
        order = _make_order()
        repo.save(order)
        found = repo.get_by_id(order.order_id)
        assert found is not None

    def test_get_all(self):
        repo = self.repo()
        repo.save(_make_order())
        repo.save(_make_order())
        assert len(repo.get_all()) == 2

    def test_delete(self):
        repo = self.repo()
        order = _make_order()
        repo.save(order)
        repo.delete(order.order_id)
        assert repo.get_by_id(order.order_id) is None

    def test_count(self):
        repo = self.repo()
        repo.save(_make_order())
        assert repo.count() == 1
