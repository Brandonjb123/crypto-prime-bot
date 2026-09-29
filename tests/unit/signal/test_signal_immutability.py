"""Test TradingSignal immutability."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.core.models.trading_signal import TradingSignal


def _make_signal():
    return TradingSignal(
        signal_id=uuid4(),
        symbol="BTC",
        side="BUY",
        status="ACTIVE",
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        created_at=datetime.now(UTC),
    )


def test_signal_immutable():
    sig = _make_signal()
    with pytest.raises((ValidationError, TypeError)):
        sig.confidence = 100


def test_signal_immutable_symbol():
    sig = _make_signal()
    with pytest.raises((ValidationError, TypeError)):
        sig.symbol = "ETH"