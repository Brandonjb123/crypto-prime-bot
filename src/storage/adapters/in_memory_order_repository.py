"""In-memory Order Repository."""

from uuid import UUID

from src.core.models.order import OrderResult
from src.storage.repositories.order_repository import OrderRepository


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._storage: dict[UUID, OrderResult] = {}

    def save(self, order: OrderResult) -> None:
        self._storage[order.order_id] = order

    def get_by_id(self, order_id: UUID) -> OrderResult | None:
        return self._storage.get(order_id)

    def get_all(self) -> list[OrderResult]:
        return list(self._storage.values())

    def delete(self, order_id: UUID) -> None:
        self._storage.pop(order_id, None)

    def exists(self, order_id: UUID) -> bool:
        return order_id in self._storage

    def count(self) -> int:
        return len(self._storage)