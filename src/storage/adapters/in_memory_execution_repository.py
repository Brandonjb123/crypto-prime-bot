"""In-memory Execution Repository."""

from uuid import UUID

from src.core.models.execution_result import ExecutionResult
from src.storage.repositories.execution_repository import ExecutionRepository


class InMemoryExecutionRepository(ExecutionRepository):
    def __init__(self) -> None:
        self._storage: dict[UUID, ExecutionResult] = {}

    def save(self, result: ExecutionResult) -> None:
        self._storage[result.execution_id] = result

    def get_by_id(self, execution_id: UUID) -> ExecutionResult | None:
        return self._storage.get(execution_id)

    def exists_by_signal_id(self, signal_id: UUID) -> bool:
        return any(r.signal_id == signal_id for r in self._storage.values())

    def list_all(self) -> list[ExecutionResult]:
        return list(self._storage.values())