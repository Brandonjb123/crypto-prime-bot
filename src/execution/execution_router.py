"""Execution Router — arahkan ke Paper atau Live engine."""

import inspect

from src.core.types.enums import TradingMode
from src.execution.base_execution_engine import BaseExecutionEngine


class ExecutionRouter:
    def __init__(
        self,
        paper_engine: BaseExecutionEngine,
        live_engine: BaseExecutionEngine,
        settings,
    ):
        self.paper = paper_engine
        self.live = live_engine
        self.settings = settings

    async def execute(self, signal):
        mode = self._get_mode()
        if mode == TradingMode.LIVE:
            return await self.live.execute(signal)

        result = self.paper.execute(signal)
        if inspect.iscoroutine(result):
            return await result
        return result

    async def cancel(self, execution_id: str):
        mode = self._get_mode()
        if mode == TradingMode.LIVE:
            return await self.live.cancel(execution_id)
        return await self.paper.cancel(execution_id)

    async def get_status(self, execution_id: str):
        mode = self._get_mode()
        if mode == TradingMode.LIVE:
            return await self.live.get_status(execution_id)
        return await self.paper.get_status(execution_id)

    def _get_mode(self) -> TradingMode:
        mode_str = getattr(self.settings, "TRADING_MODE", "PAPER").upper()
        if mode_str == "LIVE":
            if not getattr(self.settings, "LIVE_TRADING_ENABLED", False):
                raise RuntimeError(
                    "LIVE_TRADING_ENABLED is False — cannot use LIVE mode"
                )
            return TradingMode.LIVE
        if mode_str != "PAPER":
            raise ValueError(
                f"Invalid TRADING_MODE: {mode_str}. Must be PAPER or LIVE."
            )
        return TradingMode.PAPER