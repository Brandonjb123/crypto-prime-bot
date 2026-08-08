"""Dependency Injection Container — assembles all services."""

from config.constants import TELEGRAM_BOT_TOKEN
from src.analysis.indicator_engine import IndicatorEngine
from src.application.scheduler import SimpleScheduler
from src.collectors.binance_collector import BinanceCollector
from src.core.types.enums import TelegramCommand
from src.events.event_bus import EventBus
from src.events.events.order_executed import OrderExecutedEvent
from src.events.events.portfolio_updated import PortfolioUpdatedEvent
from src.events.events.position_closed import PositionClosedEvent
from src.events.events.position_opened import PositionOpenedEvent
from src.exchange.adapters.paper import PaperExchangeAdapter
from src.exchange.executor import OrderExecutor
from src.infrastructure.telegram.telegram_service import TelegramService
from src.lifecycle.trade_lifecycle_engine import TradeLifecycleEngine
from src.logging.audit_logger import AuditLogger
from src.logging.logger import get_logger
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.monitoring.health import HealthMonitor
from src.monitoring.metrics import MetricsCollector
from src.monitoring.runtime_monitor import RuntimeMonitor
from src.notification.dispatcher import NotificationDispatcher
from src.notification.formatters.order_formatter import OrderExecutedFormatter
from src.notification.formatters.portfolio_formatter import PortfolioUpdatedFormatter
from src.notification.formatters.position_formatter import (
    PositionClosedFormatter,
    PositionOpenedFormatter,
)
from src.pipeline.pipeline_runner import PipelineRunner
from src.portfolio.portfolio_manager import PortfolioManager
from src.position.position_manager import PositionManager
from src.storage.adapters.in_memory_order_repository import InMemoryOrderRepository
from src.storage.adapters.in_memory_portfolio_repository import InMemoryPortfolioRepository
from src.storage.adapters.in_memory_position_repository import InMemoryPositionRepository
from src.telegram.bot import TelegramBot
from src.telegram.command_handler import (
    help_handler,
    last_signal_handler,
    portfolio_handler,
    positions_handler,
    status_handler,
)
from src.telegram.command_router import CommandRouter
from src.telegram.notifier import TelegramNotifier


class Container:
    def __init__(self):
        self.logger = get_logger("bootstrap")
        self.audit_logger = AuditLogger()

        self.event_bus = EventBus()

        self.position_repo = InMemoryPositionRepository()
        self.order_repo = InMemoryOrderRepository()
        self.portfolio_repo = InMemoryPortfolioRepository()

        self.price_provider = InMemoryPriceProvider()

        self.position_manager = PositionManager(event_bus=self.event_bus)
        self.portfolio_manager = PortfolioManager(event_bus=self.event_bus)
        self.lifecycle_engine = TradeLifecycleEngine()

        self.paper_exchange = PaperExchangeAdapter()
        self.order_executor = OrderExecutor(adapter=self.paper_exchange, event_bus=self.event_bus)

        self.telegram_service = TelegramService(token=TELEGRAM_BOT_TOKEN)
        self.telegram_notifier = TelegramNotifier(self.telegram_service)
        self.telegram_bot = TelegramBot()
        self.telegram_bot.router = CommandRouter()
        self.telegram_bot.router.register(TelegramCommand.STATUS, lambda msg: status_handler(msg))
        self.telegram_bot.router.register(TelegramCommand.POSITIONS, lambda msg: positions_handler(msg))
        self.telegram_bot.router.register(TelegramCommand.PORTFOLIO, lambda msg: portfolio_handler(msg))
        self.telegram_bot.router.register(TelegramCommand.HELP, lambda msg: help_handler(msg))
        self.telegram_bot.router.register(TelegramCommand.LAST_SIGNAL, lambda msg: last_signal_handler(msg))

        self.notification_dispatcher = NotificationDispatcher(self.telegram_notifier)
        self.notification_dispatcher.register(OrderExecutedEvent, OrderExecutedFormatter())
        self.notification_dispatcher.register(PositionOpenedEvent, PositionOpenedFormatter())
        self.notification_dispatcher.register(PositionClosedEvent, PositionClosedFormatter())
        self.notification_dispatcher.register(PortfolioUpdatedEvent, PortfolioUpdatedFormatter())

        self.pipeline_runner = PipelineRunner(
            collector=BinanceCollector(),
            indicator_engine=IndicatorEngine(),
        )

        self.scheduler = SimpleScheduler(self.pipeline_runner, interval_seconds=14400)

        self.runtime_monitor = RuntimeMonitor()
        self.health_monitor = HealthMonitor()
        self.metrics_collector = MetricsCollector()