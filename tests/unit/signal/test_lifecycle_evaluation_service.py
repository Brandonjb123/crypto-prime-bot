"""Tests untuk LifecycleEvaluationService."""

import asyncio

from src.signal.lifecycle_evaluation_service import LifecycleEvaluationService


class _FakeEvaluator:
    def __init__(self) -> None:
        self.call_count = 0
        self.raise_on_call: int | None = None

    def evaluate_once(self):
        self.call_count += 1
        if self.raise_on_call is not None and self.call_count == self.raise_on_call:
            raise RuntimeError("simulated evaluator failure")
        return []


class TestLifecycleEvaluationService:
    async def test_start_creates_one_task(self):
        evaluator = _FakeEvaluator()
        service = LifecycleEvaluationService(evaluator, interval_seconds=0.01)

        service.start()
        assert service._task is not None
        await service.stop()

    async def test_start_twice_does_not_create_two_tasks(self):
        evaluator = _FakeEvaluator()
        service = LifecycleEvaluationService(evaluator, interval_seconds=0.01)

        service.start()
        first_task = service._task
        service.start()
        assert service._task is first_task

        await service.stop()

    async def test_stop_cancels_cleanly(self):
        evaluator = _FakeEvaluator()
        service = LifecycleEvaluationService(evaluator, interval_seconds=0.01)

        service.start()
        await asyncio.sleep(0.02)
        await service.stop()
        assert service._task is None

    async def test_evaluator_called_per_interval(self):
        evaluator = _FakeEvaluator()
        service = LifecycleEvaluationService(evaluator, interval_seconds=0.02)

        service.start()
        await asyncio.sleep(0.07)
        await service.stop()

        # Minimal 3 calls (first immediate + 2 interval ticks)
        assert evaluator.call_count >= 3

    async def test_evaluator_exception_does_not_kill_loop(self):
        evaluator = _FakeEvaluator()
        evaluator.raise_on_call = 1  # raise on first call
        service = LifecycleEvaluationService(evaluator, interval_seconds=0.02)

        service.start()
        await asyncio.sleep(0.08)
        await service.stop()

        # Loop survived — evaluator called multiple times
        assert evaluator.call_count >= 3

    async def test_stop_when_never_started(self):
        evaluator = _FakeEvaluator()
        service = LifecycleEvaluationService(evaluator, interval_seconds=0.01)

        # Tidak crash meski task None
        await service.stop()
        assert service._task is None