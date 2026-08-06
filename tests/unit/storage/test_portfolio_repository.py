"""Unit tests untuk PortfolioRepository."""

import time
from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.portfolio import PortfolioSnapshot
from src.core.types.enums import PortfolioStatus
from src.storage.adapters.in_memory_portfolio_repository import InMemoryPortfolioRepository


def _make_snapshot(status=PortfolioStatus.ACTIVE):
    return PortfolioSnapshot(
        snapshot_id=uuid4(),
        timestamp=datetime.now(UTC),
        status=status,
        total_positions=0, open_positions=0, closed_positions=0,
        long_positions=0, short_positions=0,
        net_exposure=0.0, gross_exposure=0.0,
        realized_pnl=0.0, unrealized_pnl=0.0,
        equity=10000.0, warnings=[],
    )


class TestPortfolioRepository:
    def repo(self):
        return InMemoryPortfolioRepository()

    def test_save_and_get(self):
        repo = self.repo()
        snap = _make_snapshot()
        repo.save(snap)
        assert repo.get_by_id(snap.snapshot_id) is not None

    def test_latest(self):
        repo = self.repo()
        snap1 = _make_snapshot()
        time.sleep(0.01)
        snap2 = _make_snapshot()
        repo.save(snap1)
        repo.save(snap2)
        assert repo.latest().snapshot_id == snap2.snapshot_id

    def test_history(self):
        repo = self.repo()
        repo.save(_make_snapshot())
        repo.save(_make_snapshot())
        assert len(repo.history()) == 2

    def test_count(self):
        repo = self.repo()
        repo.save(_make_snapshot())
        repo.save(_make_snapshot())
        assert repo.count() == 2