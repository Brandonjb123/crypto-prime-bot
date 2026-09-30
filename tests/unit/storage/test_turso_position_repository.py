"""Regression tests untuk TursoPositionRepository — pakai SQLite in-memory."""

import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.storage.adapters.turso_position_repository import TursoPositionRepository

SCHEMA = """
CREATE TABLE IF NOT EXISTS trading_positions (
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


def _make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


@pytest.fixture
def repo():
    conn = _make_conn()
    yield TursoPositionRepository(_SqliteWrapper(conn))
    conn.close()


def _make_position(status=PositionStatus.OPEN, realized_pnl=0.0, closed_at=None):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        signal_id=uuid4(),
        symbol="BTC",
        side=Side.LONG,
        status=status,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        tp1_price=51000.0,
        tp2_price=52000.0,
        position_size=0.01,
        opened_at=datetime.now(UTC),
        closed_at=closed_at,
        close_reason=PositionCloseReason.NONE if status == PositionStatus.OPEN else PositionCloseReason.MANUAL,
        last_price=50000.0,
        last_updated=datetime.now(UTC),
        realized_pnl=realized_pnl,
    )


class TestPositionRoundTrip:
    def test_save_and_get_open(self, repo):
        pos = _make_position()
        repo.save(pos)
        open_positions = repo.get_open()
        assert len(open_positions) == 1
        assert open_positions[0].position_id == pos.position_id
        assert open_positions[0].symbol == "BTC"
        assert open_positions[0].entry_price == 50000.0

    def test_get_closed_empty(self, repo):
        pos = _make_position()
        repo.save(pos)
        assert repo.get_closed() == []


class TestPositionUpsert:
    def test_open_then_closed_single_row(self, repo):
        pos = _make_position(status=PositionStatus.OPEN)
        repo.save(pos)

        closed_pos = Position(
            position_id=pos.position_id,
            execution_id=pos.execution_id,
            order_id=pos.order_id,
            signal_id=pos.signal_id,
            symbol=pos.symbol,
            side=pos.side,
            status=PositionStatus.CLOSED,
            entry_price=pos.entry_price,
            stop_loss=pos.stop_loss,
            take_profit=pos.take_profit,
            tp1_price=pos.tp1_price,
            tp2_price=pos.tp2_price,
            position_size=pos.position_size,
            opened_at=pos.opened_at,
            closed_at=datetime.now(UTC),
            close_reason=PositionCloseReason.STOP_LOSS,
            last_price=49000.0,
            last_updated=datetime.now(UTC),
            realized_pnl=-100.0,
        )
        repo.save(closed_pos)

        assert repo.count() == 1
        assert repo.get_open() == []
        closed = repo.get_closed()
        assert len(closed) == 1
        assert closed[0].status == PositionStatus.CLOSED
        assert closed[0].realized_pnl == -100.0


class TestRestartSimulation:
    def test_survives_repository_recreation(self):
        conn = _make_conn()
        wrapper = _SqliteWrapper(conn)

        repo_a = TursoPositionRepository(wrapper)
        open_pos = _make_position()
        closed_pos = _make_position(
            status=PositionStatus.CLOSED,
            realized_pnl=50.0,
            closed_at=datetime.now(UTC),
        )
        repo_a.save(open_pos)
        repo_a.save(closed_pos)

        repo_b = TursoPositionRepository(wrapper)
        assert len(repo_b.get_open()) == 1
        assert len(repo_b.get_closed()) == 1
        assert repo_b.get_open()[0].position_id == open_pos.position_id
        assert repo_b.get_closed()[0].position_id == closed_pos.position_id

        conn.close()