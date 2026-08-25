"""Dependency Injection Container — assembles all services."""

from config.constants import TELEGRAM_BOT_TOKEN
from config.settings import settings
from src.ai.decision_engine import DecisionEngine
from src.ai.prompt_builder import PromptBuilder
from src.ai.provider_factory import create_llm_client
from src.analysis.analysis_engine import AnalysisEngine
from src.analysis.indicator_engine import IndicatorEngine
from src.application.scheduler import SimpleScheduler
from src.collectors.binance_collector import BinanceCollector
from src.core.types.enums import TelegramCommand
from src.events.event_bus import EventBus
from src.events.events.order_executed import OrderExecutedEvent
from src.events.events.portfolio_updated import PortfolioUpdatedEvent
from src.events.events.position_closed import PositionClosedEvent
from src.events.events.position_opened import PositionOpenedEvent
from src.exchange.adapters.binance.binance_futures_adapter import BinanceFuturesAdapter
from src.exchange.adapters.binance.client import BinanceClient
from src.exchange.adapters.paper import PaperExchangeAdapter
from src.exchange.executor import OrderExecutor
from src.execution.exchange.mock_client import MockExchangeClient
from src.execution.execution_router import ExecutionRouter
from src.execution.live_trading_engine import LiveTradingEngine
from src.execution.paper_trading_engine import PaperTradingEngine
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
from src.notification.notification_engine import NotificationEngine
from src.pipeline.pipeline_runner import PipelineRunner
from src.portfolio.portfolio_manager import PortfolioManager
from src.portfolio.portfolio_state_manager import PortfolioStateManager
from src.position.position_manager import PositionManager
from src.risk.trade_risk_engine import TradeRiskEngine
from src.signal.signal_engine import SignalEngine
from src.storage.adapters.in_memory_execution_repository import InMemoryExecutionRepository
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
from src.validation.validation_engine import ValidationEngine


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
        self.portfolio_state_manager = PortfolioStateManager(
            initial_balance=10000.0,
            price_provider=self.price_provider,
        )
        self.lifecycle_engine = TradeLifecycleEngine()

        self.paper_exchange = PaperExchangeAdapter()
        self.order_executor = OrderExecutor(adapter=self.paper_exchange, event_bus=self.event_bus)

        self.telegram_service = TelegramService(token=TELEGRAM_BOT_TOKEN)
        self.telegram_notifier = TelegramNotifier(self.telegram_service)
        self.notification_engine = NotificationEngine(notifier=self.telegram_notifier)
        self.telegram_bot = TelegramBot()
        self.telegram_bot.router = CommandRouter()
        self.telegram_bot.router.register(TelegramCommand.STATUS, lambda msg, ctx=None: status_handler(msg, ctx))
        self.telegram_bot.router.register(TelegramCommand.POSITIONS, lambda msg, ctx=None: positions_handler(msg, ctx))
        self.telegram_bot.router.register(TelegramCommand.PORTFOLIO, lambda msg, ctx=None: portfolio_handler(msg, ctx))
        self.telegram_bot.router.register(TelegramCommand.HELP, lambda msg, ctx=None: help_handler(msg, ctx))
        self.telegram_bot.router.register(TelegramCommand.LAST_SIGNAL, lambda msg, ctx=None: last_signal_handler(msg, ctx))

        self.notification_dispatcher = NotificationDispatcher(self.telegram_notifier)
        self.notification_dispatcher.register(OrderExecutedEvent, OrderExecutedFormatter())
        self.notification_dispatcher.register(PositionOpenedEvent, PositionOpenedFormatter())
        self.notification_dispatcher.register(PositionClosedEvent, PositionClosedFormatter())
        self.notification_dispatcher.register(PortfolioUpdatedEvent, PortfolioUpdatedFormatter())

        client = create_llm_client()
        prompt_builder = PromptBuilder()
        decision_engine = DecisionEngine(client=client, prompt_builder=prompt_builder)

        execution_repo = InMemoryExecutionRepository()
        self.paper_trading_engine = PaperTradingEngine(
            portfolio_manager=self.portfolio_state_manager,
            execution_repo=execution_repo,
            notification_engine=self.notification_engine,
            slippage=0.0,
        )

        # Live trading engine (TESTNET only, default PAPER)
        trading_mode = getattr(settings, "TRADING_MODE", "PAPER").upper()
        live_enabled = getattr(settings, "LIVE_TRADING_ENABLED", False)
        exchange_env = getattr(settings, "EXCHANGE_ENV", "TESTNET").upper()

        if trading_mode == "LIVE" and live_enabled:
            if exchange_env == "TESTNET":
                live_client = BinanceClient(
                    api_key=getattr(settings, "EXCHANGE_API_KEY", ""),
                    api_secret=getattr(settings, "EXCHANGE_API_SECRET", ""),
                    testnet=True,
                )
                live_exchange = BinanceFuturesAdapter(live_client)
            else:
                self.logger.error("Production live trading is not allowed in Sprint 12B")
                live_exchange = MockExchangeClient(behavior="fill_immediately")
        else:
            live_exchange = MockExchangeClient(behavior="fill_immediately")

        self.live_trading_engine = LiveTradingEngine(exchange=live_exchange)

        # Execution Router — default PAPER
        self.execution_router = ExecutionRouter(
            paper_engine=self.paper_trading_engine,
            live_engine=self.live_trading_engine,
            settings=settings,
        )

        # Health monitor harus ada sebelum dipakai pipeline_runner
        self.health_monitor = HealthMonitor()
        self.lifecycle_engine = TradeLifecycleEngine()

        self.pipeline_runner = PipelineRunner(
            collector=BinanceCollector(),
            indicator_engine=IndicatorEngine(),
            analysis_engine=AnalysisEngine(),
            decision_engine=decision_engine,
            validation_engine=ValidationEngine(),
            risk_engine=TradeRiskEngine(),
            signal_engine=SignalEngine(),
            notification_engine=self.notification_engine,
            paper_trading_engine=self.paper_trading_engine,
            health_monitor=self.health_monitor,
            price_provider=self.price_provider,
            lifecycle_engine=self.lifecycle_engine,
        )

        self.scheduler = SimpleScheduler(self.pipeline_runner, interval_seconds=14400)

        self.runtime_monitor = RuntimeMonitor()
        self.metrics_collector = MetricsCollector()

        # Context untuk Telegram dashboard
        self.telegram_bot.set_context({
            "pipeline_runner": self.pipeline_runner,
            "health_monitor": self.health_monitor,
            "portfolio_state_manager": self.portfolio_state_manager,
        })