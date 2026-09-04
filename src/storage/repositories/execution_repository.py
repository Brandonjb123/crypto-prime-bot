"""Execution Repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.core.models.execution_result import ExecutionResult


class ExecutionRepository(ABC):
    @abstractmethod
    def save(self, result: ExecutionResult) -> None:
        ...

    @abstractmethod
    def get_by_id(self, execution_id: UUID) -> ExecutionResult | None:
        ...

    @abstractmethod
    def exists_by_signal_id(self, signal_id: UUID) -> bool:
        ...

    @abstractmethod
    def list_all(self) -> list[ExecutionResult]:
        ...