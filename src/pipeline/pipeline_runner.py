"""Pipeline Runner — orchestration satu siklus analisis pasar."""

from datetime import UTC, datetime

from src.core.models.analysis_result import AnalysisResult as PipelineResult
from src.logging.logger import get_logger

logger = get_logger("pipeline")


class PipelineRunner:
    def __init__(self, collector=None, indicator_engine=None, analysis_engine=None):
        self.collector = collector
        self.indicator_engine = indicator_engine
        self.analysis_engine = analysis_engine

    async def run(self, symbol: str, timeframe: str = "4h") -> PipelineResult:
        logger.info(f"Pipeline started for {symbol} ({timeframe})")

        # Step 1 — Collect
        try:
            logger.info("Collecting market data...")
            if self.collector:
                snapshot = await self.collector.collect(symbol, timeframe)
                logger.info("MarketSnapshot created")
            else:
                logger.warning("No collector configured — skipping")
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
                _ = self.analysis_engine.analyze(indicators)
                logger.info("AnalysisResult created")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        logger.info(f"Pipeline finished for {symbol}")
        return PipelineResult(
            symbol=symbol,
            timeframe=timeframe,
            status="completed",
            timestamp=datetime.now(UTC),
        )