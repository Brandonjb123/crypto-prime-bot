from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.models.account import AccountSnapshot
from src.core.models.position import Position
from src.core.types.enums import (
    PortfolioStatus,
    PositionCloseReason,
    PositionStatus,
    RiskWarning,
    Side,
)
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.portfolio.portfolio_manager import PortfolioManager


def _make_position(symbol="BTC/USDT", side=Side.LONG, status=PositionStatus.OPEN, size=0.1):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol=symbol,
        side=side,
        status=status,
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0,
        position_size=size,
        opened_at=datetime.now(UTC),
        closed_at=None if status == PositionStatus.OPEN else datetime.now(UTC),
        close_reason=PositionCloseReason.NONE
        if status == PositionStatus.OPEN
        else PositionCloseReason.MANUAL,
    )


def _make_account(balance=10000.0):
    return AccountSnapshot(
        balance=balance,
        equity=balance,
        margin_used=0.0,
        free_margin=balance,
        timestamp=datetime.now(UTC),
    )


def _make_provider(symbol="BTC/USDT", price=50000.0):
    p = InMemoryPriceProvider()
    p.update_price(symbol, price)
    return p


class TestPortfolioManager:
    def pm(self):
        return PortfolioManager()

    def test_empty_portfolio(self):
        account = _make_account()
        provider = _make_provider()
        snap = self.pm().create_snapshot([], account, provider)
        assert snap.status == PortfolioStatus.EMPTY
        assert snap.open_positions == 0
        assert snap.total_positions == 0
        assert snap.equity == 10000.0

    def test_active_portfolio(self):
        positions = [_make_position()]
        account = _make_account()
        provider = _make_provider()
        snap = self.pm().create_snapshot(positions, account, provider)
        assert snap.status == PortfolioStatus.ACTIVE
        assert snap.open_positions == 1
        assert snap.total_positions == 1

    def test_risk_limit_portfolio(self):
        positions = [_make_position(size=350.0)]
        account = _make_account()
        provider = _make_provider()
        snap = self.pm().create_snapshot(positions, account, provider)
        assert snap.status == PortfolioStatus.RISK_LIMIT
        assert RiskWarning.POSITION_SIZE_CAPPED in snap.warnings

    def test_gross_exposure(self):
        positions = [
            _make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN, 0.1),
            _make_position("ETH/USDT", Side.LONG, PositionStatus.OPEN, 0.2),
        ]
        account = _make_account()
        provider = _make_provider()
        snap = self.pm().create_snapshot(positions, account, provider)
        assert snap.gross_exposure == pytest.approx(0.3)

    def test_net_exposure(self):
        positions = [
            _make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN, 0.5),
            _make_position("ETH/USDT", Side.SHORT, PositionStatus.OPEN, 0.2),
        ]
        account = _make_account()
        provider = _make_provider()
        snap = self.pm().create_snapshot(positions, account, provider)
        assert snap.net_exposure == 0.3  # 0.5 - 0.2

    def test_equity_calculation(self):
        positions = [_make_position(size=0.1)]
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 51000.0)  # harga naik → unrealized PnL
        account = _make_account()
        snap = self.pm().create_snapshot(positions, account, provider)
        # unrealized = (51000-50000)*0.1 = 100, equity = 10000 + 0 + 100 = 10100
        assert snap.unrealized_pnl == 100.0
        assert snap.equity == 10100.0

    def test_long_count(self):
        positions = [
            _make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN),
            _make_position("ETH/USDT", Side.LONG, PositionStatus.OPEN),
            _make_position("SOL/USDT", Side.SHORT, PositionStatus.OPEN),
        ]
        account = _make_account()
        provider = _make_provider()
        snap = self.pm().create_snapshot(positions, account, provider)
        assert snap.long_positions == 2
        assert snap.short_positions == 1

    def test_open_closed_count(self):
        positions = [
            _make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN),
            _make_position("ETH/USDT", Side.LONG, PositionStatus.CLOSED),
            _make_position("SOL/USDT", Side.SHORT, PositionStatus.CLOSED),
        ]
        account = _make_account()
        provider = _make_provider()
        snap = self.pm().create_snapshot(positions, account, provider)
        assert snap.open_positions == 1
        assert snap.closed_positions == 2
        assert snap.total_positions == 3

    def test_immutable_snapshot(self):
        from pydantic import ValidationError

        account = _make_account()
        provider = _make_provider()
        snap = self.pm().create_snapshot([], account, provider)
        with pytest.raises(ValidationError):
            snap.status = PortfolioStatus.ACTIVE

    def test_deterministic(self):
        positions = [_make_position()]
        account = _make_account()
        provider = _make_provider()
        pm1 = PortfolioManager()
        pm2 = PortfolioManager()
        s1 = pm1.create_snapshot(positions, account, provider)
        s2 = pm2.create_snapshot(positions, account, provider)
        assert s1.status == s2.status
        assert s1.gross_exposure == s2.gross_exposure
        assert s1.net_exposure == s2.net_exposure
