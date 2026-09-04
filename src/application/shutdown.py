"""Graceful Shutdown Handler."""

from collections.abc import Callable
from inspect import iscoroutinefunction


class ShutdownHandler:
    def __init__(self) -> None:
        self._hooks: list[Callable] = []

    def register(self, hook: Callable) -> None:
        self._hooks.append(hook)

    async def shutdown(self) -> None:
        for hook in reversed(self._hooks):
            if iscoroutinefunction(hook):
                await hook()
            else:
                hook()
