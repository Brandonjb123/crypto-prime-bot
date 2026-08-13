"""InMemory Order Repository — untuk Phase 1."""

from src.core.models.live_order import LiveOrder


class OrderRepository:
    def __init__(self):
        self._orders: dict[str, LiveOrder] = {}

    def save(self, order: LiveOrder):
        self._orders[str(order.execution_id)] = order

    def get(self, execution_id: str) -> LiveOrder | None:
        return self._orders.get(execution_id)

    def get_by_client_order_id(self, client_order_id: str) -> LiveOrder | None:
        for order in self._orders.values():
            if order.client_order_id == client_order_id:
                return order
        return None

    def update(self, order: LiveOrder):
        self._orders[str(order.execution_id)] = order

    def get_all(self) -> list[LiveOrder]:
        return list(self._orders.values())