"""Order Repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.core.models.order import OrderResult


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: OrderResult) -> None:
        ...

    @abstractmethod
    def get_by_id(self, order_id: UUID) -> OrderResult | None:
        ...

    @abstractmethod
    def get_all(self) -> list[OrderResult]:
        ...

    @abstractmethod
    def delete(self, order_id: UUID) -> None:
        ...

    @abstractmethod
    def count(self) -> int:
        ...