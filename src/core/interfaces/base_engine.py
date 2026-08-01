from abc import ABC, abstractmethod
from typing import Any


class BaseEngine(ABC):
    """Abstract base class untuk semua processing engines."""

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input dan return output."""
        ...

    @abstractmethod
    async def validate_input(self, input_data: Any) -> bool:
        """Validate input sebelum processing."""
        ...