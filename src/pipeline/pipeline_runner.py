"""Pipeline Runner — orchestration satu siklus analisis pasar."""

from datetime import UTC, datetime

from src.core.models.analysis_result import AnalysisResult as PipelineResult
from src.core.types.enums import PipelineStatus
from src.logging.logger import get_logger

logger = get_logger("pipeline.runner")


class PipelineRunner:
    def __init__(
        self,
        collector=None,
        indicator_engine=None,
        analysis_engine=None,
        decision_engine=None,
        validation_engine=None,
        risk_engine=None,
        signal_engine=None,
        notification_engine=None,
        paper_trading_engine=None,
        health_monitor=None,
        price_provider=None,
        lifecycle_engine=None,
    ):
        self.collector = collector
        self.indicator_engine = indicator_engine
        self.analysis_engine = analysis_engine
        self.decision_engine = decision_engine
        self.validation_engine = validation_engine
        self.risk_engine = risk_engine
        self.signal_engine = signal_engine
        self.notification_engine = notification_engine
        self.paper_trading_engine = paper_trading_engine
        self.health_monitor = health_monitor
        self.price_provider = price_provider
        self.lifecycle_engine = lifecycle_engine

        # Runtime state untuk Telegram
        self.last_pipeline_status = "IDLE"
        self.last_pipeline_started_at: datetime | None = None
        self.last_pipeline_completed_at: datetime | None = None
        self.last_pipeline_error: str | None = None
        self.last_signal = None
        self.last_market_snapshot = None

    async def run(self, symbol: str, timeframe: str = "4h") -> PipelineResult:
        logger.info(f"Pipeline started for {symbol} ({timeframe})")

        # Update status
        self.last_pipeline_status = "RUNNING"
        self.last_pipeline_started_at = datetime.now(UTC)
        self._record_pipeline_status(PipelineStatus.RUNNING)

        signal = None

        # Step 1 — Collect
        try:
            logger.info("Collecting market data...")
            if self.collector:
                snapshot = await self.collector.collect(symbol, timeframe)
                self.last_market_snapshot = snapshot
    
                if self.price_provider and snapshot:
                    self.price_provider.update_price(symbol, snapshot.current_price)
                logger.info("MarketSnapshot created")
                if self.lifecycle_engine and snapshot:
                    await self._evaluate_positions(symbol, snapshot.current_price)
            else:
                snapshot = None
        except Exception as e:
            logger.error(f"Collector failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 2 — Indicators
        try:
            if self.indicator_engine and snapshot:
                logger.info("Calculating indicators...")
                indicators = self.indicator_engine.calculate(snapshot)
                logger.info("IndicatorResult created")
            else:
                indicators = None
        except Exception as e:
            logger.error(f"Indicator calculation failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 3 — Analysis
        try:
            if self.analysis_engine and indicators:
                logger.info("Running market analysis...")
                analysis = self.analysis_engine.analyze(indicators)
                logger.info("AnalysisResult created")
            else:
                analysis = None
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 4 — AI Decision
        try:
            if self.decision_engine and analysis:
                logger.info("Running AI decision...")
                decision = await self.decision_engine.decide(analysis)
                logger.info("DecisionResult created")
            else:
                decision = None
        except Exception as e:
            logger.error(f"AI decision failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 5 — Validation
        try:
            if self.validation_engine and decision:
                logger.info("Running validation...")
                validated = self.validation_engine.validate(decision)
                logger.info("Validation complete")
            else:
                validated = None
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 6 — Risk
        try:
            if self.risk_engine and validated and indicators:
                logger.info("Running risk calculation...")
                entry = snapshot.current_price if snapshot else 0
                atr = indicators.atr14 or 0
                trade_plan = self.risk_engine.calculate(validated, entry, atr)
                logger.info("TradePlan created")
            else:
                trade_plan = None
        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 7 — Signal
        try:
            if self.signal_engine and trade_plan:
                logger.info("Generating trading signal...")
                signal = self.signal_engine.generate(trade_plan)

                # Pertahankan confidence dari DecisionResult
                if decision is not None:
                    signal.confidence = getattr(decision, "confidence", 0)

                self.last_signal = signal
                logger.info("TradingSignal created")
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 8 — Paper Execution (if enabled)
        if self.paper_trading_engine and signal and getattr(signal, "status", None) == "ACTIVE":
            try:
                logger.info("Executing paper trade...")
                _ = self.paper_trading_engine.execute(signal)
                logger.info("Paper trade executed")
            except Exception as e:
                logger.error(f"Paper execution failed: {e}")

        # Notification
        if self.notification_engine and signal:
            try:
                self.notification_engine.notify_signal(signal)
            except Exception as e:
                logger.error(f"Notification failed: {e}")

        logger.info(f"Pipeline finished for {symbol}")

        # Success
        self.last_pipeline_status = "COMPLETED"
        self.last_pipeline_completed_at = datetime.now(UTC)
        self._record_pipeline_status(PipelineStatus.COMPLETED)

        return PipelineResult(
            symbol=symbol,
            timeframe=timeframe,
            status="completed",
            timestamp=datetime.now(UTC),
        )

    def _set_failed(self, error: str) -> None:
        self.last_pipeline_status = "FAILED"
        self.last_pipeline_error = error
        self.last_pipeline_completed_at = datetime.now(UTC)
        self._record_pipeline_status(PipelineStatus.FAILED)

    def _record_pipeline_status(self, status: PipelineStatus) -> None:
        if self.health_monitor:
            try:
                self.health_monitor.record_pipeline_status(status)
            except Exception:
                pass

    async def _evaluate_positions(self, symbol: str, current_price: float) -> None:
        """Evaluasi TP/SL untuk posisi open terkait symbol."""
        if not self.paper_trading_engine or not self.lifecycle_engine:
            return

        portfolio = getattr(self.paper_trading_engine, "portfolio_manager", None)
        if not portfolio:
            return

        positions = portfolio.get_open_positions()
        for pos in positions:
            if pos.symbol != symbol:
                continue

            action, fraction = self.lifecycle_engine.evaluate(pos, current_price)
            if action != "HOLD":
                logger.info(f"Lifecycle action={action} for {pos.symbol} {pos.side}")
                self.paper_trading_engine.apply_lifecycle_action(
                    pos.position_id, action, current_price, fraction
                )        