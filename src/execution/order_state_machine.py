"""Validasi transisi status order."""

from src.core.types.enums import OrderStatus

VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.NEW: {OrderStatus.SUBMITTED, OrderStatus.CANCELLED, OrderStatus.FAILED},
    OrderStatus.SUBMITTED: {
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED,
        OrderStatus.REJECTED,
        OrderStatus.CANCELLED,
        OrderStatus.FAILED,
        OrderStatus.UNKNOWN,
    },
    OrderStatus.PARTIALLY_FILLED: {
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.FAILED,
        OrderStatus.UNKNOWN,
    },
    OrderStatus.FILLED: set(),
    OrderStatus.REJECTED: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.FAILED: set(),
    OrderStatus.UNKNOWN: {
        OrderStatus.FILLED,
        OrderStatus.REJECTED,
        OrderStatus.CANCELLED,
        OrderStatus.FAILED,
    },
}


class OrderStateMachine:
    @staticmethod
    def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
        return target in VALID_TRANSITIONS.get(current, set())