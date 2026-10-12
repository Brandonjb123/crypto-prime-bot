"""Assert 4 display paths only invoke read-only lifecycle methods (H3.2 B3).

This test uses a strict probe repo that raises AssertionError on any
attribute access other than `get_lifecycle_lookup`. If the resolver or
any handler tries to touch `mark_expired`, `create_with_supersede`, or
any write method, the test fails.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.core.models.lifecycle_lookup import LifecycleLookupResult
from src.telegram.bot import TelegramBot
from src.telegram.command_handler import last_signal_handler, signals_handler


class _SignalRepo:
    """Signal repo double — read-only methods only."""

    def __init__(self, signals=None):
        self._signals = signals or []

    def history(self, **kw):
        return list(self._signals)

    def latest_by_symbol(self, symbol):
        for s in self._signals:
            if s.symbol == symbol:
                return s
        return None


class _StrictReadOnlyLifecycleProbe:
    """Lifecycle repo probe that fails on any write-method access.

    Only `get_lifecycle_lookup` is allowed. Anything else — including
    `mark_expired` and `create_with_supersede` — raises immediately.
    """

    def __init__(self, absent_ids=None):
        self.calls: list[str] = []
        self._absent = set(absent_ids or [])

    def get_lifecycle_lookup(self, signal_ids):
        self.calls.append("get_lifecycle_lookup")
        return LifecycleLookupResult(absent=set(signal_ids))

    # Explicit write methods — must never be touched by display
    def mark_expired(self, *a, **kw):
        self.calls.append("mark_expired")
        raise AssertionError("display must not call mark_expired")

    def create_with_supersede(self, *a, **kw):
        self.calls.append("create_with_supersede")
        raise AssertionError("display must not call create_with_supersede")

    def append(self, *a, **kw):
        self.calls.append("append")
        raise AssertionError("display must not call append")

    def save(self, *a, **kw):
        self.calls.append("save")
        raise AssertionError("display must not call save")

    def execute(self, *a, **kw):
        self.calls.append("execute")
        raise AssertionError("display must not call execute")

    def __getattr__(self, name):
        # Any other attribute access is forbidden.
        raise AssertionError(
            f"display touched unexpected lifecycle attribute: {name}"
        )


def _assert_only_read(probe: _StrictReadOnlyLifecycleProbe):
    for call in probe.calls:
        assert call == "get_lifecycle_lookup", (
            f"unexpected lifecycle method called: {call}"
        )


def _sig(symbol="BTC", status="ACTIVE"):
    s = MagicMock()
    s.signal_id = uuid4()
    s.symbol = symbol
    s.side = "BUY"
    s.status = status
    s.entry_price = 100.0
    s.stop_loss = 95.0
    s.take_profit = 110.0
    s.confidence = 80
    s.risk_level = "MEDIUM"
    s.position_size = 1.0
    s.reasoning = []
    s.created_at = datetime.now(UTC)
    return s


def test_lastsignal_handler_read_only():
    s = _sig()
    sig_repo = _SignalRepo([s])
    lc_repo = _StrictReadOnlyLifecycleProbe()
    resp = last_signal_handler(
        None,
        {
            "signal_repository": sig_repo,
            "signal_lifecycle_repository": lc_repo,
        },
    )
    assert resp is not None
    _assert_only_read(lc_repo)


def test_signals_handler_read_only():
    s = _sig("BTC")
    sig_repo = _SignalRepo([s])
    lc_repo = _StrictReadOnlyLifecycleProbe()
    resp = signals_handler(
        None,
        {
            "signal_repository": sig_repo,
            "signal_lifecycle_repository": lc_repo,
        },
    )
    assert resp is not None
    _assert_only_read(lc_repo)


@pytest.mark.asyncio
async def test_callback_view_signals_read_only():
    sig = _sig()
    bot = TelegramBot()
    runtime = MagicMock()
    runtime.get_context.return_value = {
        "positions": [],
        "closed_positions": [],
        "portfolio_snapshot": None,
    }
    runtime.price_provider = object()
    bot.set_runtime_provider(runtime)

    sig_repo = _SignalRepo([sig])
    lc_repo = _StrictReadOnlyLifecycleProbe()
    bot.set_signal_repository(sig_repo)
    bot.set_signal_lifecycle_repository(lc_repo)
    bot.set_context(
        {
            "positions": [],
            "closed_positions": [],
            "portfolio_snapshot": None,
            "signal_repository": sig_repo,
            "signal_lifecycle_repository": lc_repo,
        }
    )

    bot._view_signals()
    _assert_only_read(lc_repo)


def test_callback_view_last_signal_read_only():
    sig = _sig()
    bot = TelegramBot()
    runtime = MagicMock()
    runtime.get_context.return_value = {
        "positions": [],
        "closed_positions": [],
        "portfolio_snapshot": None,
    }
    runtime.price_provider = object()
    bot.set_runtime_provider(runtime)

    sig_repo = _SignalRepo([sig])
    lc_repo = _StrictReadOnlyLifecycleProbe()
    bot.set_signal_repository(sig_repo)
    bot.set_signal_lifecycle_repository(lc_repo)
    bot.set_context(
        {
            "positions": [],
            "closed_positions": [],
            "portfolio_snapshot": None,
            "signal_repository": sig_repo,
            "signal_lifecycle_repository": lc_repo,
        }
    )

    bot._view_last_signal()
    _assert_only_read(lc_repo)