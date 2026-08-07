"""Bootstrap — startup & shutdown sequence."""

import sys
from src.config.validator import validate_config
from src.bootstrap.container import Container


class Bootstrap:
    def __init__(self):
        self.container = Container()
        self.logger = self.container.logger

    def startup(self):
        self._step("Loading configuration", self._load_config)
        self._step("Validating configuration", validate_config)
        self._step("Initializing logger", self._init_logger)
        self._step("Initializing Event Bus", self._init_event_bus)
        self._step("Initializing Notification Layer", self._init_notification)
        self._step("Initializing Telegram", self._init_telegram)
        self._step("Initializing Exchange", self._init_exchange)
        self._step("Initializing Pipeline", self._init_pipeline)
        self._step("Initializing Scheduler", self._init_scheduler)
        print("Crypto Prime Bot v2.0 started successfully.")

    def shutdown(self):
        self.logger.info("Shutting down...")
        self.container.scheduler.stop()
        self.container.telegram_service.stop()
        self.logger.info("Shutdown complete.")

    def _step(self, msg, fn):
        print(msg, end="... ")
        try:
            fn()
            print("✓")
        except Exception as e:
            print(f"✗ ({e})")
            sys.exit(1)

    def _load_config(self):
        from config.settings import settings
        pass  # Already loaded by import

    def _init_logger(self):
        self.logger.info("Logger initialized")

    def _init_event_bus(self):
        self.container.event_bus

    def _init_notification(self):
        self.container.notification_dispatcher

    def _init_telegram(self):
        self.container.telegram_service

    def _init_exchange(self):
        self.container.paper_exchange

    def _init_pipeline(self):
        self.container.orchestrator

    def _init_scheduler(self):
        self.container.scheduler