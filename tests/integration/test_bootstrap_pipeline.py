"""Integration test: Bootstrap → Container → main components exist."""

from src.bootstrap.container import Container
from src.events.event_bus import EventBus
from src.portfolio.portfolio_manager import PortfolioManager
from src.position.position_manager import PositionManager


class TestBootstrapPipeline:
    def test_container_wiring(self):
        c = Container()
        assert isinstance(c.event_bus, EventBus)
        assert isinstance(c.position_manager, PositionManager)
        assert isinstance(c.portfolio_manager, PortfolioManager)
        assert c.position_repo is not None
        assert c.order_repo is not None
        assert c.portfolio_repo is not None