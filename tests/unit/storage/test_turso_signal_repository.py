"""Regression tests untuk TursoSignalRepository — pakai SQLite in-memory."""

import sqlite3
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.core.models.trading_signal import TradingSignal
from src.storage.adapters.turso_signal_repository import TursoSignalRepository

SCHEMA = """
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id       TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,
    status          TEXT NOT NULL,
    entry_price     REAL,
    stop_loss       REAL,
    take_profit     REAL,
    take_profit_1   REAL,
    take_profit_2   REAL,
    position_size   REAL NOT NULL DEFAULT 0.0,
    risk_percent    REAL NOT NULL DEFAULT 0.0,
    confidence      INTEGER NOT NULL DEFAULT 0,
    risk_level      TEXT NOT NULL DEFAULT 'MEDIUM',
    reasoning       TEXT,
    created_at      TEXT NOT NULL
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


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    yield TursoSignalRepository(_SqliteWrapper(conn))
    conn.close()


def _make_signal(symbol="BTC", side="BUY", status="ACTIVE", offset_seconds=0):
    return TradingSignal(
        signal_id=uuid4(),
        symbol=symbol,
        side=side,
        status=status,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        take_profit_1=51000.0,
        take_profit_2=52000.0,
        position_size=0.01,
        risk_percent=1.0,
        confidence=80,
        risk_level="MEDIUM",
        reasoning=["test reasoning"],
        created_at=datetime.now(UTC) + timedelta(seconds=offset_seconds),
    )


class TestSignalAppendOnly:
    def test_append_multiple_same_symbol(self, repo):
        repo.append(_make_signal(offset_seconds=0))
        repo.append(_make_signal(offset_seconds=10))
        assert repo.count() == 2

    def test_latest_by_symbol_returns_newest(self, repo):
        s1 = _make_signal(offset_seconds=0)
        s2 = _make_signal(offset_seconds=10)
        repo.append(s1)
        repo.append(s2)
        latest = repo.latest_by_symbol("BTC")
        assert latest is not None
        assert latest.signal_id == s2.signal_id

    def test_history_returns_all(self, repo):
        repo.append(_make_signal(symbol="BTC"))
        repo.append(_make_signal(symbol="ETH"))
        repo.append(_make_signal(symbol="BTC"))
        assert len(repo.history()) == 3

    def test_history_filter_by_symbol(self, repo):
        repo.append(_make_signal(symbol="BTC"))
        repo.append(_make_signal(symbol="ETH"))
        btc_history = repo.history(symbol="BTC")
        assert len(btc_history) == 1
        assert btc_history[0].symbol == "BTC"


class TestWaitInvalidPersistence:
    def test_wait_signal_persisted(self, repo):
        repo.append(_make_signal(side="WAIT", status="SKIPPED"))
        assert repo.count() == 1
        assert repo.latest_by_symbol("BTC").status == "SKIPPED"

    def test_invalid_signal_persisted(self, repo):
        repo.append(_make_signal(status="INVALID"))
        assert repo.count() == 1
        assert repo.latest_by_symbol("BTC").status == "INVALID"


class TestReasoningSerialization:
    def test_reasoning_roundtrip(self, repo):
        sig = _make_signal().model_copy(update={"reasoning": ["r1", "r2", "r3"]})
        repo.append(sig)
        retrieved = repo.latest_by_symbol("BTC")
        assert retrieved.reasoning == ["r1", "r2", "r3"]

    def test_empty_reasoning(self, repo):
        sig = _make_signal().model_copy(update={"reasoning": []})
        repo.append(sig)
        retrieved = repo.latest_by_symbol("BTC")
        assert retrieved.reasoning == []