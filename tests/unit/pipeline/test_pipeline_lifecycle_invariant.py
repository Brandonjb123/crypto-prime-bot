"""Regression test — ACTIVE signal must NOT execute without lifecycle (C0.0.2)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.core.models.trade_plan import TradePlan
from src.pipeline.pipeline_runner import PipelineRunner


def _make_trade_plan(decision="BUY"):
    return TradePlan(
        symbol="BTC",
        decision=decision,
        entry_price=100.0,
        position_size=0.01,
        risk_percent=2.0,
        account_balance=1000.0,
        stop_loss=85.0,
        take_profit=145.0,
        take_profit_1=122.5,
        take_profit_2=145.0,
        risk_reward_ratio=3.0,
        estimated_loss=15.0,
        estimated_profit=45.0,
        atr_stop_loss=15.0,
        atr_take_profit=45.0,
        timestamp=datetime.now(UTC),
    )


def _make_snapshot():
    snap = MagicMock()
    snap.current_price = 100.0
    snap.symbol = "BTC"
    snap.timeframe = "4h"
    snap.candles = []
    return snap


def _make_indicators():
    ind = MagicMock()
    ind.atr14 = 10.0
    return ind


def _make_decision():
    dec = MagicMock()
    dec.confidence = 80
    dec.reasoning = ["test"]
    dec.risk_level = "MEDIUM"
    return dec


def _make_validated():
    v = MagicMock()
    v.decision = "BUY"
    v.symbol = "BTC"
    return v


@pytest.mark.asyncio
async def test_active_without_lifecycle_repo_fails_fast():
    """ACTIVE signal + lifecycle_repository=None → fail-fast, no paper execution."""
    collector = MagicMock()
    collector.collect = AsyncMock(return_value=_make_snapshot())

    indicator_engine = MagicMock()
    indicator_engine.calculate = MagicMock(return_value=_make_indicators())

    analysis_engine = MagicMock()
    analysis_engine.analyze = MagicMock(return_value=MagicMock())

    decision_engine = MagicMock()
    decision_engine.decide = AsyncMock(return_value=_make_decision())

    validation_engine = MagicMock()
    validation_engine.validate = MagicMock(return_value=_make_validated())

    risk_engine = MagicMock()
    risk_engine.calculate = MagicMock(return_value=_make_trade_plan())

    signal_engine = MagicMock()
    active_signal = MagicMock()
    active_signal.status = "ACTIVE"
    active_signal.signal_id = uuid4()
    active_signal.symbol = "BTC"
    active_signal.created_at = datetime.now(UTC)
    signal_engine.generate = MagicMock(return_value=active_signal)

    signal_repo = MagicMock()
    paper_engine = MagicMock()
    paper_engine.execute = MagicMock()

    runner = PipelineRunner(
        collector=collector,
        indicator_engine=indicator_engine,
        analysis_engine=analysis_engine,
        decision_engine=decision_engine,
        validation_engine=validation_engine,
        risk_engine=risk_engine,
        signal_engine=signal_engine,
        paper_trading_engine=paper_engine,
        signal_repository=signal_repo,
        lifecycle_repository=None,   # ← intentionally None
    )

    result = await runner.run("BTC", "4h")

    assert result.status == "failed"
    assert "lifecycle_repository" in (result.error_message or "")
    paper_engine.execute.assert_not_called()


@pytest.mark.asyncio
async def test_active_without_valid_zone_fails_fast():
    """ACTIVE + zone invalid (ATR=0) → fail-fast, no paper execution."""
    collector = MagicMock()
    collector.collect = AsyncMock(return_value=_make_snapshot())

    indicator_engine = MagicMock()
    ind = _make_indicators()
    ind.atr14 = 0.0   # ← ATR=0 → zone None
    indicator_engine.calculate = MagicMock(return_value=ind)

    analysis_engine = MagicMock()
    analysis_engine.analyze = MagicMock(return_value=MagicMock())

    decision_engine = MagicMock()
    decision_engine.decide = AsyncMock(return_value=_make_decision())

    validation_engine = MagicMock()
    validation_engine.validate = MagicMock(return_value=_make_validated())

    risk_engine = MagicMock()
    risk_engine.calculate = MagicMock(return_value=_make_trade_plan())

    signal_engine = MagicMock()
    active_signal = MagicMock()
    active_signal.status = "ACTIVE"
    active_signal.signal_id = uuid4()
    active_signal.symbol = "BTC"
    active_signal.created_at = datetime.now(UTC)
    signal_engine.generate = MagicMock(return_value=active_signal)

    signal_repo = MagicMock()
    lifecycle_repo = MagicMock()
    paper_engine = MagicMock()
    paper_engine.execute = MagicMock()

    runner = PipelineRunner(
        collector=collector,
        indicator_engine=indicator_engine,
        analysis_engine=analysis_engine,
        decision_engine=decision_engine,
        validation_engine=validation_engine,
        risk_engine=risk_engine,
        signal_engine=signal_engine,
        paper_trading_engine=paper_engine,
        signal_repository=signal_repo,
        lifecycle_repository=lifecycle_repo,
    )

    result = await runner.run("BTC", "4h")

    assert result.status == "failed"
    assert "zone" in (result.error_message or "").lower()
    paper_engine.execute.assert_not_called()
    lifecycle_repo.create_with_supersede.assert_not_called()