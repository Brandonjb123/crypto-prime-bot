"""Integration test — evaluator + real repo + mock price → DB EXPIRED/TIME."""

import sqlite3
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import (
    SignalLifecycleExpireReason,
    SignalLifecycleStatus,
)
from src.signal.actionability_evaluator import ActionabilityEvaluator
from src.storage.adapters.turso_signal_lifecycle_repository import (
    TursoSignalLifecycleRepository,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS signal_lifecycle (
    signal_id       TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('ACTIVE', 'EXPIRED')),
    expire_reason   TEXT CHECK (expire_reason IN ('TIME', 'SUPERSEDED')),
    created_at      TEXT NOT NULL,
    expires_at      TEXT NOT NULL,
    zone_low        REAL NOT NULL,
    zone_high       REAL NOT NULL,
    terminal_at     TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_lifecycle_active_per_symbol
    ON signal_lifecycle(symbol) WHERE status = 'ACTIVE';
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
        return _SqliteResult(columns, rows)

    def batch(self, stmts):
        results = []
        self._conn.execute("BEGIN")
        try:
            for stmt in stmts:
                if isinstance(stmt, tuple):
                    sql, params = stmt
                else:
                    sql, params = stmt, []
                cursor = self._conn.execute(sql, params or [])
                rows = cursor.fetchall()
                columns = (
                    [d[0] for d in cursor.description]
                    if cursor.description
                    else []
                )
                results.append(_SqliteResult(columns, rows))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return results


class _FakeProvider:
    def __init__(self, prices=None):
        self._prices = prices or {}

    def get_price(self, symbol):
        return self._prices.get(symbol)


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    yield TursoSignalLifecycleRepository(_SqliteWrapper(conn))
    conn.close()


def test_evaluator_marks_expired_in_db(repo):
    now = datetime.now(UTC)
    lc = SignalLifecycle(
        signal_id=uuid4(),
        symbol="BTC",
        status=SignalLifecycleStatus.ACTIVE,
        expire_reason=None,
        created_at=now - timedelta(hours=1),
        expires_at=now - timedelta(seconds=1),  # past
        zone_low=100.0,
        zone_high=110.0,
        terminal_at=None,
    )
    repo.create_with_supersede(lc)

    # Sebelum evaluasi: ACTIVE
    assert len(repo.get_all_active()) == 1

    evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))
    evaluator.evaluate_once()

    # Setelah evaluasi: tidak ada ACTIVE, row EXPIRED/TIME dengan terminal_at
    assert repo.get_all_active() == []
    result = repo.client.execute(
        "SELECT * FROM signal_lifecycle WHERE signal_id = ?",
        [str(lc.signal_id)],
    )
    row = dict(zip(result.columns, result.rows[0], strict=False))
    assert row["status"] == SignalLifecycleStatus.EXPIRED.value
    assert row["expire_reason"] == SignalLifecycleExpireReason.TIME.value
    assert row["terminal_at"] is not None