from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.portfolio import PortfolioSnapshot
from src.core.models.position import Position
from src.core.models.telegram import TelegramMessage
from src.core.types.enums import (
    PortfolioStatus,
    PositionCloseReason,
    PositionStatus,
    Side,
    TelegramCommand,
    TelegramResponseType,
)
from src.telegram.command_handler import (
    help_handler,
    portfolio_handler,
    positions_handler,
    status_handler,
)


def _make_position():
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol="BTCUSDT",
        side=Side.LONG,
        status=PositionStatus.OPEN,
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0,
        position_size=0.1,
        opened_at=datetime.now(UTC),
        closed_at=None,
        close_reason=PositionCloseReason.NONE,
    )


class TestCommandHandlers:
    def test_status_response(self):
        msg = TelegramMessage(
            chat_id="1", command=TelegramCommand.STATUS, timestamp=datetime.now(UTC)
        )
        resp = status_handler(msg, {"orchestrator_status": "RUNNING", "pipeline_status": "IDLE"})
        assert resp.response_type == TelegramResponseType.TEXT
        assert "RUNNING" in resp.text

    def test_positions_response(self):
        msg = TelegramMessage(
            chat_id="1", command=TelegramCommand.POSITIONS, timestamp=datetime.now(UTC)
        )
        resp = positions_handler(msg, {"positions": [_make_position()]})
        assert "BTCUSDT" in resp.text

    def test_portfolio_response(self):
        msg = TelegramMessage(
            chat_id="1", command=TelegramCommand.PORTFOLIO, timestamp=datetime.now(UTC)
        )
        snap = PortfolioSnapshot(
            snapshot_id=uuid4(),
            timestamp=datetime.now(UTC),
            status=PortfolioStatus.ACTIVE,
            total_positions=1,
            open_positions=1,
            closed_positions=0,
            long_positions=1,
            short_positions=0,
            net_exposure=0.1,
            gross_exposure=0.1,
            realized_pnl=0.0,
            unrealized_pnl=100.0,
            equity=10100.0,
            warnings=[],
        )
        resp = portfolio_handler(msg, {"portfolio_snapshot": snap})
        assert "10100.00" in resp.text

    def test_help_response(self):
        msg = TelegramMessage(
            chat_id="1", command=TelegramCommand.HELP, timestamp=datetime.now(UTC)
        )
        resp = help_handler(msg, {})
        assert "/status" in resp.text

    def test_empty_positions(self):
        msg = TelegramMessage(
            chat_id="1", command=TelegramCommand.POSITIONS, timestamp=datetime.now(UTC)
        )
        resp = positions_handler(msg, {"positions": []})
        assert "No open positions" in resp.text

    def test_missing_portfolio(self):
        msg = TelegramMessage(
            chat_id="1", command=TelegramCommand.PORTFOLIO, timestamp=datetime.now(UTC)
        )
        resp = portfolio_handler(msg, {})
        assert "No portfolio snapshot" in resp.text
