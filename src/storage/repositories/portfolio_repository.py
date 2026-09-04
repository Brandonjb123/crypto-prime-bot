"""Portfolio Repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.core.models.portfolio import PortfolioSnapshot


class PortfolioRepository(ABC):
    @abstractmethod
    def save(self, snapshot: PortfolioSnapshot) -> None: ...

    @abstractmethod
    def get_by_id(self, snapshot_id: UUID) -> PortfolioSnapshot | None: ...

    @abstractmethod
    def get_all(self) -> list[PortfolioSnapshot]: ...

    @abstractmethod
    def latest(self) -> PortfolioSnapshot | None: ...

    @abstractmethod
    def history(self) -> list[PortfolioSnapshot]: ...

    @abstractmethod
    def delete(self, snapshot_id: UUID) -> None: ...

    @abstractmethod
    def count(self) -> int: ...
