import asyncio
import time


class RateLimiter:
    """Simple async rate limiter."""

    def __init__(self, max_calls: int, period: float = 1.0):
        self.max_calls = max_calls
        self.period = period
        self.calls: list[float] = []

    async def acquire(self) -> None:
        """Tunggu hingga slot tersedia."""
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]

        if len(self.calls) >= self.max_calls:
            wait_time = self.calls[0] + self.period - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.calls.append(time.time())