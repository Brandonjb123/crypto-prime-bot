"""Base Exchange Adapter interface."""

from abc import ABC, abstractmethod
from typing import Any

from src.core.models.execution import ExecutionPlan
from src.core.models.order import OrderResult


class BaseExchangeAdapter(ABC):
    @abstractmethod
    async def place_order(self, execution_plan: ExecutionPlan) -> OrderResult:
        """Place order berdasarkan execution plan."""
        ...

    @abstractmethod
    async def cancel_order(self, exchange_order_id: str) -> OrderResult:
        """Cancel order by exchange order ID."""
        ...

    @abstractmethod
    async def get_order(self, exchange_order_id: str) -> OrderResult:
        """Get order status by exchange order ID."""
        ...

    @abstractmethod
    async def get_open_orders(self, symbol: str | None = None) -> list[OrderResult]:
        """Get open orders."""
        ...

    @abstractmethod
    async def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get current positions."""
        ...

    @abstractmethod
    async def get_balance(self) -> dict[str, float]:
        """Get account balance."""
        ...