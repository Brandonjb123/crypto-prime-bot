"""LifecycleEvaluationService — background loop host untuk ActionabilityEvaluator.

Cadence ~60s, terpisah dari PriceRefreshService.
"""

import asyncio

from loguru import logger

from src.signal.actionability_evaluator import ActionabilityEvaluator


class LifecycleEvaluationService:
    def __init__(
        self,
        evaluator: ActionabilityEvaluator,
        interval_seconds: int = 60,
    ) -> None:
        self.evaluator = evaluator
        self.interval = interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        """Idempotent — panggilan kedua tidak membuat task baru."""
        if self._task is not None and not self._task.done():
            logger.debug("[lifecycle_eval] service already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"[lifecycle_eval] background task started (interval={self.interval}s)"
        )

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"[lifecycle_eval] task raised on stop: {e}")
            finally:
                self._task = None
            logger.info("[lifecycle_eval] background task stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                self.evaluator.evaluate_once()
            except Exception as e:
                # Jangan biarkan exception kill loop
                logger.error(f"[lifecycle_eval] evaluate_once failed: {e}")
            try:
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                raise