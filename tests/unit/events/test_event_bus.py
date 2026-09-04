"""Unit tests untuk EventBus."""

from src.events.base_event import BaseDomainEvent
from src.events.event_bus import EventBus


class TestEventBus:
    def bus(self):
        return EventBus()

    def test_register_and_publish(self):
        bus = self.bus()
        received = []
        bus.register("test_event", lambda e: received.append(e))
        event = BaseDomainEvent(event_name="test_event")
        bus.publish(event)
        assert len(received) == 1
        assert received[0].event_name == "test_event"

    def test_publish_without_handler_no_error(self):
        bus = self.bus()
        event = BaseDomainEvent(event_name="no_handler_event")
        bus.publish(event)  # tidak raise exception

    def test_multiple_handlers_receive_event(self):
        bus = self.bus()
        received = []
        bus.register("test_event", lambda e: received.append(1))
        bus.register("test_event", lambda e: received.append(2))
        bus.publish(BaseDomainEvent(event_name="test_event"))
        assert len(received) == 2

    def test_handler_order_fifo(self):
        bus = self.bus()
        order = []
        bus.register("test_event", lambda e: order.append("first"))
        bus.register("test_event", lambda e: order.append("second"))
        bus.publish(BaseDomainEvent(event_name="test_event"))
        assert order == ["first", "second"]

    def test_handler_exception_does_not_stop_dispatch(self):
        bus = self.bus()
        received = []

        def failing_handler(event):
            raise RuntimeError("handler error")

        bus.register("test_event", failing_handler)
        bus.register("test_event", lambda e: received.append("ok"))
        bus.publish(BaseDomainEvent(event_name="test_event"))
        assert received == ["ok"]

    def test_unregister(self):
        bus = self.bus()
        received = []

        def handler(e):
            received.append(e)

        bus.register("test_event", handler)
        bus.unregister("test_event", handler)
        bus.publish(BaseDomainEvent(event_name="test_event"))
        assert len(received) == 0

    def test_deterministic(self):
        bus1 = EventBus()
        bus2 = EventBus()
        received1 = []
        received2 = []
        bus1.register("test", lambda e: received1.append("x"))
        bus2.register("test", lambda e: received2.append("x"))
        bus1.publish(BaseDomainEvent(event_name="test"))
        bus2.publish(BaseDomainEvent(event_name="test"))
        assert received1 == received2
