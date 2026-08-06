"""In-memory Portfolio Repository."""

from uuid import UUID

from src.core.models.portfolio import PortfolioSnapshot
from src.storage.repositories.portfolio_repository import PortfolioRepository


class InMemoryPortfolioRepository(PortfolioRepository):
    def __init__(self) -> None:
        self._storage: dict[UUID, PortfolioSnapshot] = {}

    def save(self, snapshot: PortfolioSnapshot) -> None:
        self._storage[snapshot.snapshot_id] = snapshot

    def get_by_id(self, snapshot_id: UUID) -> PortfolioSnapshot | None:
        return self._storage.get(snapshot_id)

    def get_all(self) -> list[PortfolioSnapshot]:
        return list(self._storage.values())

    def latest(self) -> PortfolioSnapshot | None:
        if not self._storage:
            return None
        return max(self._storage.values(), key=lambda s: s.timestamp)

    def history(self) -> list[PortfolioSnapshot]:
        return sorted(self._storage.values(), key=lambda s: s.timestamp, reverse=True)

    def delete(self, snapshot_id: UUID) -> None:
        self._storage.pop(snapshot_id, None)

    def exists(self, snapshot_id: UUID) -> bool:
        return snapshot_id in self._storage

    def count(self) -> int:
        return len(self._storage)