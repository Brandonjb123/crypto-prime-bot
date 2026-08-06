"""In-memory Position Repository."""

from uuid import UUID

from src.core.models.position import Position
from src.core.types.enums import PositionStatus
from src.storage.repositories.position_repository import PositionRepository


class InMemoryPositionRepository(PositionRepository):
    def __init__(self) -> None:
        self._storage: dict[UUID, Position] = {}

    def save(self, position: Position) -> None:
        self._storage[position.position_id] = position

    def get_by_id(self, position_id: UUID) -> Position | None:
        return self._storage.get(position_id)

    def get_open(self) -> list[Position]:
        return [p for p in self._storage.values() if p.status == PositionStatus.OPEN]

    def get_closed(self) -> list[Position]:
        return [p for p in self._storage.values() if p.status != PositionStatus.OPEN]

    def get_all(self) -> list[Position]:
        return list(self._storage.values())

    def delete(self, position_id: UUID) -> None:
        self._storage.pop(position_id, None)

    def exists(self, position_id: UUID) -> bool:
        return position_id in self._storage

    def count(self) -> int:
        return len(self._storage)