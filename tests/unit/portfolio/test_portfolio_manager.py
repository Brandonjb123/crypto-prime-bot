from uuid import uuid4
from datetime import datetime, UTC
import pytest
from src.core.models.portfolio import PortfolioSnapshot
from src.core.models.position import Position
from src.core.types.enums import (
    PositionCloseReason, PositionStatus, PortfolioStatus, Side, RiskWarning
)
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
        close_reason=PositionCloseReason.NONE if status == PositionStatus.OPEN else PositionCloseReason.MANUAL,
    )


class TestPortfolioManager:
    def pm(self):
        return PortfolioManager()

    def test_empty_portfolio(self):
        snap = self.pm().create_snapshot([], 10000.0)
        assert snap.status == PortfolioStatus.EMPTY
        assert snap.open_positions == 0
        assert snap.total_positions == 0
        assert snap.equity == 10000.0

    def test_active_portfolio(self):
        positions = [_make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN, 0.1)]
        snap = self.pm().create_snapshot(positions, 10000.0)
        assert snap.status == PortfolioStatus.ACTIVE
        assert snap.open_positions == 1
        assert snap.total_positions == 1

    def test_risk_limit_portfolio(self):
        positions = [_make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN, 350.0)]
        snap = self.pm().create_snapshot(positions, 10000.0)
        assert snap.status == PortfolioStatus.RISK_LIMIT
        assert RiskWarning.POSITION_SIZE_CAPPED in snap.warnings

    def test_gross_exposure(self):
        positions = [
            _make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN, 0.1),
            _make_position("ETH/USDT", Side.LONG, PositionStatus.OPEN, 0.2),
        ]
        snap = self.pm().create_snapshot(positions, 10000.0)
        assert snap.gross_exposure == pytest.approx(0.3)

    def test_net_exposure(self):
        positions = [
            _make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN, 0.5),
            _make_position("ETH/USDT", Side.SHORT, PositionStatus.OPEN, 0.2),
        ]
        snap = self.pm().create_snapshot(positions, 10000.0)
        assert snap.net_exposure == 0.3  # 0.5 - 0.2

    def test_equity_calculation(self):
        positions = [_make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN, 0.1)]
        snap = self.pm().create_snapshot(positions, 10000.0)
        assert snap.equity == 10000.0  # balance + 0 realized + 0 unrealized

    def test_long_count(self):
        positions = [
            _make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN),
            _make_position("ETH/USDT", Side.LONG, PositionStatus.OPEN),
            _make_position("SOL/USDT", Side.SHORT, PositionStatus.OPEN),
        ]
        snap = self.pm().create_snapshot(positions, 10000.0)
        assert snap.long_positions == 2
        assert snap.short_positions == 1

    def test_open_closed_count(self):
        positions = [
            _make_position("BTC/USDT", Side.LONG, PositionStatus.OPEN),
            _make_position("ETH/USDT", Side.LONG, PositionStatus.CLOSED),
            _make_position("SOL/USDT", Side.SHORT, PositionStatus.CLOSED),
        ]
        snap = self.pm().create_snapshot(positions, 10000.0)
        assert snap.open_positions == 1
        assert snap.closed_positions == 2
        assert snap.total_positions == 3

    def test_immutable_snapshot(self):
        from pydantic import ValidationError
        snap = self.pm().create_snapshot([], 10000.0)
        with pytest.raises(ValidationError):
            snap.status = PortfolioStatus.ACTIVE

    def test_deterministic(self):
        positions = [_make_position()]
        pm1 = PortfolioManager()
        pm2 = PortfolioManager()
        s1 = pm1.create_snapshot(positions, 10000.0)
        s2 = pm2.create_snapshot(positions, 10000.0)
        assert s1.status == s2.status
        assert s1.gross_exposure == s2.gross_exposure
        assert s1.net_exposure == s2.net_exposure