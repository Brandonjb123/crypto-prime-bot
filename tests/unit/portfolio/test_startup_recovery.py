"""Test startup recovery — persisted OPEN positions tersedia setelah repo reinstantiate."""

import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.portfolio.portfolio_state_manager import PortfolioStateManager
from src.storage.adapters.turso_position_repository import TursoPositionRepository

SCHEMA = """
CREATE TABLE IF NOT EXISTS positions (
    position_id     TEXT PRIMARY KEY,
    execution_id    TEXT NOT NULL,
    order_id        TEXT NOT NULL,
    signal_id       TEXT,
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,
    status          TEXT NOT NULL,
    entry_price     REAL NOT NULL,
    stop_loss       REAL NOT NULL,
    take_profit     REAL NOT NULL,
    tp1_price       REAL,
    tp2_price       REAL,
    position_size   REAL NOT NULL,
    opened_at       TEXT NOT NULL,
    closed_at       TEXT,
    close_reason    TEXT,
    last_price      REAL,
    last_updated    TEXT,
    realized_pnl    REAL NOT NULL DEFAULT 0.0
)
"""


class _SqliteResult:
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows


class _SqliteWrapper:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cursor = self._conn.execute(sql, params or [])
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description] if cursor.description else []
        self._conn.commit()
        return _SqliteResult(columns, rows)


def _make_open_position(symbol="BTC"):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        signal_id=uuid4(),
        symbol=symbol,
        side=Side.LONG,
        status=PositionStatus.OPEN,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        tp1_price=51000.0,
        tp2_price=52000.0,
        position_size=0.01,
        opened_at=datetime.now(UTC),
        closed_at=None,
        close_reason=PositionCloseReason.NONE,
        last_price=50000.0,
        last_updated=datetime.now(UTC),
        realized_pnl=0.0,
    )


class TestStartupRecovery:
    def test_open_positions_visible_after_repository_recreation(self):
        """
        Simulate: OPEN position persist ke Turso, aplikasi restart,
        PortfolioStateManager baru + TursoPositionRepository baru.
        Persisted OPEN harus langsung terlihat tanpa preload eksplisit.
        """
        # Setup: connection + schema (simulasi Turso)
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        wrapper = _SqliteWrapper(conn)

        # Fase 1: aplikasi lama — buka & simpan posisi
        repo_old = TursoPositionRepository(wrapper)
        psm_old = PortfolioStateManager(
            initial_balance=10000.0,
            position_repository=repo_old,
        )
        persisted_pos = _make_open_position(symbol="BTC")
        psm_old.repo.save(persisted_pos)
        assert len(psm_old.get_open_positions()) == 1

        # Fase 2: aplikasi restart — repo + PSM baru, tidak preload manual
        repo_new = TursoPositionRepository(wrapper)
        psm_new = PortfolioStateManager(
            initial_balance=10000.0,
            position_repository=repo_new,
        )

        # Assertion: OPEN langsung terlihat tanpa preload
        open_positions = psm_new.get_open_positions()
        assert len(open_positions) == 1
        assert open_positions[0].position_id == persisted_pos.position_id
        assert open_positions[0].symbol == "BTC"
        assert open_positions[0].status == PositionStatus.OPEN

        # Extra: get_state() juga lihat jumlah yang sama
        state = psm_new.get_state()
        assert state.open_positions == 1

        conn.close()

    def test_closed_positions_visible_after_repository_recreation(self):
        """Persisted CLOSED positions juga harus langsung terlihat."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        wrapper = _SqliteWrapper(conn)

        # Fase 1
        repo_old = TursoPositionRepository(wrapper)
        closed_pos = _make_open_position(symbol="ETH")
        closed_pos = closed_pos.model_copy(update={
            "status": PositionStatus.CLOSED,
            "closed_at": datetime.now(UTC),
            "close_reason": PositionCloseReason.MANUAL,
            "realized_pnl": 100.0,
        })
        repo_old.save(closed_pos)

        # Fase 2
        repo_new = TursoPositionRepository(wrapper)
        psm_new = PortfolioStateManager(
            initial_balance=10000.0,
            position_repository=repo_new,
        )

        # Assertion
        assert psm_new.realized_pnl == 100.0
        state = psm_new.get_state()
        assert state.closed_positions == 1
        assert state.realized_pnl == 100.0

        conn.close()