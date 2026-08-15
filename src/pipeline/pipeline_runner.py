"""Pipeline Runner — orchestration satu siklus analisis pasar."""

from datetime import UTC, datetime

from src.core.models.analysis_result import AnalysisResult as PipelineResult
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

        # State untuk Telegram UX
        self.last_signal = None
        self.last_market_snapshot = None

    async def run(self, symbol: str, timeframe: str = "4h") -> PipelineResult:
        logger.info(f"Pipeline started for {symbol} ({timeframe})")

        signal = None

        # Step 1 — Collect
        try:
            logger.info("Collecting market data...")
            if self.collector:
                snapshot = await self.collector.collect(symbol, timeframe)
                self.last_market_snapshot = snapshot
                logger.info("MarketSnapshot created")
            else:
                snapshot = None
        except Exception as e:
            logger.error(f"Collector failed: {e}")
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
                self.last_signal = signal
                logger.info("TradingSignal created")
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 8 — Paper Execution (if enabled)
        if self.paper_trading_engine and signal and signal.status == "ACTIVE":
            try:
                logger.info("Executing paper trade...")
                _ = self.paper_trading_engine.execute(signal)
                logger.info("Paper trade executed")
            except Exception as e:
                logger.error(f"Paper execution failed: {e}")

        # Notification (side effect — tidak mempengaruhi status pipeline)
        if self.notification_engine and signal:
            try:
                self.notification_engine.notify_signal(signal)
            except Exception as e:
                logger.error(f"Notification failed: {e}")

        logger.info(f"Pipeline finished for {symbol}")
        return PipelineResult(
            symbol=symbol,
            timeframe=timeframe,
            status="completed",
            timestamp=datetime.now(UTC),
        )