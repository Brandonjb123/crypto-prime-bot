"""Pipeline Runner — orchestration satu siklus analisis pasar."""

from datetime import UTC, datetime

from src.core.models.analysis_result import AnalysisResult
from src.logging.logger import get_logger

logger = get_logger("pipeline")


class PipelineRunner:
    def __init__(self, collector=None, analysis_engine=None):
        self.collector = collector
        self.analysis_engine = analysis_engine

    async def run(self, symbol: str, timeframe: str = "4h") -> AnalysisResult:
        logger.info(f"Pipeline started for {symbol} ({timeframe})")

        # Step 1 — Collect market data
        try:
            logger.info("Collecting market data...")
            if self.collector:
                snapshot = await self.collector.collect(symbol, timeframe)
                logger.info("Market snapshot collected")
            else:
                snapshot = None
                logger.warning("No collector configured — skipping")
        except Exception as e:
            logger.error(f"Collector failed: {e}")
            return AnalysisResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 2 — Run analysis
        try:
            logger.info("Running analysis...")
            if self.analysis_engine:
                await self.analysis_engine.analyze(snapshot)
                logger.info("Analysis completed")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AnalysisResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        logger.info(f"Pipeline finished for {symbol}")
        return AnalysisResult(
            symbol=symbol,
            timeframe=timeframe,
            status="completed",
            timestamp=datetime.now(UTC),
        )