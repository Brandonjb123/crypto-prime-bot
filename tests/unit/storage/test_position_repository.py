"""Unit tests untuk PositionRepository."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.storage.adapters.in_memory_position_repository import InMemoryPositionRepository


def _make_pos(symbol="BTC/USDT", side=Side.LONG, status=PositionStatus.OPEN):
    return Position(
        position_id=uuid4(), execution_id=uuid4(), order_id=uuid4(),
        symbol=symbol, side=side, status=status,
        entry_price=50000.0, stop_loss=48000.0, take_profit=55000.0,
        position_size=0.1, opened_at=datetime.now(UTC),
        closed_at=None if status == PositionStatus.OPEN else datetime.now(UTC),
        close_reason=PositionCloseReason.NONE if status == PositionStatus.OPEN else PositionCloseReason.MANUAL,
    )


class TestPositionRepository:
    def repo(self):
        return InMemoryPositionRepository()

    def test_save_and_get(self):
        repo = self.repo()
        pos = _make_pos()
        repo.save(pos)
        found = repo.get_by_id(pos.position_id)
        assert found is not None
        assert found.position_id == pos.position_id

    def test_overwrite(self):
        repo = self.repo()
        pos1 = _make_pos()
        repo.save(pos1)
        pos2 = _make_pos()
        # Overwrite dengan ID yang sama
        pos_overwrite = Position(
            position_id=pos1.position_id, execution_id=pos2.execution_id,
            order_id=pos2.order_id, symbol=pos2.symbol, side=pos2.side,
            status=pos2.status, entry_price=pos2.entry_price,
            stop_loss=pos2.stop_loss, take_profit=pos2.take_profit,
            position_size=pos2.position_size, opened_at=pos2.opened_at,
            closed_at=pos2.closed_at, close_reason=pos2.close_reason,
        )
        repo.save(pos_overwrite)
        found = repo.get_by_id(pos1.position_id)
        assert found.entry_price == pos2.entry_price

    def test_delete(self):
        repo = self.repo()
        pos = _make_pos()
        repo.save(pos)
        repo.delete(pos.position_id)
        assert repo.get_by_id(pos.position_id) is None

    def test_get_open(self):
        repo = self.repo()
        repo.save(_make_pos("BTC/USDT", Side.LONG, PositionStatus.OPEN))
        repo.save(_make_pos("ETH/USDT", Side.SHORT, PositionStatus.CLOSED))
        assert len(repo.get_open()) == 1

    def test_get_closed(self):
        repo = self.repo()
        repo.save(_make_pos("BTC/USDT", Side.LONG, PositionStatus.CLOSED))
        repo.save(_make_pos("ETH/USDT", Side.SHORT, PositionStatus.OPEN))
        assert len(repo.get_closed()) == 1

    def test_count(self):
        repo = self.repo()
        repo.save(_make_pos())
        repo.save(_make_pos("ETH/USDT"))
        assert repo.count() == 2