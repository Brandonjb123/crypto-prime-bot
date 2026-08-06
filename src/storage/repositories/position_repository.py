"""Position Repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.core.models.position import Position


class PositionRepository(ABC):
    @abstractmethod
    def save(self, position: Position) -> None:
        ...

    @abstractmethod
    def get_by_id(self, position_id: UUID) -> Position | None:
        ...

    @abstractmethod
    def get_open(self) -> list[Position]:
        ...

    @abstractmethod
    def get_closed(self) -> list[Position]:
        ...

    @abstractmethod
    def delete(self, position_id: UUID) -> None:
        ...

    @abstractmethod
    def get_all(self) -> list[Position]:
        ...

    @abstractmethod
    def count(self) -> int:
        ...