"""Regression test — single InMemoryPriceProvider instance identity (C0.0.3).

Memverifikasi bahwa Container hanya construct InMemoryPriceProvider SEKALI,
dan semua consumer (PriceRefreshService via container, ActionabilityEvaluator,
PortfolioStateManager, PipelineRunner) share instance yang SAMA.
"""

from src.bootstrap.container import Container


def test_container_has_single_price_provider_instance():
    """ActionabilityEvaluator harus pegang instance yang sama dengan container."""
    c = Container()

    assert c.actionability_evaluator.price_provider is c.price_provider


def test_price_provider_shared_across_consumers():
    """Semua consumer harus share instance yang sama (identity check)."""
    c = Container()

    # PortfolioStateManager
    assert c.portfolio_state_manager.price_provider is c.price_provider
    # PipelineRunner
    assert c.pipeline_runner.price_provider is c.price_provider
    # ActionabilityEvaluator
    assert c.actionability_evaluator.price_provider is c.price_provider


def test_container_price_provider_construct_count():
    """Guard against future duplicate construction regression."""
    import inspect

    import src.bootstrap.container as container_module

    src = inspect.getsource(container_module)
    # Hitung kemunculan literal `InMemoryPriceProvider()`
    occurrences = src.count("InMemoryPriceProvider()")
    assert occurrences == 1, (
        f"Expected exactly 1 InMemoryPriceProvider() construction, "
        f"found {occurrences}"
    )