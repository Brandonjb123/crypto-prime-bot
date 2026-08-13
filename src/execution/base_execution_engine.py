"""Abstract base class untuk semua execution engine."""

from abc import ABC, abstractmethod
from typing import Any


class BaseExecutionEngine(ABC):
    @abstractmethod
    async def execute(self, signal: Any) -> Any:
        """Eksekusi trading signal."""
        ...

    @abstractmethod
    async def cancel(self, execution_id: str) -> Any:
        """Batalkan eksekusi."""
        ...

    @abstractmethod
    async def get_status(self, execution_id: str) -> Any:
        """Cek status eksekusi."""
        ...