"""Base Exchange Adapter interface."""

from abc import ABC, abstractmethod

from src.core.models.execution import ExecutionPlan
from src.core.models.order import OrderResult


class BaseExchangeAdapter(ABC):
    @abstractmethod
    async def place_order(self, execution_plan: ExecutionPlan) -> OrderResult:
        """Place order berdasarkan execution plan."""
        ...
